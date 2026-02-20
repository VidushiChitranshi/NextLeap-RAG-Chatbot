const chatWindow = document.getElementById('chat-window');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-btn');

// ── Messaging ────────────────────────────────────────────────────────────

function addMessage(text, sender, citations = [], isFallback = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);

    // Add fallback banner if needed
    if (isFallback && sender === 'bot') {
        const banner = document.createElement('div');
        banner.classList.add('fallback-banner');
        banner.innerHTML = `<span>⚠️</span> I don't have exact info on that, but here's a general answer.`;
        messageDiv.appendChild(banner);
    }

    const content = document.createElement('div');
    content.textContent = text;
    messageDiv.appendChild(content);

    // Add citations
    if (citations && citations.length > 0) {
        const citationsDiv = document.createElement('div');
        citationsDiv.classList.add('citations');
        citations.forEach(cit => {
            const span = document.createElement('span');
            span.classList.add('citation-tag');
            span.textContent = cit;
            citationsDiv.appendChild(span);
        });
        messageDiv.appendChild(citationsDiv);
    }

    chatWindow.appendChild(messageDiv);
    scrollToBottom();
}

function addLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'bot', 'loading-msg');
    loadingDiv.innerHTML = `
        <div class="loading-dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;
    chatWindow.appendChild(loadingDiv);
    scrollToBottom();
    return loadingDiv;
}

function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ── API Calls ────────────────────────────────────────────────────────────

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    chatInput.value = '';
    chatInput.disabled = true;
    sendBtn.disabled = true;

    addMessage(text, 'user');

    const loadingMsg = addLoading();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        
        loadingMsg.remove();

        if (data.success) {
            addMessage(data.answer, 'bot', data.citations, data.is_fallback);
        } else {
            addMessage('Error: ' + (data.error || 'Something went wrong'), 'bot');
        }
    } catch (err) {
        if (loadingMsg) loadingMsg.remove();
        addMessage('Critical failure: Could not connect to the server.', 'bot');
        console.error(err);
    } finally {
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

async function clearHistory() {
    if (!confirm('Are you sure you want to clear the conversation history?')) return;
    
    try {
        await fetch('/clear', { method: 'POST' });
        chatWindow.innerHTML = '';
        addMessage('History cleared. How can I help you today?', 'bot');
    } catch (err) {
        alert('Failed to clear history');
    }
}

// ── Event Listeners ──────────────────────────────────────────────────────

sendBtn.addEventListener('click', sendMessage);

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

clearBtn.addEventListener('click', clearHistory);

// Initial focus
chatInput.focus();
addMessage('Hi! I am the NextLeap RAG Chatbot. Ask me anything about the PM fellowship or other courses.', 'bot');
