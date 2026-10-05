import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)

HEADERS_AUTENTICADOS = {
    "Authorization": f"Bearer {settings.HUDSON_TOKEN_JWT}",
    "X-Daisugi-Tenant-ID": "sugoi_sa"
}


# ==============================================================================
# 🔄 CIRCUITO COMPLETO: PAM ➔ DAI ➔ HDC ➔ KAN-SA ➔ HDW ➔ CALLBACK DAI
# ==============================================================================

@patch("app.tasks.dispatchers.task_processar_quarentena_kansa.delay")
def test_circuito_quarentena_pam_valido(mock_kansa):
    """
    Simula o fluxo completo com governança PAM:
    - Maker: engenheiro da obra
    - Checker: controller geral
    - SoD: validado pelo Cofre PAM-IGA
    - Resultado: HDC aceita com 202 e aciona esteira pericial.
    """
    payload_circuito = {
        "evento": "DAI_QUARENTENA_SUBMETIDA",
        "hash_documento": "sha256_ccb_medicao_obra_1234567890abcdef",
        "status_parecer": "APROVADO",
        "maker": "engenheiro.canteiro@sugoisa.com.br",
        "checker": "controller.geral@sugoisa.com.br",
        "sod_validado": True,
        "metadados": {
            "obra_wbs": "OBRA-023",
            "tipo_documento": "CCB_MEDICAO_CANTEIRO",
            "valor_declarado": 350000.00
        },
        "destino_kansa": "esteira_pericial_automatica"
    }

    response = client.post(
        "/api/v1/webhooks/quarentena-auditoria",
        json=payload_circuito,
        headers=HEADERS_AUTENTICADOS
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "ACCEPTED"
    assert data["protocolo_auditoria"].startswith("KANSA-AUD-")
    mock_kansa.assert_called_once()


def test_circuito_quarentena_violacao_sod():
    """
    Simula tentativa de fraude de alçada:
    - O engenheiro tenta aprovar a própria medição de obra.
    - O HDC barra com HTTP 422 antes de gastar recursos.
    """
    payload_fraude = {
        "evento": "DAI_QUARENTENA_SUBMETIDA",
        "hash_documento": "sha256_fraude_auto_aprovacao_999",
        "status_parecer": "APROVADO",
        "maker": "engenheiro@sugoisa.com.br",
        "checker": "engenheiro@sugoisa.com.br", # VIOLAÇÃO SoD!
        "sod_validado": True,
        "metadados": {"tipo": "CCB"}
    }

    response = client.post(
        "/api/v1/webhooks/quarentena-auditoria",
        json=payload_fraude,
        headers=HEADERS_AUTENTICADOS
    )

    assert response.status_code == 422
    assert "Maker e Checker não podem ser o mesmo usuário" in response.json()["detail"]


@patch("httpx.Client.post")
def test_callback_de_retorno_para_dai(mock_post):
    """
    Valida o envio do webhook de retorno do HDC para a DAI:
    - Garante que o payload carrega ticket_id, status e autorização de catraca.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    from app.tasks.dispatchers import task_enviar_callback_dai

    callback_payload = {
        "id_evento_origem": "DSP-HUDSON-TEST99",
        "ticket_id": "TKT-DAI-2026-70FE7F",
        "tipo_retorno": "ANFITRIAO_RESPONDEU",
        "status": "AUTORIZADO",
        "resposta_anfitriao": "Estou descendo para recepcionar.",
        "catraca_liberada": True
    }

    resultado = task_enviar_callback_dai(callback_payload)
    assert resultado["status"] == "DELIVERED"
    assert resultado["http_status"] == 200
    mock_post.assert_called_once()
