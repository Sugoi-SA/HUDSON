import uuid
import logging
from fastapi import APIRouter, Depends, status

from app.core.security import verify_auth_and_signature
from app.schemas.dai_events import AlertaEmergenciaRequest, AlertaEmergenciaResponse
from app.tasks.dispatchers import task_processar_alerta_saullm

router = APIRouter(prefix="/api/v1/alertas", tags=["Alertas de Emergência P1"])
logger = logging.getLogger("hdc.routers.alertas")


@router.post(
    "/emergencia",
    response_model=AlertaEmergenciaResponse,
    status_code=status.HTTP_200_OK,
    summary="Aciona sirene P1 e diretriz preliminar do Dr. SaulLM para fiscalizações/mandados"
)
async def alerta_emergencia(
    payload: AlertaEmergenciaRequest,
    tenant_id: str = Depends(verify_auth_and_signature)
):
    """
    Gatilho de Crise no Lobby / Balcão da DAI:
    Aciona sirene no painel da Segurança Patrimonial e Diretoria Jurídica.
    Retorna orientação imediata formulada pelo Dr. SaulLM para a recepcionista/totem.
    """
    logger.critical(f"[{tenant_id}] 🚨 ACIONAMENTO DE EMERGÊNCIA P1: {payload.descricao} (Ticket: {payload.ticket_id})")

    alerta_id = f"ALR-P1-{uuid.uuid4().hex[:6].upper()}"
    task_processar_alerta_saullm.delay(tenant_id, payload.model_dump(mode="json"))

    diretriz_saullm = (
        "DIRETRIZ IMEDIATA DR. SAULLM: Identificar educadamente os agentes públicos. "
        "Acolher com discrição na Sala Executiva Térrea. "
        "Avisar imediatamente a Diretoria Jurídica e o Controller. Não franquear acesso a sistemas sem a presença do Advogado."
    )

    return AlertaEmergenciaResponse(
        status="SIRENE_DISPARADA",
        alerta_id=alerta_id,
        autoridades_acionadas=["diretoria_juridica", "seguranca_patrimonial", "controladoria"],
        diretriz_saullm=diretriz_saullm
    )
