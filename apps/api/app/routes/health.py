import time
from fastapi import APIRouter, status
from redis import asyncio as aioredis

from apps.api.app.config import settings
from apps.api.app.database import check_db_connectivity
from apps.api.app.schemas.health import HealthResponse, ComponentHealth

router = APIRouter(tags=["Health"])


async def check_redis_connectivity() -> ComponentHealth:
    """Check Redis connectivity with a 1.0s timeout."""
    start_time = time.perf_counter()
    try:
        client = aioredis.from_url(
            settings.REDIS_URL,
            socket_timeout=1.0,
            socket_connect_timeout=1.0
        )
        await client.ping()
        await client.aclose()
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return ComponentHealth(
            status="connected",
            latency_ms=latency_ms,
            details={"url": settings.REDIS_URL.split("@")[-1]}  # omit password if any
        )
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return ComponentHealth(
            status="disconnected",
            latency_ms=latency_ms,
            details={"error": str(e), "url": settings.REDIS_URL.split("@")[-1]}
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Returns connectivity status and latency metrics for core infrastructure (Database, Redis)."
)
@router.get(
    "/api/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def get_health():
    # 1. Check Database
    db_res = await check_db_connectivity()
    db_health = ComponentHealth(
        status=db_res["status"],
        latency_ms=db_res.get("latency_ms"),
        details={
            "dialect": db_res.get("dialect"),
            "postgis_enabled": db_res.get("postgis_enabled", False),
            **({"error": db_res["error"]} if "error" in db_res else {})
        }
    )

    # 2. Check Redis
    redis_health = await check_redis_connectivity()

    # Determine overall status:
    # Database is critical; Redis is non-fatal for MVP dev
    overall_status = "healthy"
    if db_health.status != "connected":
        overall_status = "unhealthy"
    elif redis_health.status != "connected":
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database=db_health,
        redis=redis_health
    )
