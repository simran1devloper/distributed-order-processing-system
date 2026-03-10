from redis import asyncio as aioredis

async def is_duplicate(redis: aioredis.Redis, key: str, expiry=3600) -> bool:
    """Returns True if the request was already processed."""
    # SET NX (Set if Not Exists)
    result = await redis.set(f"idempotency:{key}", "processing", ex=expiry, nx=True)
    return result is None