"""In-process rate limiting.

A fixed window counter per key. The deployment runs a single uvicorn worker, so
process local counters are enough to stop password guessing and signup floods;
with several workers each process gets its own budget, which is acceptable until
a shared counter (redis) is worth its operational cost.
"""

import time


class RateLimiter:
    def __init__(self, *, limit: int, window: int):
        self._limit = limit
        self._window = window
        self._hits: dict[str, tuple[float, int]] = {}

    def hit(self, key: str) -> int | None:
        """Register one attempt.

        Returns the number of seconds to wait when the budget is exhausted, and
        ``None`` while the caller is still allowed in.
        """
        now = time.monotonic()
        window_start, count = self._hits.get(key, (now, 0))

        if now - window_start >= self._window:
            window_start, count = now, 0

        count += 1
        self._hits[key] = (window_start, count)

        if len(self._hits) > 10_000:
            self._prune(now)

        if count > self._limit:
            return int(self._window - (now - window_start)) + 1
        return None

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)

    def _prune(self, now: float) -> None:
        expired = [
            key for key, (window_start, _) in self._hits.items() if now - window_start >= self._window
        ]
        for key in expired:
            del self._hits[key]


#: Failed sign-ins per client: 10 attempts a minute is far above what a human
#: needs and far below what guessing a password requires.
login_limiter = RateLimiter(limit=10, window=60)

#: Signups per client: accounts are cheap for an attacker to create, expensive
#: for the database.
signup_limiter = RateLimiter(limit=5, window=3600)

#: Refreshes per client: the frontend refreshes once per expired token.
refresh_limiter = RateLimiter(limit=30, window=60)