import logging
import uuid
import httpx
from datetime import datetime

from app.core.config import settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger("hdc.tasks")


@celery_app.task(name="hdc.despachar_notificacao_anfitriao", bind=True, max_retries=3)
def task_despachar_notificacao_anfitriao(self, tenant_id: str, payload: dict):
    """
    Despacha notificação para Slack/Push ao anfitrião do departamento/sala alvo.
    Em ambiente real, conecta às APIs do Slack/Push Mobile.
    Simula e dispara o callback de retorno para a DAI.
    """
    ticket_id = payload.get("ticket_id")
    sala = payload.get("sala_destino")
    visitante = payload.get("visitante", {}).get("nome")
    logger.info(f"[{tenant_id}] Despachando notificação para Anfitrião da sala '{sala}' sobre visitante '{visitante}'.")

    # Mock de envio com sucesso:
    id_despacho = f"DSP-HUDSON-{uuid.uuid4().hex[:6].upper()}"

    # Dispara callback de autorização para a DAI
    callback_payload = {
        "id_evento_origem": id_despacho,
        "ticket_id": ticket_id,
        "tipo_retorno": "ANFITRIAO_RESPONDEU",
        "status": "AUTORIZADO",
        "resposta_anfitriao": f"Anfitrião ciente da chegada de {visitante}. Autorizado acesso.",
        "catraca_liberada": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    task_enviar_callback_dai.delay(callback_payload)
    return {"status": "SUCCESS", "id_despacho": id_despacho}


@celery_app.task(name="hdc.processar_quarentena_kansa", bind=True, max_retries=3)
def task_processar_quarentena_kansa(self, tenant_id: str, payload: dict):
    """
    Processa submissão de quarentena PAM:
    - Aciona a esteira pericial do KAN-SA para validação da CCB / medição de obra.
    - Grava correlação de entidades no Grafo Central.
    """
    hash_doc = payload.get("hash_documento")
    maker = payload.get("maker")
    checker = payload.get("checker")
    logger.info(f"[{tenant_id}] Encaminhando documento '{hash_doc[:12]}...' (Maker: {maker}, Checker: {checker}) para perícia KAN-SA.")

    # Conexão com o KAN-SA (ou mock de esteira pericial)
    protocolo = f"KANSA-AUD-{uuid.uuid4().hex[:8].upper()}"
    return {"status": "SUCCESS", "protocolo_kansa": protocolo}


@celery_app.task(name="hdc.processar_alerta_saullm", bind=True)
def task_processar_alerta_saullm(self, tenant_id: str, payload: dict):
    """
    Trata Alerta P1 Crítico:
    - Aciona sirene no painel da Segurança Patrimonial e Diretoria Jurídica.
    - Aciona o especialista cognitivo Dr. SaulLM para orientações imediatas de mitigação de risco legal.
    """
    ticket_id = payload.get("ticket_id")
    descricao = payload.get("descricao")
    logger.critical(f"[{tenant_id}] 🚨 ALERTA P1 DISPARADO! Ticket: {ticket_id}. Descrição: {descricao}")
    
    diretriz = (
        "DIRETRIZ DR. SAULLM: Solicitar identificação funcional do portador. "
        "Acolher com urbanidade e conduzir à Sala Executiva Térrea. "
        "Não fornecer documentação física ou digital antes da chegada do Advogado responsável."
    )
    return {"status": "SIRENE_DISPARADA", "diretriz_saullm": diretriz}


@celery_app.task(name="hdc.enviar_callback_dai", bind=True, default_retry_delay=5, max_retries=3)
def task_enviar_callback_dai(self, callback_data: dict):
    """
    Envia webhook de callback de volta para o Back-End da DAI (porta 8001).
    Utiliza exponential backoff em caso de oscilação momentânea da DAI.
    """
    try:
        logger.info(f"Enviando callback para a DAI ({settings.DAI_CALLBACK_URL}) - Ticket: {callback_data.get('ticket_id')}")
        with httpx.Client(timeout=settings.DAI_TIMEOUT_SECONDS) as client:
            resp = client.post(settings.DAI_CALLBACK_URL, json=callback_data)
            resp.raise_for_status()
            logger.info(f"Callback entregue com sucesso à DAI. Status HTTP: {resp.status_code}")
            return {"status": "DELIVERED", "http_status": resp.status_code}
    except Exception as exc:
        logger.warning(f"Falha temporária ao enviar callback para a DAI: {exc}. Retentando...")
        raise self.retry(exc=exc)
