import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)

HEADERS_VALIDOS = {
    "Authorization": f"Bearer {settings.HUDSON_TOKEN_JWT}",
    "X-Daisugi-Tenant-ID": "sugoi_sa"
}


def test_health_check():
    """Valida se o health check responde 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["port"] == 9000


def test_notificar_anfitriao_sem_token():
    """Garante rejeição 401 quando o token Bearer não é enviado."""
    payload = {
        "evento": "DAI_NOTIFICAR_ANFITRIAO",
        "ticket_id": "TKT-TEST-001",
        "sala_destino": "Governança",
        "departamento": "Auditoria",
        "visitante": {"nome": "Teste"},
        "anfitriao_alvo": {"mensagem": "Olá"}
    }
    response = client.post("/api/v1/eventos/notificar-anfitriao", json=payload)
    assert response.status_code == 401


def test_notificar_anfitriao_token_invalido():
    """Garante rejeição 403 quando o token Bearer é forjado."""
    headers = {"Authorization": "Bearer token_falso_hacker"}
    payload = {
        "evento": "DAI_NOTIFICAR_ANFITRIAO",
        "ticket_id": "TKT-TEST-002",
        "sala_destino": "Governança",
        "departamento": "Auditoria",
        "visitante": {"nome": "Teste"},
        "anfitriao_alvo": {"mensagem": "Olá"}
    }
    response = client.post("/api/v1/eventos/notificar-anfitriao", json=payload, headers=headers)
    assert response.status_code == 403


@patch("app.routers.eventos.check_idempotency_or_lock", new_callable=AsyncMock)
@patch("app.tasks.dispatchers.task_despachar_notificacao_anfitriao.delay")
def test_notificar_anfitriao_sucesso(mock_task, mock_idemp):
    """Valida aceitação em < 300ms com retorno HTTP 202."""
    mock_idemp.return_value = True
    payload = {
        "evento": "DAI_NOTIFICAR_ANFITRIAO",
        "ticket_id": "TKT-DAI-2026-TEST",
        "sala_destino": "Governança de Travas ERP",
        "departamento": "Controladoria & Auditoria",
        "visitante": {
            "id_usuario": 4,
            "nome": "Controller Geral",
            "perfil_pam": "admin"
        },
        "anfitriao_alvo": {
            "canal_preferencial": "slack_and_push",
            "mensagem": "Visitante aguarda liberação."
        }
    }
    response = client.post("/api/v1/eventos/notificar-anfitriao", json=payload, headers=HEADERS_VALIDOS)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "ACCEPTED"
    assert data["id_despacho"].startswith("DSP-HUDSON-")
    mock_task.assert_called_once()


def test_alerta_emergencia_p1():
    """Valida acionamento de emergência com diretriz do Dr. SaulLM."""
    payload = {
        "evento": "ALERTA_EMERGENCIA_P1",
        "nivel_prioridade": "P1_CRITICO",
        "ticket_id": "TKT-EMERG-001",
        "descricao": "Mandado judicial no térreo",
        "localizacao": "Lobby",
        "acao_imediata": "Acolhimento em sala executiva"
    }
    response = client.post("/api/v1/alertas/emergencia", json=payload, headers=HEADERS_VALIDOS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SIRENE_DISPARADA"
    assert "DIRETRIZ IMEDIATA DR. SAULLM" in data["diretriz_saullm"]


def test_consultar_grafo_entidade():
    """Valida busca semântica de entidade no Grafo."""
    response = client.get("/api/v1/grafo/consultar-entidade?termo=Ronaldo+Akagui", headers=HEADERS_VALIDOS)
    assert response.status_code == 200
    data = response.json()
    assert data["encontrado"] is True
    assert data["entidade"]["nome"] == "Ronaldo Akagui"
    assert "SUGOI CONSTRUTORA S.A." in data["entidade"]["relacionamentos_ativos"]
