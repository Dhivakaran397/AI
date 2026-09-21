import redis.asyncio as aioredis
from app.config import settings

redis_client: aioredis.Redis | None = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


async def get_redis() -> aioredis.Redis:
    """Dependency for injecting Redis client."""
    if redis_client is None:
        await init_redis()
    return redis_client  # type: ignore
