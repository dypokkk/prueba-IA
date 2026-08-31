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

    // Persistent Multi-turn Session Identifier (localStorage survives page reload and tab closing)
    let currentSessionId = localStorage.getItem("gla_persistent_session_id");
    if (!currentSessionId) {
        currentSessionId = "web_" + Math.random().toString(36).substring(2, 10);
        localStorage.setItem("gla_persistent_session_id", currentSessionId);
    }

    // Load full conversational history from SQLite API on startup and ask user if they want to resume or start new
    async function loadHistory() {
        if (!currentSessionId) return;
        try {
            const resp = await fetch(`/api/chat/history/${currentSessionId}`);
            if (resp.ok) {
                const data = await resp.json();
                if (data.history && data.history.length > 0) {
                    showResumePrompt(data.history);
                }
            }
        } catch (e) {
            console.warn("Could not load previous history from SQLite:", e);
        }
    }

    function showResumePrompt(historyData) {
        // Prevent duplicate prompt
        if (document.getElementById("gla-resume-prompt")) return;

        const promptDiv = document.createElement("div");
        promptDiv.id = "gla-resume-prompt";
        promptDiv.className = "p-4 mx-3 my-3 rounded-2xl bg-slate-900/95 border border-brand-500/40 text-slate-200 shadow-2xl space-y-2.5 backdrop-blur-md";
        promptDiv.innerHTML = `
            <div class="flex items-center justify-between text-xs">
                <span class="font-bold text-amber-300 flex items-center gap-1.5">
                    <i class="fa-solid fa-clock-rotate-left"></i> Conversación anterior detectada
                </span>
                <span class="text-[10px] text-slate-400 font-mono bg-white/10 px-2 py-0.5 rounded-full">${historyData.length} mensajes</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
                Detectamos un chat anterior guardado. ¿Deseas retomar esta conversación con tu historial o iniciar una nueva desde cero?
            </p>
            <div class="flex items-center gap-2 pt-1">
                <button type="button" id="btn-do-resume" class="flex-1 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold text-xs py-2 px-3 rounded-xl transition-all shadow border border-white/20 flex items-center justify-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-rotate-right text-[10px]"></i> Retomar
                </button>
                <button type="button" id="btn-do-new" class="flex-1 bg-white/10 hover:bg-white/20 text-slate-200 font-semibold text-xs py-2 px-3 rounded-xl transition-all border border-white/10 flex items-center justify-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-plus text-[10px]"></i> Iniciar Nueva
                </button>
            </div>
        `;

        // Insert into only ONE container to avoid duplicate IDs and event listener conflicts
        const targetContainer = modalMessagesContainer || standaloneContainer;
        if (targetContainer) {
            targetContainer.prepend(promptDiv);
        }

        // Attach event listeners directly (no cloneNode — avoids duplicate ID issue)
        const resumeBtn = document.getElementById("btn-do-resume");
        const newBtn = document.getElementById("btn-do-new");

        if (resumeBtn) {
            resumeBtn.onclick = () => {
                document.getElementById("gla-resume-prompt")?.remove();
                historyData.forEach(item => {
                    if (item.role === "user") {
                        appendUserMessage(item.content, item.timestamp);
                    } else if (item.role === "assistant" || item.role === "admin") {
                        appendBotMessage({
                            answer: item.content,
                            tier: item.tier || "ai_rag",
                            sender_role: item.role,
                            author: item.role === "admin" ? "Asesor de Admisiones Humano" : "Global Language Academy"
                        }, item.timestamp);
                    }
                });
                scrollToModalBottom();
            };
        }

        if (newBtn) {
            newBtn.onclick = () => {
                document.getElementById("gla-resume-prompt")?.remove();
                currentSessionId = "web_" + Math.random().toString(36).substring(2, 10);
                localStorage.setItem("gla_persistent_session_id", currentSessionId);
                if (socket && socket.readyState === WebSocket.OPEN) {
                    try {
                        socket.send(JSON.stringify({ action: "join", session_id: currentSessionId, role: "user" }));
                    } catch (e) {}
                }
            };
        }
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
                // Register session with backend
                try {
                    socket.send(JSON.stringify({ action: "join", session_id: currentSessionId, role: "user" }));
                } catch (e) {}
            };

            socket.onmessage = (event) => {
                hideTypingIndicator();
                try {
                    const data = JSON.parse(event.data);
                    if (data.session_id) {
                        currentSessionId = data.session_id;
                        localStorage.setItem("gla_persistent_session_id", currentSessionId);
                    }
                    if (data.tier !== "system" && data.event !== "user_message") {
                        appendBotMessage(data);
                        // If human agent responded, automatically open chat modal so student sees it immediately!
                        if (data.tier === "human_agent" || data.sender_role === "admin") {
                            window.openChatModal();
                        }
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
    loadHistory();

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
        // Fix: use localStorage (not sessionStorage) so the new session persists across reloads
        localStorage.setItem("gla_persistent_session_id", currentSessionId);

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

    function formatTime(ts) {
        // ts can be a unix epoch (float, from SQLite) or undefined (live message)
        const d = ts ? new Date(ts * 1000) : new Date();
        return d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
    }

    function appendUserMessage(text, timestamp) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "flex items-start justify-end space-x-2.5 user-message-wrapper";
        msgDiv.innerHTML = `
            <div>
                <div class="user-bubble text-white rounded-2xl rounded-tr-none px-4 py-2.5 max-w-[85%] text-xs sm:text-sm leading-relaxed shadow-lg">
                    ${escapeHtml(text)}
                </div>
                <div class="text-right text-[10px] text-slate-500 mt-0.5 pr-1">${formatTime(timestamp)}</div>
            </div>
            <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white flex-shrink-0 text-xs shadow border border-white/20">
                <i class="fa-solid fa-user text-[11px]"></i>
            </div>
        `;

        if (modalMessagesContainer) modalMessagesContainer.appendChild(msgDiv.cloneNode(true));
        if (standaloneContainer) standaloneContainer.appendChild(msgDiv);
        scrollToModalBottom();
    }

    function appendBotMessage(data, timestamp) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "flex items-start space-x-3 bot-message";

        const formattedAnswer = renderMarkdownSimple(data.answer);
        const isHumanAgent = data.tier === "human_agent" || data.sender_role === "admin";

        let ticketBadge = "";
        if (data.ticket_id) {
            ticketBadge = `
                <div class="mt-2.5 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between text-[11px] text-rose-300">
                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-ticket"></i> Ticket de Soporte:</span>
                    <strong class="font-mono bg-rose-500/20 px-2 py-0.5 rounded-md text-white border border-rose-400/30">${data.ticket_id}</strong>
                </div>
            `;
        }

        const avatarHtml = isHumanAgent
            ? `<div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white flex-shrink-0 text-xs shadow border border-emerald-400/40">
                   <i class="fa-solid fa-headset text-xs"></i>
               </div>`
            : `<div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white flex-shrink-0 text-xs shadow border border-white/20">
                   <i class="fa-solid fa-graduation-cap"></i>
               </div>`;

        const headerBadgeHtml = isHumanAgent
            ? `<div class="flex items-center justify-between gap-1.5 mb-1.5">
                   <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 uppercase tracking-wider">
                       <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse mr-1.5"></span> Asesor Humano en Vivo
                   </span>
                   <span class="text-[10px] text-emerald-400/80 font-mono">Respuesta Oficial</span>
               </div>`
            : `<div class="flex items-center justify-between gap-1.5 mb-1.5">
                   <span class="text-[11px] font-bold text-brand-300 tracking-wide uppercase">Global Language Academy</span>
                   <span class="text-[10px] text-slate-400 font-mono">En vivo</span>
               </div>`;

        const bubbleBorder = isHumanAgent ? "border-emerald-500/30 bg-emerald-950/20" : "";

        msgDiv.innerHTML = `
            ${avatarHtml}
            <div class="glass-bubble rounded-2xl rounded-tl-none p-4 text-slate-100 max-w-[85%] text-xs sm:text-sm leading-relaxed ${bubbleBorder}">
                ${headerBadgeHtml}
                <div class="prose prose-invert prose-xs sm:prose-sm max-w-none text-slate-200 leading-relaxed">
                    ${formattedAnswer}
                </div>
                ${ticketBadge}
                <div class="text-[10px] text-slate-500 mt-1.5">${formatTime(timestamp)}</div>
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
