import logging
import httpx
from app.core.config import settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger("hdc.hdw_bridge")

# Mapeamento dinâmico de Tenants para seus respectivos endpoints HDW
TENANT_HDW_REGISTRY = {
    "sugoi_sa": {
        "url": "http://vmsever.sugoisa.com.br:8000",
        "api_key": "sugoi_master_hudson_dw_key_2026",
        "nome": "SUGOI CONSTRUTORA S.A."
    }
}


@celery_app.task(name="hdc.sincronizar_hdw_local", bind=True, max_retries=3)
def task_sincronizar_hdw_local(self, tenant_id: str, hash_documento: str, status_auditoria: str, metadata: dict):
    """
    Sincronização Federada HDC ➔ HDW:
    Notifica o Data Warehouse Soberano do Cliente sobre o parecer de quarentena emitido.
    Permite que o HDW registre o evento pericial no 'custody_log' local do acervo.
    """
    tenant_info = TENANT_HDW_REGISTRY.get(tenant_id)
    if not tenant_info:
        logger.warning(f"Tenant '{tenant_id}' não possui HDW registrado no catálogo. Sincronização pulada.")
        return {"status": "SKIPPED", "reason": "tenant_not_registered"}

    hdw_url = tenant_info["url"]
    api_key = tenant_info["api_key"]
    logger.info(f"[{tenant_id}] Sincronizando evento pericial do hash {hash_documento[:12]}... com HDW ({hdw_url})")

    payload_hdw = {
        "hash_sha256": hash_documento,
        "evento": "PARECER_QUARENTENA_KANSA",
        "status": status_auditoria,
        "metadados": metadata
    }

    try:
        # Chamada segura para o HDW local com API Key
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        # Timeout curto para não prender o worker caso a VPN esteja em oscilação
        with httpx.Client(timeout=3.0) as client:
            resp = client.post(f"{hdw_url}/api/v1/sync/parecer", json=payload_hdw, headers=headers)
            if resp.status_code in [200, 201, 202]:
                logger.info(f"[{tenant_id}] HDW local sincronizado com sucesso.")
                return {"status": "SYNCED", "http_status": resp.status_code}
            else:
                logger.warning(f"[{tenant_id}] HDW retornou status inesperado: {resp.status_code}")
                return {"status": "WARNING", "http_status": resp.status_code}
    except Exception as exc:
        logger.warning(f"[{tenant_id}] Falha ao contactar HDW local ({hdw_url}): {exc}. Registrando na fila de retry...")
        raise self.retry(exc=exc, countdown=10)
