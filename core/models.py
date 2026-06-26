from django.db import models
from django.contrib.auth.models import User
import uuid
import os

try:
    from pgvector.django import VectorField
except ImportError:
    # Industry-grade fallback for local SQLite dev if pgvector is not installed
    VectorField = models.JSONField

RawMediaCloudinaryStorage = None
if os.getenv('CLOUDINARY_URL'):
    try:
        from cloudinary_storage.storage import RawMediaCloudinaryStorage
    except ImportError:
        RawMediaCloudinaryStorage = None

class Profile(models.Model):
    """Single profile record for the portfolio owner."""
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200, help_text="Short headline, e.g. 'Full Stack Developer'")
    bio = models.TextField()
    avatar = models.ImageField(upload_to='profile/', blank=True, null=True)
    resume_url = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    years_experience = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profile"


class ProjectCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Project Categories"


class Project(models.Model):
    title = models.CharField(max_length=150)
    short_description = models.CharField(max_length=300)
    full_description = models.TextField(blank=True)
    image = models.ImageField(upload_to='projects/', blank=True, null=True, help_text="Main thumbnail image")
    slug = models.SlugField(unique=True, blank=True, null=True)
    live_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    tech_stack = models.CharField(max_length=500, blank=True, help_text="Comma-separated: Python, Django, React")
    category = models.ForeignKey(ProjectCategory, on_delete=models.SET_NULL, null=True, blank=True)
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, help_text="Lower = shown first")
    created_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_tech_list(self):
        return [t.strip() for t in self.tech_stack.split(',') if t.strip()]

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', '-created_at']

class ProjectScreenshot(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Screenshot for {self.project.title}"

    class Meta:
        ordering = ['order']

class Skill(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=50,
        choices=[
            ('Frontend', 'Frontend'),
            ('Backend', 'Backend'),
            ('Tools', 'Tools/DevOps'),
            ('Other', 'Other')
        ]
    )
    icon_class = models.CharField(max_length=100, blank=True, help_text="e.g. devicon class or emoji")
    image = models.ImageField(upload_to='skills/', blank=True, null=True, help_text="Upload custom technology logo")
    url = models.URLField(blank=True, null=True, help_text="Official website or documentation link")

    def __str__(self):
        return f"{self.name} ({self.category})"

    class Meta:
        ordering = ['name']


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        ordering = ['-created_at']


# --- RAG CHATBOT MODELS & ADVANCED GUEST TRACKING ---

class GuestUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100, help_text="Codename (ID) the guest chose.")
    real_name = models.CharField(max_length=100, blank=True, null=True, help_text="The person's actual name.")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


class KnowledgeDocument(models.Model):
    knowledge_doc_storage = (
        RawMediaCloudinaryStorage()
        if RawMediaCloudinaryStorage is not None and os.getenv('CLOUDINARY_URL')
        else None
    )
    title = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='knowledge_docs/',
        storage=knowledge_doc_storage,
        help_text="Upload .txt or .pdf files",
    )
    # Legacy local-disk storage kept for future reference from pre-Vercel builds:
    # from django.core.files.storage import FileSystemStorage
    # from django.conf import settings
    # local_storage = FileSystemStorage(location=settings.MEDIA_ROOT)
    # file = models.FileField(upload_to='knowledge_docs/', storage=local_storage, help_text="Upload .txt or .pdf files")
    # Previous generic Cloudinary media storage also caused docs to be treated as image resources.
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False, help_text="True if chunks and embeddings are generated")

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name='chunks')
    chunk_text = models.TextField()
    embedding = VectorField(dimensions=3072, help_text="Gemini native 3072-dimensional embedding")

    def __str__(self):
        return f"Chunk {self.id} of {self.document.title}"


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guest = models.ForeignKey(GuestUser, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True, help_text="The guest who generated this chat.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.id} for {self.guest.username}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [('human', 'Human'), ('ai', 'AI')]
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    message = models.TextField()
    embedding = VectorField(dimensions=3072, null=True, blank=True, help_text="Gemini native 3072-dimensional embedding for human queries")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        session_id = self.session.id if self.session else "No Session"
        return f"{self.role} msg in {session_id}"

    class Meta:
        ordering = ['created_at']

