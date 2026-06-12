import redis
import logging
from datetime import datetime
from fastapi import HTTPException
import os

logger = logging.getLogger(__name__)

MONTHLY_BUDGET_USD = 10.0
PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.warning(f"Could not connect to Redis: {e}")
    r = None

def check_budget(user_id: str, estimated_cost: float = 0.001) -> None:
    """
    Return True nếu còn budget, False nếu vượt.
    
    Logic:
    - Mỗi user có budget $10/tháng
    - Track spending trong Redis
    - Reset đầu tháng
    """
    if not r:
        logger.warning("Redis is not available, skipping budget check")
        return

    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"

    try:
        current = float(r.get(key) or 0)
        if current + estimated_cost > MONTHLY_BUDGET_USD:
            raise HTTPException(status_code=402, detail="Monthly budget exceeded")

        r.incrbyfloat(key, estimated_cost)
        # TTL 33 days to ensure it deletes early next month
        r.expire(key, 33 * 24 * 3600)
    except redis.RedisError as e:
        logger.error(f"Redis error during budget check: {e}")
