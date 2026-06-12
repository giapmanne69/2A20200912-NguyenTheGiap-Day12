import time
import redis
from fastapi import HTTPException
from app.config import settings
from collections import defaultdict, deque

# Redis setup
_redis = None
if settings.redis_url:
    try:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
        _redis.ping()
    except Exception:
        _redis = None

# Fallback in-memory limiter
_rate_windows: dict[str, deque] = defaultdict(deque)

def check_rate_limit(key: str):
    if _redis:
        try:
            # Redis-based sliding window rate limiter
            now = time.time()
            redis_key = f"rate_limit:{key}"
            pipe = _redis.pipeline()
            # Remove keys older than 60s
            pipe.zremrangebyscore(redis_key, 0, now - 60)
            # Count remaining
            pipe.zcard(redis_key)
            # Add current timestamp
            pipe.zadd(redis_key, {str(now): now})
            # Set TTL on key
            pipe.expire(redis_key, 60)
            _, count, _, _ = pipe.execute()
            
            if count >= settings.rate_limit_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                    headers={"Retry-After": "60"},
                )
            return
        except redis.RedisError:
            # Fallback to memory on Redis error
            pass

    # In-memory fallback
    now = time.time()
    window = _rate_windows[key]
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
    window.append(now)
