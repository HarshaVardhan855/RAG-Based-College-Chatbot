// Student Chatbot Module

document.addEventListener('DOMContentLoaded', () => {
    setupChatListeners();
});

function setupChatListeners() {
    const chatForm = document.getElementById('chatForm');
    const newChatBtn = document.getElementById('newChatBtn');
    const sampleBtns = document.querySelectorAll('.sample-btn');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('userInput');
        const question = input.value.trim();
        if (!question) return;

        input.value = '';
        await sendQuestion(question);
    });

    newChatBtn.addEventListener('click', async () => {
        await createNewChatSession();
    });

    sampleBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const query = btn.getAttribute('data-query');
            if (query) {
                await sendQuestion(query);
            }
        });
    });
}

// Load Chat History list
async function loadChatHistory() {
    if (!state.token) return;
    try {
        const sessions = await apiRequest('/api/chat/sessions');
        state.sessions = sessions;
        renderHistoryList(sessions);
    } catch (err) {}
}

function renderHistoryList(sessions) {
    const container = document.getElementById('chatHistoryList');
    container.innerHTML = '';

    if (sessions.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem; padding: 0.5rem;">No past chats</div>';
        return;
    }

    sessions.forEach(s => {
        const item = document.createElement('div');
        item.className = `chat-history-item ${s.id === state.currentSessionId ? 'active' : ''}`;
        item.innerHTML = `
            <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;"><i class="fa-regular fa-message"></i> ${escapeHtml(s.title)}</span>
            <i class="fa-solid fa-trash text-danger" style="font-size: 0.75rem; opacity: 0.7;" onclick="event.stopPropagation(); deleteChatSession(${s.id})"></i>
        `;
        item.addEventListener('click', () => loadChatSessionMessages(s.id));
        container.appendChild(item);
    });
}

async function createNewChatSession() {
    if (!state.token) {
        document.getElementById('authModal').classList.remove('hidden');
        return;
    }
    try {
        const session = await apiRequest('/api/chat/sessions', 'POST', { title: "New Conversation" });
        state.currentSessionId = session.id;
        clearChatArea();
        await loadChatHistory();
    } catch (err) {}
}

async function loadChatSessionMessages(sessionId) {
    state.currentSessionId = sessionId;
    renderHistoryList(state.sessions);

    try {
        const data = await apiRequest(`/api/chat/sessions/${sessionId}/messages`);
        renderMessages(data.messages);
    } catch (err) {}
}

function clearChatArea() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-icon"><i class="fa-solid fa-robot"></i></div>
            <h2>New Conversation</h2>
            <p>Ask any college-related question below. Answers are strictly grounded in official college documents.</p>
        </div>
    `;
}

function renderMessages(messages) {
    const container = document.getElementById('chatMessages');
    container.innerHTML = '';

    if (messages.length === 0) {
        clearChatArea();
        return;
    }

    messages.forEach(m => {
        appendMessageBubble(m.sender, m.message, m.sources, m.timestamp);
    });

    scrollToBottom();
}

async function sendQuestion(question) {
    if (!state.token) {
        document.getElementById('authModal').classList.remove('hidden');
        return;
    }

    // Ensure session exists
    if (!state.currentSessionId) {
        try {
            const session = await apiRequest('/api/chat/sessions', 'POST', { title: question.substring(0, 30) });
            state.currentSessionId = session.id;
            clearChatArea();
        } catch (e) {
            return;
        }
    }

    // Remove welcome card if present
    const welcomeCard = document.querySelector('.welcome-card');
    if (welcomeCard) welcomeCard.remove();

    // 1. Append User Bubble
    appendMessageBubble('user', question, [], getCurrentTimeStr());
    scrollToBottom();

    // 2. Append Loading AI Bubble
    const loadingId = 'loading_' + Date.now();
    appendLoadingBubble(loadingId);
    scrollToBottom();

    // 3. Request RAG Response
    try {
        const res = await apiRequest(`/api/chat/sessions/${state.currentSessionId}/messages`, 'POST', { question });
        
        // Remove loading bubble
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) loadingElem.remove();

        // Append AI Response Bubble
        appendMessageBubble('ai', res.ai_message.message, res.ai_message.sources, res.ai_message.timestamp);
        scrollToBottom();

        // Refresh History
        loadChatHistory();
    } catch (err) {
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) loadingElem.remove();
        appendMessageBubble('ai', 'Error processing question. Please check connection.', [], getCurrentTimeStr());
    }
}

function appendMessageBubble(sender, text, sources = [], timestamp = '') {
    const container = document.getElementById('chatMessages');
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${sender}`;

    let avatarIcon = sender === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-graduation-cap"></i>';
    
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources-box">
                <div class="sources-header"><i class="fa-solid fa-file-contract"></i> Retrieved Official Sources (${sources.length})</div>
        `;
        sources.forEach(src => {
            sourcesHtml += `
                <div class="source-item">
                    <div class="source-title">📄 ${escapeHtml(src.document_name)}</div>
                    <div class="source-detail">Page ${src.page} • Section: ${escapeHtml(src.section)}</div>
                </div>
            `;
        });
        sourcesHtml += `</div>`;
    }

    bubble.innerHTML = `
        <div class="msg-avatar">${avatarIcon}</div>
        <div class="msg-content">
            <div>${formatMessageText(text)}</div>
            ${sourcesHtml}
            <span style="font-size: 0.65rem; color: var(--text-muted); display: block; margin-top: 0.4rem; text-align: right;">${timestamp}</span>
        </div>
    `;

    container.appendChild(bubble);
}

function appendLoadingBubble(id) {
    const container = document.getElementById('chatMessages');
    const bubble = document.createElement('div');
    bubble.id = id;
    bubble.className = 'message-bubble ai';
    bubble.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-spinner fa-spin"></i></div>
        <div class="msg-content">
            <span style="color: var(--text-muted); font-style: italic;">Searching vector database & generating grounded answer...</span>
        </div>
    `;
    container.appendChild(bubble);
}

async function deleteChatSession(sessionId) {
    if (!confirm('Are you sure you want to delete this chat session?')) return;
    try {
        await apiRequest(`/api/chat/sessions/${sessionId}`, 'DELETE');
        if (state.currentSessionId === sessionId) {
            state.currentSessionId = null;
            clearChatArea();
        }
        await loadChatHistory();
        showToast('Chat session deleted', 'info');
    } catch (err) {}
}

function scrollToBottom() {
    const container = document.getElementById('chatMessages');
    container.scrollTop = container.scrollHeight;
}

function getCurrentTimeStr() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatMessageText(text) {
    if (!text) return '';
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}
