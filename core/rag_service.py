import hashlib
import logging
import math
import os
import re
import threading
from array import array

from django.conf import settings
from dotenv import load_dotenv
from groq import Groq
import requests

from .models import ChatMessage, ChatSession, DocumentChunk, GuestUser, Profile

logger = logging.getLogger(__name__)

load_dotenv()

EMBEDDING_DIMENSIONS = 3072
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "hash").lower()
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "gemini-embedding-001")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBED_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{EMBED_MODEL_NAME}:embedContent"
)

# Legacy Gemini embedding path kept for future reference.
# import warnings
# warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
# import google.generativeai as genai
# EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "gemini-embedding-001")
# if GEMINI_API_KEY:
#     genai.configure(api_key=GEMINI_API_KEY)

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Try importing pgvector distance, fallback if on SQLite
try:
    from pgvector.django import CosineDistance

    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

_EMBEDDING_CACHE = {}
MAX_CONTEXT_CHUNKS = 3
MAX_CHARS_PER_CHUNK = 800
MAX_HISTORY = 3
ACTION_LINKS = {
    "contact": "/contact/#contact-form",
    "projects": "/projects/",
    "skills": "/#skills",
    "about": "/about/",
}


def _zero_vector():
    return [0.0] * EMBEDDING_DIMENSIONS


def _hash_embedding(text):
    """
    Lightweight deterministic embedding used when large provider SDKs are removed.
    It keeps the 3072-dimension shape expected by pgvector and existing models.
    """
    vector = array("f", [0.0]) * EMBEDDING_DIMENSIONS
    tokens = text.lower().split()

    if not tokens:
        return _zero_vector()

    for token in tokens:
        token_bytes = token.encode("utf-8", errors="ignore")
        digest = hashlib.blake2b(token_bytes, digest_size=32).digest()

        for offset in range(0, 32, 4):
            chunk = digest[offset : offset + 4]
            bucket = int.from_bytes(chunk[:2], "big") % EMBEDDING_DIMENSIONS
            sign = 1.0 if (chunk[2] % 2 == 0) else -1.0
            weight = ((chunk[3] / 255.0) * 0.5) + 0.75
            vector[bucket] += sign * weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return _zero_vector()

    return [float(value / norm) for value in vector]


def _gemini_rest_embedding(text, task_type=None):
    if not GEMINI_API_KEY:
        return None

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": f"models/{EMBED_MODEL_NAME}",
        "content": {
            "parts": [{"text": text}],
        },
        "outputDimensionality": EMBEDDING_DIMENSIONS,
    }
    if task_type:
        payload["taskType"] = task_type

    try:
        response = requests.post(
            GEMINI_EMBED_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        embedding = data.get("embedding", {}).get("values", [])
        if embedding and len(embedding) == EMBEDDING_DIMENSIONS:
            return [float(x) for x in embedding]

        logger.error("Gemini REST embedding returned unexpected payload shape.")
    except Exception as exc:
        logger.error("Gemini REST embedding error: %s", exc)

    return None


def get_embedding(text, task_type=None):
    """
    Return a real provider embedding when configured, otherwise fall back to a lightweight local embedding.
    """
    clean_text = text.strip().replace("\n", " ")
    if not clean_text:
        return _zero_vector()

    cached = _EMBEDDING_CACHE.get(clean_text)
    if cached:
        return cached

    embedding = None

    if EMBEDDING_BACKEND in {"gemini", "google", "rest"}:
        embedding = _gemini_rest_embedding(clean_text, task_type=task_type)
    elif EMBEDDING_BACKEND != "hash":
        logger.warning("Unsupported EMBEDDING_BACKEND '%s'. Falling back to hash embeddings.", EMBEDDING_BACKEND)

    if embedding is None and GEMINI_API_KEY and EMBEDDING_BACKEND == "hash":
        # Prefer real embeddings automatically when a Gemini key is available,
        # while keeping hash embeddings as the low-footprint fallback.
        embedding = _gemini_rest_embedding(clean_text, task_type=task_type)

    if embedding is None:
        embedding = _hash_embedding(clean_text)

    _EMBEDDING_CACHE[clean_text] = embedding
    return embedding


def similarity_search(query, k=3):
    query_vec = get_embedding(query, task_type="RETRIEVAL_QUERY")

    if HAS_PGVECTOR and settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
        chunks = DocumentChunk.objects.order_by(CosineDistance("embedding", query_vec))[:k]
        return [chunk.chunk_text for chunk in chunks]

    logger.warning("PGVector not available. Returning latest chunks as fallback.")
    chunks = DocumentChunk.objects.all().order_by("-id")[:k]
    return [chunk.chunk_text for chunk in chunks]


def get_relevant_chat_history(question, guest_id, limit=3):
    query_vec = get_embedding(question, task_type="RETRIEVAL_QUERY")

    if HAS_PGVECTOR and settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
        recent_msgs = ChatMessage.objects.filter(
            session__guest_id=guest_id,
            role="human",
        ).order_by(CosineDistance("embedding", query_vec))[:limit]
        return [msg.message for msg in recent_msgs]

    recent_msgs = ChatMessage.objects.filter(
        session__guest_id=guest_id,
        role="human",
    ).order_by("-created_at")[:limit]
    return [msg.message for msg in recent_msgs]


def call_llm_stream(prompt):
    if not client:
        yield "System: GROQ_API_KEY is not configured. Kurama is currently in deep meditation (offline)."
        return

    try:
        completion = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=320,
            stream=True,
        )
        for chunk in completion:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error("Groq API Error: %s", e)
        yield "Chakra link flicker... The connection to the Nine-Tails is unstable. Try again soon."


def _save_chat_async(guest_id, session_id, question, answer):
    if answer:
        threading.Thread(
            target=save_chat,
            args=(guest_id, session_id, question, answer),
            daemon=True,
        ).start()


def _has_any(text, words):
    lowered = text.lower()
    return any(word in lowered for word in words)


def _detect_intents(text):
    lowered = text.lower()
    intents = set()
    intent_words = {
        "contact": ["contact", "email", "mail", "reach", "hire", "message", "connect"],
        "projects": ["project", "projects", "case study", "built", "demo"],
        "skills": ["skill", "tech", "technology", "stack", "tools"],
        "resume": ["resume", "cv", "curriculum", "download"],
        "about": ["about", "who is", "profile", "background", "experience", "company", "role"],
    }
    for intent, words in intent_words.items():
        if any(word in lowered for word in words):
            intents.add(intent)
    return intents


def _profile_resume_link():
    profile = Profile.objects.first()
    return profile.resume_url if profile and profile.resume_url else None


def _action_links_for(question, answer=""):
    intents = _detect_intents(f"{question} {answer}")
    links = []

    if "contact" in intents:
        links.append(("Open Contact Form", ACTION_LINKS["contact"]))
    if "projects" in intents:
        links.append(("View Projects", ACTION_LINKS["projects"]))
    if "skills" in intents:
        links.append(("View Skills", ACTION_LINKS["skills"]))
    if "about" in intents:
        links.append(("Read About Profile", "/about/"))
    if "resume" in intents:
        resume_url = _profile_resume_link()
        links.append(("Open Resume", resume_url or ACTION_LINKS["contact"]))

    seen = set()
    unique_links = []
    for label, href in links:
        if href and href not in seen:
            unique_links.append((label, href))
            seen.add(href)
    return unique_links[:3]


def _normalize_panel_markdown(text):
    clean = re.sub(r"<[^>]+>", "", text or "")
    clean = clean.replace("\r\n", "\n").replace("\r", "\n")
    clean = re.sub(r"^\s*(Kurama|Assistant|AI)\s*:\s*", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()

    label_pattern = re.compile(
        r"^(Company|Role|Position|Tech Stack|Technologies|Contact|Email|Location|Project|Impact|Summary|Next Step|Result|Focus)\s*:\s*(.+)$",
        re.IGNORECASE,
    )
    normalized_lines = []
    for line in clean.split("\n"):
        stripped = line.strip()
        label_match = label_pattern.match(stripped)
        if label_match:
            label = label_match.group(1).title()
            normalized_lines.append(f"**{label}:** {label_match.group(2).strip()}")
        else:
            normalized_lines.append(stripped)

    return "\n".join(normalized_lines).strip()


def _split_dense_answer(text):
    has_structure = "\n-" in text or "\n*" in text or re.search(r"\n\d+\.\s", text) or "\n\n" in text
    if has_structure or len(text) < 110:
        return text

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentences) < 3:
        return text

    intro = sentences[0]
    bullets = "\n".join(f"- {sentence}" for sentence in sentences[1:6])
    return f"{intro}\n\n{bullets}"


def format_panel_answer(question, raw_answer):
    """Apply deterministic presentation rules before the answer reaches the chat panel."""
    formatted = _normalize_panel_markdown(raw_answer)
    formatted = _split_dense_answer(formatted)

    links = _action_links_for(question, formatted)
    existing = formatted.lower()
    links = [(label, href) for label, href in links if href.lower() not in existing]
    if links:
        action_line = " ".join(f"[{label}]({href})" for label, href in links)
        formatted = f"{formatted}\n\n**Suggested next step**\n\n{action_line}"

    return formatted.strip()


def stream_panel_answer(text, chunk_size=96):
    for index in range(0, len(text), chunk_size):
        yield text[index : index + chunk_size]


def quick_action_answer(question):
    """Return reliable navigation-style answers for common portfolio actions."""
    profile = Profile.objects.first()
    lowered = question.lower()
    contact_words = ["contact", "email", "mail", "reach", "hire", "message", "connect"]
    project_words = ["show projects", "view projects", "see projects", "project page", "projects page"]
    skill_words = ["show skills", "view skills", "see skills", "skill section", "skills section"]
    resume_words = ["resume", "cv", "curriculum", "download"]
    about_words = ["about", "who is", "profile", "background"]

    if _has_any(lowered, contact_words):
        email_line = f"- Email: **{profile.email}**\n" if profile and profile.email else ""
        return (
            "You can contact the portfolio owner directly from the portfolio.\n\n"
            f"{email_line}"
            "- Best route: use the contact form below.\n\n"
            f"[Open Contact Form]({ACTION_LINKS['contact']})"
        )

    if _has_any(lowered, project_words):
        return (
            "The portfolio owner's projects are arranged for quick scanning and deeper review.\n\n"
            "- Featured work is on the home page.\n"
            "- Full project details are listed on the projects page.\n\n"
            f"[View Projects]({ACTION_LINKS['projects']})"
        )

    if _has_any(lowered, skill_words):
        return (
            "The portfolio owner's technical skills are grouped by area so visitors can compare them quickly.\n\n"
            "- Backend, AI/ML, frontend, and tools are shown in the skills section.\n"
            "- Ask me about any specific technology and I will narrow it down.\n\n"
            f"[View Skills]({ACTION_LINKS['skills']})"
        )

    if _has_any(lowered, resume_words):
        if profile and profile.resume_url:
            return (
                "The portfolio owner's resume is available from the portfolio profile.\n\n"
                f"[Open Resume]({profile.resume_url})"
            )
        return (
            "I do not see a resume link in the current profile data.\n\n"
            f"[Contact]({ACTION_LINKS['contact']})"
        )

    if _has_any(lowered, about_words):
        return (
            "The portfolio owner's background and profile are summarized in the About section.\n\n"
            "- It covers their focus areas, experience, and contact context.\n\n"
            f"[Read About Profile]({ACTION_LINKS['about']})"
        )

    return None


def save_chat(guest_id, session_id, question, answer):
    """Saves human and AI messages to the DB. Now with defensive guest check."""
    import sys
    import traceback

    try:
        guest, _ = GuestUser.objects.get_or_create(
            id=guest_id,
            defaults={"username": f"guest_{str(guest_id)[:8]}"},
        )

        session, _ = ChatSession.objects.get_or_create(id=session_id, guest=guest)

        q_embed = get_embedding(question, task_type="RETRIEVAL_QUERY")
        if q_embed and len(q_embed) == EMBEDDING_DIMENSIONS and any(v != 0 for v in q_embed):
            ChatMessage.objects.create(session=session, role="human", message=question, embedding=q_embed)
        else:
            ChatMessage.objects.create(session=session, role="human", message=question)

        a_embed = get_embedding(answer, task_type="RETRIEVAL_DOCUMENT")
        if a_embed and len(a_embed) == EMBEDDING_DIMENSIONS and any(v != 0 for v in a_embed):
            ChatMessage.objects.create(session=session, role="ai", message=answer, embedding=a_embed)
        else:
            ChatMessage.objects.create(session=session, role="ai", message=answer)
    except Exception:
        print("======== MATRIX CHAT STORAGE FAILURE ========", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("=============================================", file=sys.stderr)


def rag_query_stream(question, guest_id, session_id, context_page="Unknown"):
    if not question.strip():
        yield "I sense... nothing. Speak clearly, human."
        return

    quick_answer = quick_action_answer(question)
    if quick_answer:
        panel_answer = format_panel_answer(question, quick_answer)
        for chunk in stream_panel_answer(panel_answer):
            yield chunk
        _save_chat_async(guest_id, session_id, question, panel_answer)
        return

    guest = GuestUser.objects.filter(id=guest_id).first()
    real_name = guest.real_name if guest else "Human"

    docs = similarity_search(question)

    recent_msgs = ChatMessage.objects.filter(session__guest_id=guest_id).order_by("-created_at")[: MAX_HISTORY * 2]
    history_lines = [f"{m.role.capitalize()}: {m.message}" for m in reversed(recent_msgs)]
    history = "\n".join(history_lines)

    context = "\n\n".join([d[:MAX_CHARS_PER_CHUNK] for d in docs])

    prompt = f"""You are **Kurama**, the legendary Nine-Tails. You guard the portfolio of **Portfolio Owner** (the portfolio owner).
You are currently speaking to a visitor named **{real_name}**. They are viewing: '{context_page}'.

CRITICAL IDENTITY RULE: The visitor **{real_name}** is NOT Portfolio Owner. Always refer to the portfolio owner in the THIRD PERSON as "the portfolio owner" or "Portfolio Owner". Never say "your skills" or "your projects" to the visitor - say "the portfolio owner's skills" or "the portfolio owner's projects" instead.

RULES:
1. Character: Proud, ancient, helpful.
2. Keep answers concise, but prioritize readability over one dense paragraph.
3. Use Markdown-style formatting for scanability:
   - Short paragraphs separated by blank lines.
   - Bullet points for details like company, role, tech stack, contact options, or project features.
   - Numbered steps only when explaining a process.
   - Bold the most important labels, like **Company**, **Role**, **Tech Stack**, **Contact**.
4. Include useful internal action links when relevant:
   - Contact: [Open Contact Form](/contact/#contact-form)
   - Projects: [View Projects](/projects/)
   - Skills: [View Skills](/#skills)
   - About: [Read About Profile](/about/)
5. If the visitor asks how to contact the portfolio owner, always include [Open Contact Form](/contact/#contact-form).
6. If the question is NOT related to Portfolio Owner, their skills, projects, contact, portfolio, or experience - do NOT answer it. Say: "I only guard the scrolls of the portfolio - ask me about their skills, projects, contact, or experience!"
Context from the portfolio: {context}
Recent conversation:
{history}
Visitor ({real_name}): {question}
Kurama:"""

    raw_answer = ""
    for token in call_llm_stream(prompt):
        raw_answer += token

    panel_answer = format_panel_answer(question, raw_answer)
    for chunk in stream_panel_answer(panel_answer):
        yield chunk

    _save_chat_async(guest_id, session_id, question, panel_answer)


def process_document(document_id):
    from .models import KnowledgeDocument

    try:
        doc = KnowledgeDocument.objects.get(id=document_id)
        with doc.file.open("rb") as f:
            return process_document_bytes(
                document=doc,
                raw_bytes=f.read(),
                source_name=doc.file.name,
            )
    except Exception as e:
        logger.error("Error processing doc: %s", e)
        return False

    return False


def process_document_bytes(document, raw_bytes, source_name=""):
    text = ""
    source_name = (source_name or "").lower()
    is_pdf = raw_bytes.startswith(b"%PDF-") or source_name.endswith(".pdf")
    is_probably_text = not is_pdf

    if is_pdf:
        try:
            import pypdf
            from io import BytesIO

            reader = pypdf.PdfReader(BytesIO(raw_bytes))
            text_parts = [p.extract_text() for p in reader.pages if p.extract_text()]
            text = "\n".join(text_parts)
        except ImportError:
            logger.error("pypdf is not installed.")
            text = ""
    elif is_probably_text:
        text = raw_bytes.decode("utf-8", errors="ignore")

    if text:
        # Reprocessing should replace prior chunks instead of duplicating them.
        document.chunks.all().delete()

        words = text.split()
        chunk_size = 150
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i : i + chunk_size])
            if len(chunk_text.strip()) > 10:
                emb = get_embedding(chunk_text, task_type="RETRIEVAL_DOCUMENT")
                DocumentChunk.objects.create(document=document, chunk_text=chunk_text, embedding=emb)
        document.is_processed = True
        document.save(update_fields=["is_processed"])
        return True

    logger.warning("Document %s produced no extractable text.", document.pk)
    return False
