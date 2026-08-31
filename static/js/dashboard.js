// Global Tab Switcher Function
window.switchDocTab = function(docName) {
    const tabBtns = document.querySelectorAll(".doc-tab-btn");
    const contentPanes = document.querySelectorAll(".doc-content-pane");

    tabBtns.forEach((btn) => {
        btn.classList.remove("bg-gradient-to-r", "from-brand-600", "to-indigo-600", "text-white", "shadow-md", "shadow-brand-600/30", "border-white/20");
        btn.classList.add("text-slate-400", "hover:text-slate-200", "hover:bg-white/5", "border-transparent");
    });

    contentPanes.forEach((pane) => {
        pane.classList.add("hidden");
    });

    const activeBtn = document.getElementById(`tab-btn-${docName}`);
    if (activeBtn) {
        activeBtn.classList.remove("text-slate-400", "hover:text-slate-200", "hover:bg-white/5", "border-transparent");
        activeBtn.classList.add("bg-gradient-to-r", "from-brand-600", "to-indigo-600", "text-white", "shadow-md", "shadow-brand-600/30", "border-white/20");
    }

    const activePane = document.getElementById(`doc-content-${docName}`);
    if (activePane) {
        activePane.classList.remove("hidden");
    }
};

document.addEventListener("DOMContentLoaded", () => {
    const refreshBtn = document.getElementById("refresh-metrics-btn");
    const clearCacheBtn = document.getElementById("clear-cache-btn");

    const elTotalQueries = document.getElementById("metric-total-queries");
    const elDeterministicMatches = document.getElementById("metric-deterministic-matches");
    const elAiCompletions = document.getElementById("metric-ai-completions");
    const elCacheRate = document.getElementById("metric-cache-rate");
    const elCacheHits = document.getElementById("metric-cache-hits");
    const elEstimatedSavings = document.getElementById("metric-estimated-savings");
    const elTotalCost = document.getElementById("metric-total-cost");
    const elTotalTokens = document.getElementById("metric-total-tokens");
    const elEscalationRate = document.getElementById("metric-escalation-rate");
    const elEscalationsCount = document.getElementById("metric-escalations-count");

    function fetchMetrics() {
        fetch("/api/metrics")
            .then((res) => res.json())
            .then((data) => {
                if (elTotalQueries) elTotalQueries.textContent = data.total_queries ?? 0;
                if (elDeterministicMatches) elDeterministicMatches.textContent = data.deterministic_matches ?? 0;
                if (elAiCompletions) elAiCompletions.textContent = data.ai_completions ?? 0;
                if (elCacheRate) elCacheRate.textContent = `${data.cache_hit_rate_pct ?? 0}%`;
                if (elCacheHits) elCacheHits.textContent = data.cache_hits ?? 0;
                if (elEstimatedSavings) elEstimatedSavings.textContent = data.estimated_savings_usd ?? "0.0000";
                if (elTotalCost) elTotalCost.textContent = `$${data.total_cost_usd ?? "0.000000"}`;
                if (elTotalTokens) elTotalTokens.textContent = data.total_tokens ?? 0;
                if (elEscalationRate) elEscalationRate.textContent = `${data.escalation_rate_pct ?? 0}%`;
                if (elEscalationsCount) elEscalationsCount.textContent = data.escalations ?? data.escalated_queries ?? 0;
            })
            .catch((err) => console.error("[Dashboard] Error updating metrics:", err));
    }

    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            fetchMetrics();
            const icon = refreshBtn.querySelector("i");
            if (icon) icon.classList.add("fa-spin");
            setTimeout(() => {
                if (icon) icon.classList.remove("fa-spin");
            }, 600);
        });
    }

    if (clearCacheBtn) {
        clearCacheBtn.addEventListener("click", () => {
            if (confirm("¿Estás seguro de que deseas vaciar todas las respuestas en caché?")) {
                fetch("/api/cache/clear", { method: "POST" })
                    .then((res) => res.json())
                    .then((data) => {
                        fetchMetrics();
                    })
                    .catch((err) => console.error("Error clearing cache:", err));
            }
        });
    }

    // Auto-refresh metrics every 4 seconds
    setInterval(fetchMetrics, 4000);
});
