import threading
from typing import Dict, Any

class MetricsService:
    """
    Real-Time Operational Metrics Tracker.
    Calculates query volume, cache hit ratios, token usage, estimated costs ($ USD), and escalation rates.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.total_queries = 0
        self.deterministic_matches = 0
        self.ai_completions = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.escalated_queries = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_latency_ms = 0.0

        # Cost rates ($ per 1 Million tokens) - Default for Gemini 3.5 Flash Lite
        self.PRICE_PER_M_INPUT = 0.075
        self.PRICE_PER_M_OUTPUT = 0.300

    def record_query(
        self,
        tier: str,
        is_cache_hit: bool,
        is_escalated: bool,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0
    ):
        with self._lock:
            self.total_queries += 1
            self.total_latency_ms += latency_ms

            if is_cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1

            if tier == "deterministic":
                self.deterministic_matches += 1
            elif tier in ("ai_rag", "escalation"):
                self.ai_completions += 1

            if prompt_tokens > 0 or completion_tokens > 0:
                self.total_prompt_tokens += prompt_tokens
                self.total_completion_tokens += completion_tokens

            if is_escalated:
                self.escalated_queries += 1

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = max(self.total_queries, 1)
            cache_hit_rate = (self.cache_hits / total) * 100 if self.total_queries > 0 else 0.0
            escalation_rate = (self.escalated_queries / total) * 100 if self.total_queries > 0 else 0.0
            avg_latency = (self.total_latency_ms / total) if self.total_queries > 0 else 0.0

            # Calculate actual incurred cost
            cost_input = (self.total_prompt_tokens / 1_000_000) * self.PRICE_PER_M_INPUT
            cost_output = (self.total_completion_tokens / 1_000_000) * self.PRICE_PER_M_OUTPUT
            total_cost_usd = cost_input + cost_output

            # Calculate savings from cache and deterministic tier
            saved_queries = self.cache_hits + self.deterministic_matches
            # Approximate 500 prompt tokens + 150 completion tokens saved per intercepted query
            est_saved_tokens_input = saved_queries * 500
            est_saved_tokens_output = saved_queries * 150
            savings_usd = (
                (est_saved_tokens_input / 1_000_000) * self.PRICE_PER_M_INPUT +
                (est_saved_tokens_output / 1_000_000) * self.PRICE_PER_M_OUTPUT
            )

            total_tokens = self.total_prompt_tokens + self.total_completion_tokens

            return {
                "total_queries": self.total_queries,
                "deterministic_matches": self.deterministic_matches,
                "ai_completions": self.ai_completions,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate_pct": round(cache_hit_rate, 1),
                "escalations": self.escalated_queries,
                "escalated_queries": self.escalated_queries,
                "escalation_rate_pct": round(escalation_rate, 1),
                "total_prompt_tokens": self.total_prompt_tokens,
                "total_completion_tokens": self.total_completion_tokens,
                "total_tokens": total_tokens,
                "total_cost_usd": f"{total_cost_usd:.6f}",
                "estimated_savings_usd": f"{savings_usd:.4f}",
                "average_latency_ms": round(avg_latency, 1)
            }

metrics_service = MetricsService()
