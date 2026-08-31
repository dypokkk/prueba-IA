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

    // Persistent Multi-turn Session Identifier
    let currentSessionId = sessionStorage.getItem("gla_session_id");
    if (!currentSessionId) {
        currentSessionId = "web_" + Math.random().toString(36).substring(2, 10);
        sessionStorage.setItem("gla_session_id", currentSessionId);
    }

    // 1. Establish WebSocket Connection
    function initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

        try {
            socket = new WebSocket(wsUrl);

            socket.onopen = () => {
                isWebSocketReady = true;
                connectionDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50";
                connectionStatus.textContent = "Conectado en Tiempo Real (WebSocket)";
            };

            socket.onmessage = (event) => {
                hideTypingIndicator();
                try {
                    const data = JSON.parse(event.data);
                    if (data.session_id) {
                        currentSessionId = data.session_id;
                        sessionStorage.setItem("gla_session_id", currentSessionId);
                    }
                    if (data.tier !== "system") {
                        appendBotMessage(data);
                    }
                } catch (e) {
                    console.error("Error parsing WebSocket response:", e);
                }
            };

            socket.onclose = () => {
                isWebSocketReady = false;
                connectionDot.className = "w-2.5 h-2.5 rounded-full bg-amber-400 shadow-sm shadow-amber-400/50";
                connectionStatus.textContent = "Conectado vía HTTP Fallback";
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

    // 4. Clear Chat & Reset Session Memory
    if (clearChatBtn) {
        clearChatBtn.addEventListener("click", () => {
            // Notify backend to clear session history
            if (isWebSocketReady && socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ action: "clear", session_id: currentSessionId }));
            }
            fetch("/api/chat/clear", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: currentSessionId })
            }).catch(() => {});

            // Generate new session ID
            currentSessionId = "web_" + Math.random().toString(36).substring(2, 10);
            sessionStorage.setItem("gla_session_id", currentSessionId);

            messagesContainer.innerHTML = `
                <div class="flex items-start space-x-3.5 bot-message">
                    <div class="w-9 h-9 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white flex-shrink-0 text-xs shadow-md border border-white/20">
                        <i class="fa-solid fa-graduation-cap"></i>
                    </div>
                    <div class="glass-bubble rounded-3xl rounded-tl-none p-5 text-slate-100 max-w-2xl text-sm leading-relaxed">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs font-bold text-brand-300 tracking-wide uppercase">Global Language Academy</span>
                            <span class="text-[10px] text-slate-400 font-mono">En vivo</span>
                        </div>
                        <p>Conversación reiniciada con éxito. ¿En qué idioma o programa estás interesado hoy?</p>
                    </div>
                </div>
            `;
        });
    }

    function sendMessage(text) {
        appendUserMessage(text);
        showTypingIndicator();

        if (isWebSocketReady && socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ message: text, session_id: currentSessionId }));
        } else {
            // REST API Fallback
            fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    channel: "web",
                    session_id: currentSessionId
                })
            })
            .then((res) => res.json())
            .then((data) => {
                hideTypingIndicator();
                if (data.session_id) {
                    currentSessionId = data.session_id;
                    sessionStorage.setItem("gla_session_id", currentSessionId);
                }
                appendBotMessage(data);
            })
            .catch((err) => {
                hideTypingIndicator();
                console.error("Chat API error:", err);
                appendBotMessage({
                    answer: "Ocurrió un error al contactar al servicio de admisiones. Por favor intenta de nuevo.",
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
        msgDiv.className = "flex items-start justify-end space-x-3.5 user-message-wrapper";
        msgDiv.innerHTML = `
            <div class="user-bubble text-white rounded-3xl rounded-tr-none px-5 py-3.5 max-w-xl text-sm leading-relaxed shadow-lg">
                ${escapeHtml(text)}
            </div>
            <div class="w-9 h-9 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white flex-shrink-0 text-xs shadow-md border border-white/20">
                <i class="fa-solid fa-user"></i>
            </div>
        `;
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendBotMessage(data) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "flex items-start space-x-3.5 bot-message";

        const formattedAnswer = renderMarkdownSimple(data.answer);

        let badgeTier = "";
        if (data.tier === "deterministic") {
            badgeTier = `<span class="badge-deterministic px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"><i class="fa-solid fa-bolt text-[9px] mr-1"></i>Determinista (${data.latency_ms}ms)</span>`;
        } else if (data.tier === "ai_rag") {
            badgeTier = `<span class="badge-ai px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"><i class="fa-solid fa-wand-magic-sparkles text-[9px] mr-1"></i>Gemini 3.5 Flash Lite (${data.latency_ms}ms)</span>`;
        } else if (data.tier === "cache") {
            badgeTier = `<span class="badge-cache px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"><i class="fa-solid fa-database text-[9px] mr-1"></i>Caché (${data.latency_ms}ms)</span>`;
        } else if (data.tier === "escalation") {
            badgeTier = `<span class="badge-escalated px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"><i class="fa-solid fa-headset text-[9px] mr-1"></i>Escalado a Soporte</span>`;
        }

        let ticketBadge = "";
        if (data.ticket_id) {
            ticketBadge = `
                <div class="mt-3.5 p-3 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between text-xs text-rose-300">
                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-ticket"></i> Ticket de Soporte Creado:</span>
                    <strong class="font-mono bg-rose-500/20 px-2 py-0.5 rounded-lg text-white border border-rose-400/30">${data.ticket_id}</strong>
                </div>
            `;
        }

        let sourcesBadge = "";
        if (data.sources && data.sources.length > 0 && !data.escalate_to_human) {
            const sourceTags = data.sources.map(s => `<span class="bg-white/5 border border-white/10 px-2 py-0.5 rounded-lg text-[10px] text-slate-300 font-mono">${escapeHtml(s)}</span>`).join(" ");
            sourcesBadge = `
                <div class="mt-3.5 pt-2.5 border-t border-white/10 flex flex-wrap items-center gap-1.5">
                    <span class="text-[10px] text-slate-400 font-medium"><i class="fa-solid fa-book-open mr-1"></i>Fuentes oficiales:</span>
                    ${sourceTags}
                </div>
            `;
        }

        msgDiv.innerHTML = `
            <div class="w-9 h-9 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white flex-shrink-0 text-xs shadow-md border border-white/20">
                <i class="fa-solid fa-graduation-cap"></i>
            </div>
            <div class="glass-bubble rounded-3xl rounded-tl-none p-5 text-slate-100 max-w-2xl text-sm leading-relaxed">
                <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <span class="text-xs font-bold text-brand-300 tracking-wide uppercase">Global Language Academy</span>
                    ${badgeTier}
                </div>
                <div class="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed">
                    ${formattedAnswer}
                </div>
                ${ticketBadge}
                ${sourcesBadge}
            </div>
        `;

        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        if (typingIndicator) {
            typingIndicator.classList.remove("hidden");
            scrollToBottom();
        }
    }

    function hideTypingIndicator() {
        if (typingIndicator) {
            typingIndicator.classList.add("hidden");
        }
    }

    function scrollToBottom() {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 50);
    }

    function escapeHtml(text) {
        if (!text) return "";
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function renderMarkdownSimple(md) {
        if (!md) return "";
        let html = md
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code class="bg-white/10 px-1.5 py-0.5 rounded text-brand-300 font-mono text-xs border border-white/10">$1</code>')
            .replace(/### (.*?)\n/g, '<h4 class="text-white font-bold text-sm mt-3 mb-1">$1</h4>')
            .replace(/## (.*?)\n/g, '<h3 class="text-white font-bold text-base mt-4 mb-2">$1</h3>')
            .replace(/# (.*?)\n/g, '<h2 class="text-white font-bold text-lg mt-4 mb-2">$1</h2>')
            .replace(/^• (.*?)$/gm, '<li class="ml-4 list-disc">$1</li>')
            .replace(/^- (.*?)$/gm, '<li class="ml-4 list-disc">$1</li>')
            .replace(/\n\n/g, '<div class="h-2"></div>')
            .replace(/\n/g, '<br>');
        return html;
    }
});
