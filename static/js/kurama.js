/* =======================================================
   KURAMA.JS - Interactive Fox Pet & Chat Assistant Overlay
   ======================================================= */

/* -- DOM REFERENCES ----------------------------------- */
const chatBox       = document.getElementById('chat-box');
const chatForm      = document.getElementById('chat-form');
const chatWrapper   = document.getElementById('chat-wrapper');
const chatInput     = document.getElementById('chat-input');
const assistantPanel = document.getElementById('assistant-panel');
const kuramaWidget  = document.getElementById('kurama-widget');
const kuramaSpeech  = document.getElementById('kurama-widget-speech');
const tbbOverlay    = document.getElementById('kurama-widget-tbb');
const chatSendButton = document.getElementById('chat-send');

/* -- STATE -------------------------------------------- */
const assistantState = {
    isOpen: false,
    isInitialized: false,
    currentPage: window.location.pathname,
    isBusy: false
};

const CHAT_HISTORY_KEY = 'kurama_chat_history_v1';
const MAX_STORED_MESSAGES = 40;

let currentSessionId = localStorage.getItem('kurama_session_id');
let currentUserId    = localStorage.getItem('kurama_user_id_v2');
let currentRealName  = localStorage.getItem('kurama_realname');
let hasGreeted       = false;
let petMood          = 'idle';
let responseStatusTimer;
let activeAssistantController = null;

/* -- DRAGGABLE WIDGET LOGIC --------------------------- */
/* -- DRAGGABLE WIDGET LOGIC --------------------------- */
const widget = document.getElementById("kurama-widget");
let isDraggingKurama = false;
let offsetX = 0; let offsetY = 0;

widget.addEventListener("mousedown", dragStart);
widget.addEventListener("touchstart", dragStart, { passive: false });

function dragStart(e) {
    isDraggingKurama = false;
    const rect = widget.getBoundingClientRect();
    const isTouch = e.type === "touchstart";
    const clientX = isTouch ? e.touches[0].clientX : e.clientX;
    const clientY = isTouch ? e.touches[0].clientY : e.clientY;

    offsetX = clientX - rect.left;
    offsetY = clientY - rect.top;

    widget.style.bottom = "auto";
    widget.style.right = "auto";
    widget.style.left = rect.left + "px";
    widget.style.top = rect.top + "px";

    function onMove(moveEvent) {
        isDraggingKurama = true;
        const mX = isTouch ? moveEvent.touches[0].clientX : moveEvent.clientX;
        const mY = isTouch ? moveEvent.touches[0].clientY : moveEvent.clientY;
        widget.style.left = (mX - offsetX) + "px";
        widget.style.top = (mY - offsetY) + "px";
    }

    function onEnd() {
        document.removeEventListener(isTouch ? "touchmove" : "mousemove", onMove);
        document.removeEventListener(isTouch ? "touchend" : "mouseup", onEnd);
        setTimeout(() => isDraggingKurama = false, 50);
    }

    document.addEventListener(isTouch ? "touchmove" : "mousemove", onMove, { passive: false });
    document.addEventListener(isTouch ? "touchend" : "mouseup", onEnd);
}

widget.addEventListener("click", (e) => {
    if (isDraggingKurama) {
        e.preventDefault();
        e.stopPropagation();
        return;
    }
    toggleAssistantMode();
});

/* -- SPEECH BUBBLE ------------------------------------ */
function showSpeechBubble(text, ms = 2000) {
    if (!kuramaSpeech) return;
    kuramaSpeech.textContent = text;
    kuramaSpeech.classList.add('visible');
    setTimeout(() => kuramaSpeech.classList.remove('visible'), ms);
}

/* -- PET STATE MANAGEMENT ----------------------------- */
function setPetState(state) {
    if (!kuramaWidget) return;
    
    // Clear all state classes
    ['state-happy','state-angry','state-sleep','state-attacking'].forEach(c => {
        kuramaWidget.classList.remove(c);
    });

    switch (state) {
        case 'thinking':
            const thoughts = ['', 'cloud', 'focus', 'Loading chakra...', 'Reading scrolls...', 'I sense it...', 'Just a moment...'];
            showSpeechBubble(thoughts[Math.floor(Math.random() * thoughts.length)], 8000);
            break;
        case 'speaking':
            showSpeechBubble('', 6000);
            break;
        case 'attacking':
            kuramaWidget.classList.add('state-angry');
            showSpeechBubble('', 3000);
            break;
        case 'tbb':
            kuramaWidget.classList.add('state-angry');
            // TBB overlay handled below if needed
            break;
        case 'angry':
            kuramaWidget.classList.add('state-angry');
            break;
        case 'happy':
            kuramaWidget.classList.add('state-happy');
            showSpeechBubble('', 2000);
            break;
        case 'sleep':
            kuramaWidget.classList.add('state-sleep');
            break;
        case 'idle':
        default:
            kuramaSpeech?.classList.remove('visible');
            break;
    }
    petMood = state;
}

/* Idle Timeout -> Sleep */
let idleTimer;
function resetIdleTimer() {
    clearTimeout(idleTimer);
    if (petMood === 'sleep') setPetState('idle');
    idleTimer = setTimeout(() => {
        if (!assistantState.isOpen && petMood === 'idle') {
            setPetState('sleep');
        }
    }, 15000); // 15 seconds of no interaction -> sleep
}
window.addEventListener('mousemove', resetIdleTimer);
window.addEventListener('keydown', resetIdleTimer);
resetIdleTimer();


/* -- INTELLIGENT TYPING WATCH ------------------------- */
let typingWatchTimer;
if (chatInput) {
    chatInput.addEventListener('input', () => {
        clearTimeout(typingWatchTimer);
        const len = chatInput.value.length;
        if (len > 0 && len % 40 === 0) {
            if (len >= 120) {
                setPetState('tbb');
            } else if (len >= 60) {
                setPetState('attacking');
                showSpeechBubble('* Chakra rising!', 2000);
            }
        }
        typingWatchTimer = setTimeout(() => {
            if (petMood === 'attacking' || petMood === 'tbb' || petMood === 'angry') setPetState('idle');
        }, 5000);
    });
}

/* -- RESIZER ----------------------------------- */
const assistantResizer = document.getElementById('assistant-resizer');
let isResizing = false;

function applyPanelWidth(px) {
    const min = 280, max = Math.min(680, window.innerWidth * 0.65);
    const clamped = Math.max(min, Math.min(max, px));
    document.documentElement.style.setProperty('--panel-width', clamped + 'px');
    if (assistantPanel) assistantPanel.style.width = clamped + 'px';
}

if (assistantResizer && assistantPanel) {
    assistantResizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        if (assistantPanel) assistantPanel.style.transition = 'none';
        e.preventDefault();
    });
    // Touch support
    assistantResizer.addEventListener('touchstart', (e) => {
        isResizing = true;
        if (assistantPanel) assistantPanel.style.transition = 'none';
        e.preventDefault();
    }, { passive: false });
}

window.addEventListener('mousemove', (e) => {
    if (!isResizing) return;
    applyPanelWidth(window.innerWidth - e.clientX);
});
window.addEventListener('touchmove', (e) => {
    if (!isResizing || !e.touches[0]) return;
    applyPanelWidth(window.innerWidth - e.touches[0].clientX);
}, { passive: true });
window.addEventListener('mouseup', () => {
    if (!isResizing) return;
    isResizing = false;
    document.body.style.cursor = '';
    assistantPanel.style.transition = '';
    const nav = document.getElementById('main-nav');
    if (nav) nav.style.transition = '';
});

/* -- PANEL TOGGLE ------------------------------------- */
function toggleAssistantMode() {
    if (!window.appReadyForAssistant) return;
    assistantState.isOpen = !assistantState.isOpen;
    const nav = document.getElementById('main-nav');
    
    if (assistantState.isOpen) {
        document.body.classList.add('assistant-active');
        const w = assistantPanel.style.width || '420px';
        assistantPanel.style.width = w;
        if (nav) nav.style.width = `calc(100% - ${w})`;
        setPetState('happy');
        setTimeout(() => setPetState('idle'), 2000);
        
        // Push state for mobile back-button support
        if (window.innerWidth <= 768) {
            history.pushState({ assistantOpen: true }, '');
        }
        
        if (!assistantState.isInitialized) initAssistant();
    } else {
        document.body.classList.remove('assistant-active');
        assistantPanel.style.width = '';
        if (nav) nav.style.width = '';
        setPetState('idle');
    }
}

// Mobile Back Button Support
window.addEventListener('popstate', (e) => {
    if (assistantState.isOpen) {
        // Prevent default navigation if panel is open, just close it
        toggleAssistantMode();
    }
});

/* -- ASSISTANT INIT ----------------------------------- */
function initAssistant() {
    assistantState.isInitialized = true;
    if (!currentSessionId) {
        showWelcomeScreen();
    } else {
        const hasHistory = renderStoredMessages();
        setChatInputEnabled(true);
        if (!hasHistory && !hasGreeted) {
            const name = currentRealName || localStorage.getItem('kurama_username') || 'Human';
            appendAiMsg(`Hmph. ${name}. I sense your chakra once more. I am the Nine-Tails - Kurama. Speak your query.`);
            hasGreeted = true;
        }
        if (chatWrapper) chatWrapper.classList.remove('hidden');
        if (chatInput)   chatInput.focus();
    }
}

/* -- MODALS ------------------------------------------- */
function showRegModal() {
    document.getElementById('registration-modal')?.classList.remove('opacity-0','invisible','pointer-events-none');
}
function hideRegModal() {
    document.getElementById('registration-modal')?.classList.add('opacity-0','invisible','pointer-events-none');
}

async function submitRegistration() {
    const username = document.getElementById('reg-codename')?.value.trim();
    const realName = document.getElementById('reg-realname')?.value.trim();
    const err      = document.getElementById('reg-error');
    if (!username || !realName) { err?.classList.remove('hidden'); return; }
    err?.classList.add('hidden');
    try {
        const fd = new URLSearchParams();
        fd.append('username', username); fd.append('real_name', realName);
        const res  = await fetch('/api/init-assistant/', {method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:fd});
        const data = await res.json();
        if (data.session_id) {
            currentSessionId = data.session_id; currentUserId = data.user_id; currentRealName = data.real_name;
            localStorage.setItem('kurama_session_id', currentSessionId);
            localStorage.setItem('kurama_user_id_v2', currentUserId);
            localStorage.setItem('kurama_username',   data.username);
            localStorage.setItem('kurama_realname',   data.real_name);
            setChatInputEnabled(true);
            hideRegModal();
            if (assistantState.isOpen && chatBox) {
                chatBox.innerHTML = '';
                hasGreeted = false;
                initAssistant();
            }
        } else {
            if (err) { err.innerText = data.message || 'Registration error.'; err.classList.remove('hidden'); }
        }
    } catch { if (err) { err.innerText = 'Connection failed.'; err.classList.remove('hidden'); } }
}

/* -- IN-PANEL WELCOME --------------------------------- */
function showWelcomeScreen() {
    if (!chatBox) return;
    localStorage.removeItem(CHAT_HISTORY_KEY);
    setChatInputEnabled(false, 'Enter details to unlock chat');
    chatBox.innerHTML = `
    <div class="msg-bubble msg-ai mb-2">I am <strong>Kurama</strong>, the Nine-Tails. Enter your details to proceed, human.</div>
    <div id="auth-box" class="flex flex-col gap-3 p-3 bg-white/5 rounded border border-white/10">
        <div class="flex flex-col gap-1">
            <label class="text-[10px] uppercase text-portfolio-orange font-bold tracking-wider">Codename</label>
            <input type="text" id="guest-codename" class="bg-black/60 border border-white/10 text-white text-sm px-3 py-2 focus:border-portfolio-orange outline-none" placeholder="e.g. ShadowFox" autofocus onkeydown="if(event.key==='Enter') document.getElementById('guest-realname').focus()">
        </div>
        <div class="flex flex-col gap-1">
            <label class="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Your Name</label>
            <input type="text" id="guest-realname" class="bg-black/60 border border-white/10 text-white text-sm px-3 py-2 focus:border-portfolio-orange outline-none" placeholder="e.g. John Doe" onkeydown="if(event.key==='Enter') startSession()">
        </div>
        <button onclick="startSession()" class="btn-portfolio-primary text-sm py-2 justify-center mt-1">
            Enter Domain <i class="fas fa-chevron-right ml-2"></i>
        </button>
    </div>`;
    if (chatWrapper) chatWrapper.classList.remove('hidden');
}

async function startSession() {
    const username = document.getElementById('guest-codename')?.value.trim();
    const realName = document.getElementById('guest-realname')?.value.trim();
    if (!username || !realName) { alert('Both fields are required.'); return; }
    const authBox = document.getElementById('auth-box');
    const orig    = authBox.innerHTML;
    authBox.innerHTML = '<div class="flex justify-center p-4"><i class="fas fa-circle-notch fa-spin text-portfolio-orange text-2xl"></i></div>';
    try {
        const fd = new URLSearchParams();
        fd.append('username', username); fd.append('real_name', realName);
        const res  = await fetch('/api/init-assistant/', {method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:fd});
        const data = await res.json();
        if (data.session_id) {
            currentSessionId = data.session_id; currentUserId = data.user_id; currentRealName = data.real_name;
            localStorage.setItem('kurama_session_id', currentSessionId);
            localStorage.setItem('kurama_user_id_v2', currentUserId);
            localStorage.setItem('kurama_username',   data.username);
            localStorage.setItem('kurama_realname',   data.real_name);
            authBox.remove();
            setChatInputEnabled(true);
            appendAiMsg(`Hmph. **${data.real_name || data.username}**. Etched in the scrolls of the Nine-Tails. What is your query?`);
            setPetState('happy');
            setTimeout(() => setPetState('idle'), 3000);
            if (chatInput) chatInput.focus();
        } else throw new Error();
    } catch {
        authBox.innerHTML = orig + '<p class="text-red-400 text-xs mt-2 text-center">Failed - try a different codename.</p>';
    }
}

/* -- CHAT HELPERS ------------------------------------- */
function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function sanitizeHref(href) {
    const value = String(href || '').trim();
    if (
        value.startsWith('/') ||
        value.startsWith('#') ||
        value.startsWith('mailto:') ||
        value.startsWith('https://') ||
        value.startsWith('http://')
    ) {
        return value;
    }
    return '#';
}

function renderInlineMarkdown(text) {
    const parts = [];
    const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
    let lastIndex = 0;
    let match;

    function renderTextChunk(chunk) {
        return escapeHtml(chunk).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    }

    while ((match = linkPattern.exec(text)) !== null) {
        parts.push(renderTextChunk(text.slice(lastIndex, match.index)));
        const label = escapeHtml(match[1]);
        const href = escapeHtml(sanitizeHref(match[2]));
        parts.push(`<a href="${href}" class="chat-action-link">${label}</a>`);
        lastIndex = linkPattern.lastIndex;
    }

    parts.push(renderTextChunk(text.slice(lastIndex)));
    return parts.join('');
}

function renderAssistantMessage(text) {
    const lines = String(text || '').replace(/\r\n/g, '\n').split('\n');
    const blocks = [];
    let listType = null;
    let listItems = [];

    function flushList() {
        if (!listType || listItems.length === 0) return;
        blocks.push(`<${listType}>${listItems.map((item) => `<li>${item}</li>`).join('')}</${listType}>`);
        listType = null;
        listItems = [];
    }

    lines.forEach((rawLine) => {
        const line = rawLine.trim();
        if (!line) {
            flushList();
            return;
        }

        const bullet = line.match(/^[-*]\s+(.+)/);
        const numbered = line.match(/^\d+\.\s+(.+)/);

        if (bullet || numbered) {
            const nextType = bullet ? 'ul' : 'ol';
            if (listType && listType !== nextType) flushList();
            listType = nextType;
            listItems.push(renderInlineMarkdown((bullet || numbered)[1]));
            return;
        }

        flushList();
        blocks.push(`<p>${renderInlineMarkdown(line)}</p>`);
    });

    flushList();
    return blocks.join('');
}

function getStoredMessages() {
    try {
        const messages = JSON.parse(localStorage.getItem(CHAT_HISTORY_KEY) || '[]');
        return Array.isArray(messages) ? messages.filter(item => item && item.role && item.text) : [];
    } catch {
        return [];
    }
}

function saveStoredMessages(messages) {
    try {
        localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messages.slice(-MAX_STORED_MESSAGES)));
    } catch {
        // Storage can fail in private browsing; the live chat still works.
    }
}

function rememberMessage(role, text) {
    if (!text) return;
    const messages = getStoredMessages();
    messages.push({ role, text: String(text), ts: Date.now() });
    saveStoredMessages(messages);
}

function renderStoredMessages() {
    if (!chatBox) return false;
    const messages = getStoredMessages();
    if (!messages.length) return false;

    chatBox.innerHTML = '';
    messages.forEach((message) => {
        if (message.role === 'human') appendHumanMsg(message.text, false);
        if (message.role === 'ai') appendAiMsg(message.text, false);
    });
    return true;
}

function clearStoredMessages() {
    localStorage.removeItem(CHAT_HISTORY_KEY);
    if (chatBox) chatBox.innerHTML = '';
    hasGreeted = false;
    assistantState.isInitialized = false;
    initAssistant();
}

function hasActiveSession() {
    return Boolean(currentSessionId && currentUserId);
}

function setChatInputEnabled(enabled, placeholder) {
    if (chatInput) {
        chatInput.disabled = !enabled;
        chatInput.placeholder = placeholder || (enabled ? 'Ask Kurama...' : 'Enter details to unlock chat');
    }
    if (chatSendButton) {
        chatSendButton.disabled = !enabled;
        chatSendButton.classList.toggle('opacity-50', !enabled);
        chatSendButton.classList.toggle('cursor-not-allowed', !enabled);
    }
}

function setResponseBusyState(isBusy) {
    if (chatInput && hasActiveSession()) {
        chatInput.disabled = false;
        chatInput.placeholder = isBusy ? 'Type your next question...' : 'Ask Kurama...';
    }
    if (!chatSendButton) return;

    chatSendButton.disabled = false;
    chatSendButton.classList.remove('opacity-50', 'cursor-not-allowed');
    chatSendButton.classList.toggle('chat-stop-button', isBusy);
    chatSendButton.innerHTML = isBusy ? '<i class="fas fa-stop"></i>' : '<i class="fas fa-paper-plane"></i>';
    chatSendButton.setAttribute('aria-label', isBusy ? 'Stop generating' : 'Send message');
    chatSendButton.setAttribute('title', isBusy ? 'Stop generating' : 'Send message');
}

window.clearKuramaHistory = clearStoredMessages;

function scrollChat() { 
    if (chatBox) {
        requestAnimationFrame(() => {
            const lastMsg = chatBox.lastElementChild;
            if (lastMsg) {
                lastMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        });
    }
}
function appendHumanMsg(t, remember = true) {
    if (!chatBox) return;
    chatBox.innerHTML += `<div class="msg-bubble msg-human">${escapeHtml(t)}</div>`;
    if (remember) rememberMessage('human', t);
    scrollChat();
}

function appendAiMsg(t, remember = true) {
    if (!chatBox) return;
    chatBox.innerHTML += `<div class="msg-bubble msg-ai">${renderAssistantMessage(t)}</div>`;
    if (remember) rememberMessage('ai', t);
    scrollChat();
}

function startResponseStatus() {
    const typingEl = document.getElementById('kurama-typing');
    const typingText = document.getElementById('kurama-typing-text');
    if (!typingEl || !typingText) return;

    const states = [
        'Kurama is reading the scrolls',
        "Searching portfolio data",
        'Preparing a readable answer',
    ];
    let index = 0;
    typingText.textContent = states[index];
    typingEl.classList.remove('hidden');
    clearInterval(responseStatusTimer);
    responseStatusTimer = setInterval(() => {
        index = (index + 1) % states.length;
        typingText.textContent = states[index];
    }, 1600);
}

function stopResponseStatus() {
    clearInterval(responseStatusTimer);
    responseStatusTimer = null;
    document.getElementById('kurama-typing')?.classList.add('hidden');
}

if (chatInput) {
    chatInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && assistantState.isBusy) {
            event.preventDefault();
            showSpeechBubble('I am still generating. You can stop it or wait.', 2200);
        }
    });
}

if (chatSendButton) {
    chatSendButton.addEventListener('click', (event) => {
        if (!assistantState.isBusy) return;
        event.preventDefault();
        activeAssistantController?.abort();
    });
}

/* -- CHAT FORM ---------------------------------------- */
if (chatForm) {
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = chatInput.value.trim();
        if (!question) return;
        if (!hasActiveSession()) {
            showWelcomeScreen();
            showRegModal();
            return;
        }
        if (assistantState.isBusy) {
            showSpeechBubble('One answer at a time. I am still searching.', 2200);
            return;
        }

        appendHumanMsg(question);
        chatInput.value = '';
        assistantState.isBusy = true;
        activeAssistantController = new AbortController();
        setResponseBusyState(true);
        startResponseStatus();

        const len = question.length;
        if (len > 120) {
            setPetState('tbb');
        } else if (len > 60) {
            setPetState('angry');
        } else {
            setPetState('thinking');
        }

        const aiBubble = document.createElement('div');
        aiBubble.className = 'msg-bubble msg-ai';
        aiBubble.innerHTML = '<div class="chat-generating"><i class="fas fa-circle-notch fa-spin text-portfolio-orange"></i><span>Generating answer</span></div><div class="chat-loading-bar" aria-hidden="true"><span></span></div>';
        chatBox.appendChild(aiBubble); scrollChat();

        let full = '';
        try {
            const fd = new URLSearchParams();
            fd.append('question', question);
            fd.append('session_id', currentSessionId);
            fd.append('user_id',    currentUserId);
            fd.append('context_page', assistantState.currentPage);
            const resp = await fetch('/api/assistant/', {
                method:'POST',
                headers:{'Content-Type':'application/x-www-form-urlencoded'},
                body:fd,
                signal: activeAssistantController.signal
            });
            if (!resp.ok) throw new Error();

            aiBubble.innerHTML = '';
            const reader  = resp.body.getReader();
            const decoder = new TextDecoder();
            setPetState('speaking');
            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, {stream:true});
                full += chunk;
                aiBubble.innerHTML = renderAssistantMessage(full);
                scrollChat();
            }
            rememberMessage('ai', full);
            stopResponseStatus();

            const lt = full.toLowerCase();
            let next = 'idle';
            if (lt.includes('great') || lt.includes('power') || lt.includes('master') || lt.includes('strong')) next = 'happy';
            if (lt.includes('fool') || lt.includes('pathetic') || lt.includes('dare') || lt.includes('anger'))   next = 'angry';
            if (lt.match(/!\s*$/) || lt.includes('impossible') || lt.includes('incredible'))                       next = 'happy';
            
            setPetState(next);
            setTimeout(() => { if (petMood === next) setPetState('idle'); }, 4000);
            
            // Keep focus for desktop users
            if (window.innerWidth > 768) chatInput.focus();
        } catch (error) {
            stopResponseStatus();
            const wasStopped = error?.name === 'AbortError';
            const errorMessage = wasStopped ? 'Response stopped.' : 'Chakra link severed. Try again.';
            if (full) {
                const stoppedAnswer = `${full}\n\n${errorMessage}`;
                aiBubble.innerHTML = renderAssistantMessage(stoppedAnswer);
                rememberMessage('ai', stoppedAnswer);
            } else {
                aiBubble.innerHTML = wasStopped ? `<span class="chat-muted">${errorMessage}</span>` : `<span class='text-red-400'>${errorMessage}</span>`;
                rememberMessage('ai', errorMessage);
            }
            setPetState('idle');
        } finally {
            assistantState.isBusy = false;
            activeAssistantController = null;
            if (hasActiveSession()) setResponseBusyState(false);
            if (window.innerWidth > 768) chatInput?.focus();
        }
    });
}

/* -- BOOT --------------------------------------------- */
window.addEventListener('DOMContentLoaded', () => {
    window.appReadyForAssistant = true;
    if (!currentSessionId) setTimeout(showRegModal, 1500);
});


// Append to kurama.js
const cuteEyes = document.querySelectorAll('.cute-fox-eye-l, .cute-fox-eye-r');
if (cuteEyes.length > 0 && kuramaWidget) {
    document.addEventListener('mousemove', (e) => {
        if (!assistantState.isOpen && petMood !== 'sleep') {
            const rect = kuramaWidget.getBoundingClientRect();
            // Center of the widget
            const cx = rect.left + rect.width / 2;
            const cy = rect.top + rect.height / 2;
            // Vector from center to mouse
            const dx = e.clientX - cx;
            const dy = e.clientY - cy;
            // Dist
            const dist = Math.sqrt(dx*dx + dy*dy);
            
            // Only move if mouse is relatively close but not inside
            if (dist < 400 && dist > 20) {
                // Max pupil displacement = 3px
                const maxD = 4;
                const tx = (dx / dist) * maxD;
                const ty = (dy / dist) * maxD;
                cuteEyes.forEach(eye => {
                    // Ensure we preserve any existing CSS transforms like blinking by wrapping inside CSS
                    eye.style.transform = `translate(${tx}px, ${ty}px)`;
                });
            } else {
                cuteEyes.forEach(eye => { eye.style.transform = ''; });
            }
        } else {
            cuteEyes.forEach(eye => { eye.style.transform = ''; });
        }
    });
}

// -- MOBILE VISUAL VIEWPORT (KEYBOARD) FIX --
if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', () => {
        if (assistantState.isOpen && window.innerWidth <= 768) {
            const h = window.visualViewport.height;
            document.body.style.height = h + 'px';
            assistantPanel.style.height = h + 'px';
            scrollChat();
        } else {
            document.body.style.height = '';
            assistantPanel.style.height = '';
        }
    });
}

// -- KURAMA CLICK REACTION (FIRE CHAKRA) --
kuramaWidget?.addEventListener('mousedown', () => {
    if (assistantState.isOpen) return;
    setPetState('attacking');
    setTimeout(() => { if (petMood === 'attacking') setPetState('idle'); }, 2000);
});
