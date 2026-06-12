import time
import redis
import logging
from datetime import datetime
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

# Redis setup
_redis = None
if settings.redis_url:
    try:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
        _redis.ping()
    except Exception:
        _redis = None

# Fallback in-memory
_daily_cost = 0.0
_cost_reset_day = time.strftime("%Y-%m-%d")

def check_and_record_cost(input_tokens: int, output_tokens: int):
    global _daily_cost, _cost_reset_day
    
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
    
    if _redis:
        try:
            today = time.strftime("%Y-%m-%d")
            key = f"cost_guard:daily:{today}"
            
            # Check current cost
            current = float(_redis.get(key) or 0.0)
            if current >= settings.daily_budget_usd:
                raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
            
            # Record cost
            _redis.incrbyfloat(key, cost)
            _redis.expire(key, 2 * 24 * 3600)  # 2 days TTL
            return
        except redis.RedisError as e:
            logger.error(f"Redis error in cost guard: {e}")
            # fallback to memory
            pass

    # In-memory fallback
    today = time.strftime("%Y-%m-%d")
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today
        
    if _daily_cost >= settings.daily_budget_usd:
        raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
        
    _daily_cost += cost

def get_daily_cost() -> float:
    if _redis:
        try:
            today = time.strftime("%Y-%m-%d")
            key = f"cost_guard:daily:{today}"
            return float(_redis.get(key) or 0.0)
        except redis.RedisError:
            pass
    return _daily_cost
