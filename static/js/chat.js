// Student Chatbot Module

document.addEventListener('DOMContentLoaded', () => {
    setupChatListeners();
});

function setupChatListeners() {
    const chatForm = document.getElementById('chatForm');
    const newChatBtn = document.getElementById('newChatBtn');

    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('userInput');
            const question = input.value.trim();
            if (!question) return;

            input.value = '';
            await sendQuestion(question);
        });
    }

    if (newChatBtn) {
        newChatBtn.addEventListener('click', async () => {
            await createNewChatSession();
        });
    }

    // Dynamic delegate for sample question buttons
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.sample-btn');
        if (btn) {
            const query = btn.getAttribute('data-query');
            if (query) {
                await sendQuestion(query);
            }
        }
    });
}

// Load Chat History list
async function loadChatHistory() {
    if (!state.token) return;
    try {
        const sessions = await apiRequest('/api/chat/sessions');
        state.sessions = sessions;
        renderHistoryList(sessions);
    } catch (err) {
        console.error('Failed to load chat history:', err);
    }
}

function renderHistoryList(sessions) {
    const container = document.getElementById('chatHistoryList');
    if (!container) return;
    container.innerHTML = '';

    if (!sessions || sessions.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem; padding: 0.5rem;">No past chats</div>';
        return;
    }

    const safeEscape = window.escapeHtml || escapeHtml;

    sessions.forEach(s => {
        const item = document.createElement('div');
        item.className = `chat-history-item ${s.id === state.currentSessionId ? 'active' : ''}`;
        
        const titleSpan = document.createElement('span');
        titleSpan.style.cssText = 'overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;';
        titleSpan.innerHTML = `<i class="fa-regular fa-message"></i> ${safeEscape(s.title)}`;
        
        const trashBtn = document.createElement('i');
        trashBtn.className = 'fa-solid fa-trash text-danger';
        trashBtn.style.cssText = 'font-size: 0.75rem; opacity: 0.7; padding: 4px; cursor: pointer;';
        trashBtn.title = 'Delete Session';
        
        trashBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            await deleteChatSession(s.id);
        });

        item.appendChild(titleSpan);
        item.appendChild(trashBtn);
        item.addEventListener('click', () => loadChatSessionMessages(s.id));
        container.appendChild(item);
    });
}

async function createNewChatSession() {
    if (!state.token) {
        showToast('Please log in to start a new chat session.', 'info');
        const modal = document.getElementById('authModal');
        if (modal) modal.classList.remove('hidden');
        return;
    }
    try {
        const session = await apiRequest('/api/chat/sessions', 'POST', { title: "New Conversation" });
        state.currentSessionId = session.id;
        clearChatArea();
        await loadChatHistory();
    } catch (err) {
        console.error('Failed to create new chat session:', err);
    }
}

async function loadChatSessionMessages(sessionId) {
    state.currentSessionId = sessionId;
    renderHistoryList(state.sessions);

    try {
        const data = await apiRequest(`/api/chat/sessions/${sessionId}/messages`);
        renderMessages(data.messages);
    } catch (err) {
        console.error(`Failed to load messages for session ${sessionId}:`, err);
    }
}

function clearChatArea() {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
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
    if (!container) return;
    container.innerHTML = '';

    if (!messages || messages.length === 0) {
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
        showToast('Please log in to chat with the AI Assistant.', 'info');
        const modal = document.getElementById('authModal');
        if (modal) modal.classList.remove('hidden');
        return;
    }

    // Ensure session exists
    if (!state.currentSessionId) {
        try {
            const session = await apiRequest('/api/chat/sessions', 'POST', { title: question.substring(0, 30) });
            state.currentSessionId = session.id;
            clearChatArea();
        } catch (e) {
            console.error('Failed to initialize session before sending question:', e);
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
        await loadChatHistory();
    } catch (err) {
        console.error('Failed to retrieve AI response:', err);
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) loadingElem.remove();
        appendMessageBubble('ai', 'Error processing question. Please check connection.', [], getCurrentTimeStr());
    }
}

function appendMessageBubble(sender, text, sources = [], timestamp = '') {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${sender}`;

    const avatarIcon = sender === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-graduation-cap"></i>';
    const safeEscape = window.escapeHtml || escapeHtml;
    
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources-box">
                <div class="sources-header"><i class="fa-solid fa-file-contract"></i> Retrieved Official Sources (${sources.length})</div>
        `;
        sources.forEach(src => {
            sourcesHtml += `
                <div class="source-item">
                    <div class="source-title">📄 ${safeEscape(src.document_name)}</div>
                    <div class="source-detail">Page ${src.page || 1} • Section: ${safeEscape(src.section || 'General')}</div>
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
            <span style="font-size: 0.65rem; color: var(--text-muted); display: block; margin-top: 0.4rem; text-align: right;">${safeEscape(timestamp)}</span>
        </div>
    `;

    container.appendChild(bubble);
}

function appendLoadingBubble(id) {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    
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
    } catch (err) {
        console.error(`Failed to delete session ${sessionId}:`, err);
    }
}
window.deleteChatSession = deleteChatSession;

function scrollToBottom() {
    const container = document.getElementById('chatMessages');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

function getCurrentTimeStr() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
}

function formatMessageText(text) {
    if (!text) return '';
    const safeEscape = window.escapeHtml || escapeHtml;
    let formatted = safeEscape(text);
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}
