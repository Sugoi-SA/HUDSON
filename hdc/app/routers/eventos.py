import uuid
import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.security import check_idempotency_or_lock, verify_auth_and_signature
from app.schemas.dai_events import NotificarAnfitriaoRequest, NotificarAnfitriaoResponse
from app.tasks.dispatchers import task_despachar_notificacao_anfitriao

router = APIRouter(prefix="/api/v1/eventos", tags=["Eventos Portaria DAI"])
logger = logging.getLogger("hdc.routers.eventos")


@router.post(
    "/notificar-anfitriao",
    response_model=NotificarAnfitriaoResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Notifica o anfitrião sobre a chegada de visitante na portaria (Tab 2 DAI)"
)
async def notificar_anfitriao(
    payload: NotificarAnfitriaoRequest,
    tenant_id: str = Depends(verify_auth_and_signature)
):
    """
    Recebe notificação da DAI em < 200ms.
    Valida Idempotência no Redis para descartar duplicatas no intervalo de 10 min.
    Enfileira a entrega de mensagem nos canais preferenciais do anfitrião via Celery.
    """
    logger.info(f"[{tenant_id}] Recebido pedido de notificação para ticket: {payload.ticket_id}")

    # 1. Checagem de Idempotência Atômica no Redis
    is_new = await check_idempotency_or_lock(payload.ticket_id, tenant_id)
    if not is_new:
        logger.warning(f"[{tenant_id}] Evento duplicado detectado para ticket {payload.ticket_id}. Retornando aceitação prévia.")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ALREADY_ACCEPTED",
                "id_despacho": f"DSP-IDEMP-{payload.ticket_id}",
                "canais_acionados": ["ja_enfileirado"],
                "tempo_estimado_entrega": "< 1s"
            }
        )

    # 2. Despejo Assíncrono na Fila Celery
    id_despacho = f"DSP-HUDSON-{uuid.uuid4().hex[:6].upper()}"
    task_despachar_notificacao_anfitriao.delay(tenant_id, payload.model_dump(mode="json"))

    # 3. Resposta Imediata para Liberar a Portaria da DAI
    return NotificarAnfitriaoResponse(
        status="ACCEPTED",
        id_despacho=id_despacho,
        canais_acionados=["slack", "push_mobile"],
        tempo_estimado_entrega="< 2s"
    )
