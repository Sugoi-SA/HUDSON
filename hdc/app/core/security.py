import hashlib
import hmac
import logging
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Header, HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger("hdc.security")

# Pool assíncrono do Redis para Idempotência e Bloqueios Distribuídos
redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Retorna a instância singleton do cliente assíncrono Redis."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=2.0
        )
    return redis_client


async def close_redis_client():
    """Fecha as conexões do pool Redis no shutdown do serviço."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def verify_auth_and_signature(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_daisugi_signature: Optional[str] = Header(None, alias="X-Daisugi-Signature"),
    x_daisugi_tenant_id: Optional[str] = Header(None, alias="X-Daisugi-Tenant-ID"),
) -> str:
    """
    Middleware de Segurança Rígida:
    1. Valida o Token Bearer JWT.
    2. Valida a assinatura HMAC SHA-256 contra o segredo compartilhado (Anti-Tampering).
    3. Normaliza e extrai o Tenant ID (ex: sugoi_sa).
    """
    # 1. Validação do Token Bearer
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Tentativa de acesso não autorizada: Header Authorization ausente ou inválido.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization Bearer obrigatório."
        )
    
    token = authorization.split("Bearer ")[1].strip()
    if token != settings.HUDSON_TOKEN_JWT:
        logger.warning("Token Bearer rejeitado no HUDSON DC.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token Bearer inválido ou não autorizado."
        )

    # 2. Validação da Assinatura HMAC (se o header estiver presente)
    if x_daisugi_signature:
        body_bytes = await request.body()
        expected_prefix = "sha256="
        received_hash = x_daisugi_signature
        if received_hash.startswith(expected_prefix):
            received_hash = received_hash[len(expected_prefix):]

        computed_hmac = hmac.new(
            settings.HUDSON_WEBHOOK_SECRET.encode("utf-8"),
            msg=body_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(received_hash, computed_hmac):
            logger.error("Assinatura HMAC SHA-256 inválida! Possível tentativa de adulteração de payload.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assinatura HMAC SHA-256 incompatível."
            )

    # 3. Definição do Tenant ID
    tenant_id = x_daisugi_tenant_id or settings.DEFAULT_TENANT_ID
    return tenant_id


async def check_idempotency_or_lock(ticket_id: str, tenant_id: str, ttl_seconds: int = 600) -> bool:
    """
    Garante a Idempotência no Redis:
    Registra atômico: 'idemp:{tenant_id}:{ticket_id}'
    Retorna True se é um evento NOVO.
    Retorna False se o evento já foi processado ou está em andamento (descarte de duplicata).
    """
    try:
        r = await get_redis_client()
        lock_key = f"hdc:idemp:{tenant_id}:{ticket_id}"
        # SET ... NX EX (Set if Not eXists, com expiração em segundos)
        is_new = await r.set(lock_key, "PROCESSING", nx=True, ex=ttl_seconds)
        return bool(is_new)
    except Exception as e:
        logger.error(f"Erro ao conectar com Redis para idempotência: {e}. Prosseguindo em modo fail-safe.")
        # Em caso de falha de conexão do Redis, não bloqueia o fluxo crítico (Fail-Open controlado com log)
        return True
