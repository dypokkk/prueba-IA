// Global Modal Toggle Functions
window.toggleChatModal = function() {
    const modal = document.getElementById("chat-modal-container");
    const openIcon = document.getElementById("fab-open-icon");
    const closeIcon = document.getElementById("fab-close-icon");
    const input = document.getElementById("modal-user-input");

    if (!modal) return;

    const isOpen = !modal.classList.contains("opacity-0");

    if (isOpen) {
        // Close modal
        modal.classList.add("scale-95", "opacity-0", "pointer-events-none");
        modal.classList.remove("scale-100", "opacity-100", "pointer-events-auto");
        if (openIcon) openIcon.classList.remove("hidden");
        if (closeIcon) closeIcon.classList.add("hidden");
    } else {
        // Open modal
        modal.classList.remove("scale-95", "opacity-0", "pointer-events-none");
        modal.classList.add("scale-100", "opacity-100", "pointer-events-auto");
        if (openIcon) openIcon.classList.add("hidden");
        if (closeIcon) closeIcon.classList.remove("hidden");
        setTimeout(() => {
            if (input) input.focus();
            scrollToModalBottom();
        }, 150);
    }
};

window.openChatModal = function() {
    const modal = document.getElementById("chat-modal-container");
    const openIcon = document.getElementById("fab-open-icon");
    const closeIcon = document.getElementById("fab-close-icon");
    const input = document.getElementById("modal-user-input");

    if (!modal) return;
    modal.classList.remove("scale-95", "opacity-0", "pointer-events-none");
    modal.classList.add("scale-100", "opacity-100", "pointer-events-auto");
    if (openIcon) openIcon.classList.add("hidden");
    if (closeIcon) closeIcon.classList.remove("hidden");
    setTimeout(() => {
        if (input) input.focus();
        scrollToModalBottom();
    }, 150);
};

window.closeChatModal = function() {
    const modal = document.getElementById("chat-modal-container");
    const openIcon = document.getElementById("fab-open-icon");
    const closeIcon = document.getElementById("fab-close-icon");

    if (!modal) return;
    modal.classList.add("scale-95", "opacity-0", "pointer-events-none");
    modal.classList.remove("scale-100", "opacity-100", "pointer-events-auto");
    if (openIcon) openIcon.classList.remove("hidden");
    if (closeIcon) closeIcon.classList.add("hidden");
};

window.openChatModalWithQuery = function(queryText) {
    window.openChatModal();
    const input = document.getElementById("modal-user-input") || document.getElementById("user-input");
    if (input) {
        input.value = queryText;
        // Dispatch submit event
        const form = document.getElementById("modal-chat-form") || document.getElementById("chat-form");
        if (form) {
            form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
        }
    }
};

function scrollToModalBottom() {
    const container = document.getElementById("modal-messages-container") || document.getElementById("messages-container");
    if (container) {
        setTimeout(() => {
            container.scrollTop = container.scrollHeight;
        }, 50);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Select elements (modal or standalone chat)
    const modalMessagesContainer = document.getElementById("modal-messages-container");
    const modalChatForm = document.getElementById("modal-chat-form");
    const modalUserInput = document.getElementById("modal-user-input");
    const modalTypingIndicator = document.getElementById("modal-typing-indicator");
    const modalConnectionDot = document.getElementById("modal-connection-dot");
    const modalConnectionStatus = document.getElementById("modal-connection-status");
    const modalClearChatBtn = document.getElementById("modal-clear-chat-btn");
    const modalChipButtons = document.querySelectorAll(".modal-chip-btn");

    // Standalone chat elements (if on /chat page)
    const standaloneContainer = document.getElementById("messages-container");
    const standaloneForm = document.getElementById("chat-form");
    const standaloneInput = document.getElementById("user-input");
    const standaloneClearBtn = document.getElementById("clear-chat-btn");
    const standaloneChips = document.querySelectorAll(".chip-btn");

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
                if (modalConnectionDot) modalConnectionDot.className = "w-2 h-2 rounded-full bg-emerald-400";
                if (modalConnectionStatus) modalConnectionStatus.textContent = "En línea";
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
                if (modalConnectionDot) modalConnectionDot.className = "w-2 h-2 rounded-full bg-amber-400";
                if (modalConnectionStatus) modalConnectionStatus.textContent = "HTTP Fallback";
            };

            socket.onerror = (err) => {
                console.warn("WebSocket encountered error, fallback to HTTP:", err);
                isWebSocketReady = false;
            };
        } catch (err) {
            console.warn("WebSocket init error, will use REST:", err);
            isWebSocketReady = false;
        }
    }

    initWebSocket();

    // 2. Handle Message Submission (Modal)
    if (modalChatForm) {
        modalChatForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const text = modalUserInput ? modalUserInput.value.trim() : "";
            if (!text) return;

            sendMessage(text);
            if (modalUserInput) modalUserInput.value = "";
        });
    }

    // Handle Message Submission (Standalone if on /chat)
    if (standaloneForm) {
        standaloneForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const text = standaloneInput ? standaloneInput.value.trim() : "";
            if (!text) return;

            sendMessage(text);
            if (standaloneInput) standaloneInput.value = "";
        });
    }

    // 3. Handle Suggestion Chips
    modalChipButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            if (query) {
                sendMessage(query);
            }
        });
    });

    standaloneChips.forEach((btn) => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            if (query) {
                sendMessage(query);
            }
        });
    });

    // 4. Clear Chat & Reset Session Memory
    function resetChatUI() {
        if (isWebSocketReady && socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: "clear", session_id: currentSessionId }));
        }
        fetch("/api/chat/clear", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: currentSessionId })
        }).catch(() => {});

        currentSessionId = "web_" + Math.random().toString(36).substring(2, 10);
        sessionStorage.setItem("gla_session_id", currentSessionId);

        const welcomeHtml = `
            <div class="flex items-start space-x-3 bot-message">
                <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white flex-shrink-0 text-xs shadow border border-white/20">
                    <i class="fa-solid fa-graduation-cap"></i>
                </div>
                <div class="glass-bubble rounded-2xl rounded-tl-none p-4 text-slate-100 max-w-[85%] text-xs sm:text-sm leading-relaxed">
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-[11px] font-bold text-brand-300 uppercase tracking-wide">Global Language Academy</span>
                        <span class="text-[10px] text-slate-400 font-mono">En vivo</span>
                    </div>
                    <p>Conversación reiniciada con éxito. ¿En qué programa o idioma estás interesado hoy?</p>
                </div>
            </div>
        `;

        if (modalMessagesContainer) modalMessagesContainer.innerHTML = welcomeHtml;
        if (standaloneContainer) standaloneContainer.innerHTML = welcomeHtml;
    }

    if (modalClearChatBtn) modalClearChatBtn.addEventListener("click", resetChatUI);
    if (standaloneClearBtn) standaloneClearBtn.addEventListener("click", resetChatUI);

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
        msgDiv.className = "flex items-start justify-end space-x-2.5 user-message-wrapper";
        msgDiv.innerHTML = `
            <div class="user-bubble text-white rounded-2xl rounded-tr-none px-4 py-2.5 max-w-[85%] text-xs sm:text-sm leading-relaxed shadow-lg">
                ${escapeHtml(text)}
            </div>
            <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white flex-shrink-0 text-xs shadow border border-white/20">
                <i class="fa-solid fa-user text-[11px]"></i>
            </div>
        `;

        if (modalMessagesContainer) modalMessagesContainer.appendChild(msgDiv.cloneNode(true));
        if (standaloneContainer) standaloneContainer.appendChild(msgDiv);
        scrollToModalBottom();
    }

    function appendBotMessage(data) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "flex items-start space-x-3 bot-message";

        const formattedAnswer = renderMarkdownSimple(data.answer);

        let badgeTier = "";
        if (data.tier === "deterministic") {
            badgeTier = `<span class="badge-deterministic px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider"><i class="fa-solid fa-bolt text-[8px] mr-1"></i>Determinista (${data.latency_ms}ms)</span>`;
        } else if (data.tier === "ai_rag") {
            badgeTier = `<span class="badge-ai px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider"><i class="fa-solid fa-wand-magic-sparkles text-[8px] mr-1"></i>Gemini 3.5 Flash Lite (${data.latency_ms}ms)</span>`;
        } else if (data.tier === "cache") {
            badgeTier = `<span class="badge-cache px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider"><i class="fa-solid fa-database text-[8px] mr-1"></i>Caché (${data.latency_ms}ms)</span>`;
        } else if (data.tier === "escalation") {
            badgeTier = `<span class="badge-escalated px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider"><i class="fa-solid fa-headset text-[8px] mr-1"></i>Escalado a Soporte</span>`;
        }

        let ticketBadge = "";
        if (data.ticket_id) {
            ticketBadge = `
                <div class="mt-2.5 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between text-[11px] text-rose-300">
                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-ticket"></i> Ticket de Soporte:</span>
                    <strong class="font-mono bg-rose-500/20 px-2 py-0.5 rounded-md text-white border border-rose-400/30">${data.ticket_id}</strong>
                </div>
            `;
        }

        let sourcesBadge = "";
        if (data.sources && data.sources.length > 0 && !data.escalate_to_human) {
            const sourceTags = data.sources.map(s => `<span class="bg-white/5 border border-white/10 px-1.5 py-0.2 rounded text-[9px] text-slate-300 font-mono">${escapeHtml(s)}</span>`).join(" ");
            sourcesBadge = `
                <div class="mt-2.5 pt-2 border-t border-white/10 flex flex-wrap items-center gap-1">
                    <span class="text-[9px] text-slate-400 font-medium"><i class="fa-solid fa-book-open mr-1"></i>Fuentes:</span>
                    ${sourceTags}
                </div>
            `;
        }

        msgDiv.innerHTML = `
            <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white flex-shrink-0 text-xs shadow border border-white/20">
                <i class="fa-solid fa-graduation-cap"></i>
            </div>
            <div class="glass-bubble rounded-2xl rounded-tl-none p-4 text-slate-100 max-w-[85%] text-xs sm:text-sm leading-relaxed">
                <div class="flex flex-wrap items-center justify-between gap-1.5 mb-1.5">
                    <span class="text-[11px] font-bold text-brand-300 tracking-wide uppercase">Global Language Academy</span>
                    ${badgeTier}
                </div>
                <div class="prose prose-invert prose-xs sm:prose-sm max-w-none text-slate-200 leading-relaxed">
                    ${formattedAnswer}
                </div>
                ${ticketBadge}
                ${sourcesBadge}
            </div>
        `;

        if (modalMessagesContainer) modalMessagesContainer.appendChild(msgDiv.cloneNode(true));
        if (standaloneContainer) standaloneContainer.appendChild(msgDiv);
        scrollToModalBottom();
    }

    function showTypingIndicator() {
        if (modalTypingIndicator) modalTypingIndicator.classList.remove("hidden");
        const standaloneTyping = document.getElementById("typing-indicator");
        if (standaloneTyping) standaloneTyping.classList.remove("hidden");
        scrollToModalBottom();
    }

    function hideTypingIndicator() {
        if (modalTypingIndicator) modalTypingIndicator.classList.add("hidden");
        const standaloneTyping = document.getElementById("typing-indicator");
        if (standaloneTyping) standaloneTyping.classList.add("hidden");
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
            .replace(/### (.*?)\n/g, '<h4 class="text-white font-bold text-xs sm:text-sm mt-2.5 mb-1">$1</h4>')
            .replace(/## (.*?)\n/g, '<h3 class="text-white font-bold text-sm sm:text-base mt-3 mb-1.5">$1</h3>')
            .replace(/# (.*?)\n/g, '<h2 class="text-white font-bold text-base sm:text-lg mt-3.5 mb-2">$1</h2>')
            .replace(/^• (.*?)$/gm, '<li class="ml-3 list-disc">$1</li>')
            .replace(/^- (.*?)$/gm, '<li class="ml-3 list-disc">$1</li>')
            .replace(/\n\n/g, '<div class="h-1.5"></div>')
            .replace(/\n/g, '<br>');
        return html;
    }
});
