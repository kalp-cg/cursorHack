"""
Simple in-memory sliding-window rate limiter for expensive / public endpoints.
Not a substitute for Redis at multi-instance scale — sufficient for single-node deploy.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque

from fastapi import HTTPException, Request

_lock = Lock()
_buckets: dict[str, Deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def rate_limit(request: Request, *, limit: int, window_sec: int, bucket: str) -> None:
    """Raise 429 if more than `limit` hits in `window_sec` for this IP+bucket."""
    key = f"{bucket}:{_client_ip(request)}"
    now = time.monotonic()
    with _lock:
        q = _buckets[key]
        while q and now - q[0] > window_sec:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded ({limit}/{window_sec}s). Try again shortly.",
            )
        q.append(now)
