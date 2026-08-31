document.addEventListener("DOMContentLoaded", () => {
    const messagesContainer = document.getElementById("messages-container");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const typingIndicator = document.getElementById("typing-indicator");
    const connectionDot = document.getElementById("connection-dot");
    const connectionStatus = document.getElementById("connection-status");
    const clearChatBtn = document.getElementById("clear-chat-btn");
    const chipButtons = document.querySelectorAll(".chip-btn");

    let socket = null;
    let isWebSocketReady = false;

    // 1. Establish WebSocket Connection
    function initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

        try {
            socket = new WebSocket(wsUrl);

            socket.onopen = () => {
                isWebSocketReady = true;
                connectionDot.className = "w-2 h-2 rounded-full bg-emerald-400";
                connectionStatus.textContent = "Connected via WebSocket";
            };

            socket.onmessage = (event) => {
                hideTypingIndicator();
                try {
                    const data = JSON.parse(event.data);
                    appendBotMessage(data);
                } catch (e) {
                    console.error("Error parsing WebSocket response:", e);
                }
            };

            socket.onclose = () => {
                isWebSocketReady = false;
                connectionDot.className = "w-2 h-2 rounded-full bg-amber-400";
                connectionStatus.textContent = "Connected via HTTP Fallback";
            };

            socket.onerror = (err) => {
                console.warn("WebSocket encountered error, falling back to HTTP:", err);
                isWebSocketReady = false;
            };
        } catch (err) {
            console.warn("WebSocket init error, will use REST:", err);
            isWebSocketReady = false;
        }
    }

    initWebSocket();

    // 2. Handle Message Submission
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        sendMessage(text);
        userInput.value = "";
    });

    // 3. Handle Quick Suggestion Chips
    chipButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            if (query) {
                sendMessage(query);
            }
        });
    });

    // 4. Clear Chat
    clearChatBtn.addEventListener("click", () => {
        messagesContainer.innerHTML = `
            <div class="flex items-start space-x-3 bot-message">
                <div class="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white flex-shrink-0 text-xs shadow">
                    <i class="fa-solid fa-graduation-cap"></i>
                </div>
                <div class="flex-1 bg-slate-700/60 border border-slate-600/60 rounded-2xl rounded-tl-none p-4 shadow-sm max-w-2xl">
                    <div class="flex items-center justify-between mb-1.5">
                        <span class="text-xs font-semibold text-brand-300">Global Language Academy</span>
                        <span class="text-[10px] text-slate-400">Just now</span>
                    </div>
                    <div class="text-sm text-slate-200 leading-relaxed">
                        <p>Chat cleared. How else can I assist with your language journey?</p>
                    </div>
                </div>
            </div>
        `;
    });

    function sendMessage(text) {
        appendUserMessage(text);
        showTypingIndicator();

        if (isWebSocketReady && socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ message: text }));
        } else {
            // REST API Fallback
            fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, channel: "web" })
            })
            .then((res) => res.json())
            .then((data) => {
                hideTypingIndicator();
                appendBotMessage(data);
            })
            .catch((err) => {
                hideTypingIndicator();
                console.error("Chat API error:", err);
                appendBotMessage({
                    answer: "An error occurred while contacting the support service. Please try again.",
                    tier: "error",
                    sources: [],
                    confidence: 0,
                    escalate_to_human: true,
                    ticket_id: "ERR-LOCAL"
                });
            });
        }
    }

    function appendUserMessage(text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "flex items-start justify-end space-x-3";
        msgDiv.innerHTML = `
            <div class="bg-brand-600 text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-md max-w-xl text-sm leading-relaxed">
                ${escapeHtml(text)}
            </div>
            <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-slate-300 flex-shrink-0 text-xs shadow">
                <i class="fa-solid fa-user"></i>
            </div>
        `;
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendBotMessage(data) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "flex items-start space-x-3 bot-message";

        // Render formatted response
        const formattedAnswer = renderMarkdownSimple(data.answer);

        let statusIndicator = "";
        if (data.escalate_to_human && data.ticket_id) {
            statusIndicator = `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30"><i class="fa-solid fa-ticket mr-1"></i>Ticket: ${data.ticket_id}</span>`;
        }

        msgDiv.innerHTML = `
            <div class="w-8 h-8 rounded-full ${data.escalate_to_human ? 'bg-amber-600' : 'bg-brand-600'} flex items-center justify-center text-white flex-shrink-0 text-xs shadow">
                <i class="fa-solid ${data.escalate_to_human ? 'fa-headset' : 'fa-graduation-cap'}"></i>
            </div>
            <div class="flex-1 bg-slate-700/60 border border-slate-600/60 rounded-2xl rounded-tl-none p-4 shadow-sm max-w-2xl">
                <div class="flex items-center justify-between gap-2 mb-2">
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-semibold text-brand-300">Global Language Academy</span>
                        ${statusIndicator}
                    </div>
                    <span class="text-[10px] text-slate-400">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div class="text-sm text-slate-200 leading-relaxed bot-response-content">
                    ${formattedAnswer}
                </div>
            </div>
        `;

        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        messagesContainer.appendChild(typingIndicator);
        typingIndicator.classList.remove("hidden");
        typingIndicator.classList.add("flex");
        sendBtn.disabled = true;
        scrollToBottom();
    }

    function hideTypingIndicator() {
        typingIndicator.classList.add("hidden");
        typingIndicator.classList.remove("flex");
        sendBtn.disabled = false;
    }

    function scrollToBottom() {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 50);
    }

    function escapeHtml(string) {
        return String(string)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function renderMarkdownSimple(text) {
        if (!text) return "";
        try {
            if (typeof marked !== "undefined" && typeof marked.parse === "function") {
                return marked.parse(text, { breaks: true, gfm: true });
            }
        } catch (e) {
            console.warn("Marked.js parse error:", e);
        }

        // Fallback parser
        let html = text
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>")
            .replace(/^### (.*$)/gim, "<h3>$1</h3>")
            .replace(/^## (.*$)/gim, "<h2>$1</h2>")
            .replace(/^# (.*$)/gim, "<h1>$1</h1>")
            .replace(/^\s*-\s+(.*)$/gim, "<li>$1</li>")
            .replace(/\n\n/g, "</p><p>")
            .replace(/\n/g, "<br/>");

        html = html.replace(/(<li>.*<\/li>)/gis, "<ul>$1</ul>");
        return `<p>${html}</p>`;
    }
});
