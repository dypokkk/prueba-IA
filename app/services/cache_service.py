import time
import re
from typing import Optional, Dict, Any
from app.config import settings

class CacheService:
    """
    In-memory LRU / TTL Query Cache.
    Returns sub-millisecond responses for repeated inquiries at $0.00 API cost.
    """

    def __init__(self, ttl_seconds: int = None, max_size: int = None):
        self.ttl = ttl_seconds or settings.CACHE_TTL_SECONDS
        self.max_size = max_size or settings.MAX_CACHE_SIZE
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _normalize_key(self, query: str) -> str:
        """Normalizes user query to increase cache hit probability."""
        normalized = query.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached response if valid and not expired."""
        key = self._normalize_key(query)
        if key in self.cache:
            entry = self.cache[key]
            # Check TTL
            if time.time() - entry["created_at"] < self.ttl:
                entry["last_accessed"] = time.time()
                entry["hits"] = entry.get("hits", 0) + 1
                return entry["data"]
            else:
                # Expired
                del self.cache[key]
        return None

    def set(self, query: str, data: Dict[str, Any]):
        """Stores query response in cache. Evicts oldest if exceeding max_size."""
        # Never cache human escalation responses
        if data.get("escalate_to_human", False):
            return

        key = self._normalize_key(query)
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Evict oldest by last_accessed
            oldest_key = min(self.cache, key=lambda k: self.cache[k].get("last_accessed", 0))
            del self.cache[oldest_key]

        self.cache[key] = {
            "data": data,
            "created_at": time.time(),
            "last_accessed": time.time(),
            "hits": 0
        }

    def clear(self):
        """Clears all cached entries."""
        self.cache.clear()

    def size(self) -> int:
        """Returns active number of cached entries."""
        return len(self.cache)

cache_service = CacheService()
