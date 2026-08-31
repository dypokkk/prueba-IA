document.addEventListener("DOMContentLoaded", () => {
    const refreshBtn = document.getElementById("refresh-metrics-btn");
    const clearCacheBtn = document.getElementById("clear-cache-btn");

    const elTotalQueries = document.getElementById("metric-total-queries");
    const elCacheRate = document.getElementById("metric-cache-rate");
    const elTotalCost = document.getElementById("metric-total-cost");
    const elTotalTokens = document.getElementById("metric-total-tokens");
    const elEscalationRate = document.getElementById("metric-escalation-rate");

    // 1. Document Tab Switcher
    const docTabs = document.querySelectorAll(".doc-tab-btn");
    const docPanels = document.querySelectorAll(".doc-content-panel");

    docTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const targetId = tab.getAttribute("data-target");

            // Update Tab active styling
            docTabs.forEach((t) => {
                t.classList.remove("bg-brand-600", "text-white", "shadow");
                t.classList.add("bg-slate-700/70", "text-slate-300");
            });
            tab.classList.remove("bg-slate-700/70", "text-slate-300");
            tab.classList.add("bg-brand-600", "text-white", "shadow");

            // Show selected panel
            docPanels.forEach((panel) => {
                if (panel.id === targetId) {
                    panel.classList.remove("hidden");
                } else {
                    panel.classList.add("hidden");
                }
            });
        });
    });

    // 2. Fetch and Update Metrics
    function fetchMetrics() {
        fetch("/api/metrics")
            .then((res) => res.json())
            .then((data) => {
                if (elTotalQueries) elTotalQueries.textContent = data.total_queries;
                if (elCacheRate) elCacheRate.textContent = `${data.cache_hit_rate_pct}%`;
                if (elTotalCost) elTotalCost.textContent = `$${data.total_cost_usd}`;
                if (elTotalTokens) elTotalTokens.textContent = data.total_tokens;
                if (elEscalationRate) elEscalationRate.textContent = `${data.escalation_rate_pct}%`;
            })
            .catch((err) => console.error("Error updating metrics:", err));
    }

    // 3. Button Listeners
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            fetchMetrics();
            refreshBtn.classList.add("animate-spin");
            setTimeout(() => refreshBtn.classList.remove("animate-spin"), 500);
        });
    }

    if (clearCacheBtn) {
        clearCacheBtn.addEventListener("click", () => {
            if (confirm("Are you sure you want to flush all in-memory cache entries?")) {
                fetch("/api/cache/clear", { method: "POST" })
                    .then((res) => res.json())
                    .then((data) => {
                        alert("Cache successfully flushed!");
                        fetchMetrics();
                    })
                    .catch((err) => console.error("Error clearing cache:", err));
            }
        });
    }

    // Auto-refresh metrics every 5 seconds
    setInterval(fetchMetrics, 5000);
});
