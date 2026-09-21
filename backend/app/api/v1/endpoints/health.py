import time
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter()


@router.get("/healthz")
async def health():
    return {"status": "ok"}


@router.get("/healthz/deep")
async def deep_health(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    components: dict[str, dict] = {}
    overall_status = "healthy"

    # 1. Database check
    db_start = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        db_duration_ms = round((time.perf_counter() - db_start) * 1000, 2)
        components["database"] = {
            "status": "up",
            "latency_ms": db_duration_ms,
        }
    except Exception as e:
        overall_status = "degraded"
        components["database"] = {
            "status": "down",
            "error": str(e),
        }

    # 2. Redis check
    redis_start = time.perf_counter()
    try:
        await redis.ping()
        redis_duration_ms = round((time.perf_counter() - redis_start) * 1000, 2)
        components["redis"] = {
            "status": "up",
            "latency_ms": redis_duration_ms,
        }
    except Exception as e:
        overall_status = "degraded"
        components["redis"] = {
            "status": "down",
            "error": str(e),
        }

    status_code = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "components": components,
            "timestamp": time.time(),
        },
    )
