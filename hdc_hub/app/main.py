import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import close_redis_client, get_redis_client
from app.routers import alertas, eventos, grafo, health, webhooks

# Configuração de Logs Estruturados
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("hdc.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de Vida do HUDSON DC:
    - Inicializa pool de conexões com o Redis no startup.
    - Encerra graciosamente as conexões no shutdown.
    """
    logger.info(f"🚀 Inicializando {settings.APP_NAME} v{settings.APP_VERSION} na porta {settings.PORT}...")
    try:
        r = await get_redis_client()
        await r.ping()
        logger.info("✅ Conexão com broker Redis estabelecida com sucesso.")
    except Exception as e:
        logger.warning(f"⚠️ Redis indisponível no startup ({e}). O HDC operará em modo fail-safe.")

    yield

    logger.info("🛑 Encerrando HUDSON DC e desalocando pools de conexões...")
    await close_redis_client()
    logger.info("✅ HUDSON DC finalizado com sucesso.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Orquestrador Central, Event Hub & Webhook Broker da Daisugi Tecnologias para a DAI Smart Reception, KAN-SA e DWs Soberanos.",
    lifespan=lifespan
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_and_latency_middleware(request: Request, call_next):
    """
    Mede a latência da requisição para garantir o cumprimento estrito do SLA da DAI (< 300ms).
    """
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000.0
    response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
    
    # Log de monitoramento
    logger.info(f"HTTP {request.method} {request.url.path} - Status: {response.status_code} - Latência: {duration_ms:.2f}ms")
    return response


# Inclusão dos Roteadores da API
app.include_router(health.router)
app.include_router(eventos.router)
app.include_router(webhooks.router)
app.include_router(alertas.router)
app.include_router(grafo.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Garante que qualquer erro não tratado devolva JSON seguro e auditado."""
    logger.error(f"Erro não tratado na rota {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "erro": "INTERNAL_SERVER_ERROR",
            "mensagem": "Falha interna no processamento do evento no HUDSON DC.",
            "detalhes": str(exc) if settings.DEBUG else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)
