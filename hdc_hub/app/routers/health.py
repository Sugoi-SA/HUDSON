from fastapi import APIRouter
from app.core.config import settings
from app.core.security import get_redis_client

router = APIRouter(tags=["Health & Status"])


@router.get("/health", summary="Health check e telemetria do HUDSON DC")
async def health_check():
    """
    Verifica a saúde do serviço HDC e a conectividade com o broker Redis.
    """
    redis_status = "connected"
    try:
        r = await get_redis_client()
        pong = await r.ping()
        if not pong:
            redis_status = "degraded"
    except Exception:
        redis_status = "offline"

    return {
        "status": "healthy" if redis_status == "connected" else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "port": settings.PORT,
        "broker_redis": redis_status
    }
