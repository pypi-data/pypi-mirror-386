import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple


class RateLimiter:
    def __init__(self, max_calls: int, per_seconds: float):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self.calls: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)

    def allow(self, session_id: str, intent: str) -> bool:
        key = (session_id, intent)
        now = time.time()
        q = self.calls[key]
        while q and now - q[0] > self.per_seconds:
            q.popleft()
        if len(q) < self.max_calls:
            q.append(now)
            return True
        return False
