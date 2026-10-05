import uuid
import logging
from fastapi import APIRouter, Depends, status

from app.core.security import verify_auth_and_signature
from app.schemas.dai_events import QuarentenaAuditoriaRequest, QuarentenaAuditoriaResponse
from app.tasks.dispatchers import task_processar_quarentena_kansa

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks Quarentena & PAM"])
logger = logging.getLogger("hdc.routers.webhooks")


@router.post(
    "/quarentena-auditoria",
    response_model=QuarentenaAuditoriaResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Recebe submissão de quarentena de CCB/Medição e despacha para a esteira KAN-SA"
)
async def quarentena_auditoria(
    payload: QuarentenaAuditoriaRequest,
    tenant_id: str = Depends(verify_auth_and_signature)
):
    """
    Recebe documento em quarentena validado pela esteira PAM da DAI (Maker-Checker).
    Encaminha para a fila pericial do KAN-SA e correlaciona no Grafo Central.
    """
    # 1. Validação Estrita de Governança PAM (SoD - Segregação de Funções)
    if payload.maker.strip().lower() == payload.checker.strip().lower() or not payload.sod_validado:
        logger.critical(
            f"[{tenant_id}] VIOLAÇÃO DE GOVERNANÇA PAM DETECTADA! "
            f"Maker ({payload.maker}) idêntico ao Checker ou SoD não validado. Rejeitando com HTTP 422."
        )
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Violação de Governança PAM (SoD): Maker e Checker não podem ser o mesmo usuário."
        )

    logger.info(f"[{tenant_id}] Documento {payload.hash_documento[:12]}... recebido em quarentena. SoD Validado: {payload.sod_validado}")

    protocolo = f"KANSA-AUD-{uuid.uuid4().hex[:8].upper()}"
    task_processar_quarentena_kansa.delay(tenant_id, payload.model_dump(mode="json"))

    return QuarentenaAuditoriaResponse(
        status="ACCEPTED",
        protocolo_auditoria=protocolo,
        esteira_acionada="esteira_pericial_automatica_kansa",
        mensagem="Documento aceito sob quarentena. Ordem de perícia despachada com sucesso."
    )
