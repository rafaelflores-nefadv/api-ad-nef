import time
from dataclasses import dataclass
from threading import Lock
from typing import Dict

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings


@dataclass
class Bucket:
    tokens: float
    last: float


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._store: Dict[str, Bucket] = {}
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        refill_rate = settings.rate_limit_per_minute / 60.0
        burst = settings.rate_limit_burst
        with self._lock:
            bucket = self._store.get(key)
            if bucket is None:
                bucket = Bucket(tokens=burst, last=now)
                self._store[key] = bucket
            elapsed = now - bucket.last
            bucket.tokens = min(burst, bucket.tokens + elapsed * refill_rate)
            bucket.last = now
            if bucket.tokens >= 1:
                bucket.tokens -= 1
                return True
            return False


limiter = InMemoryRateLimiter()


def rate_limit_dependency(request: Request) -> None:
    client_key = request.client.host if request.client else "unknown"
    path_key = request.url.path
    key = f"{client_key}:{path_key}"
    if not limiter.allow(key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit excedido")


def RateLimit() -> None:
    return Depends(rate_limit_dependency)
