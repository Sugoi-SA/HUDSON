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


# ==============================================================================
# 🛡️ 1. TESTE DE HARNESS RÍGIDO (Governança SoD & Travas do Cofre PAM)
# ==============================================================================
def test_harness_bloqueio_sod_maker_igual_checker():
    """
    [HARNESS RÍGIDO]:
    Se o engenheiro tentar aprovar a própria medição (Maker == Checker),
    o sistema DEVE travar com HTTP 422 e impedir o envio para o KAN-SA.
    """
    payload_violacao = {
        "evento": "DAI_QUARENTENA_SUBMETIDA",
        "hash_documento": "sha256_fake_teste_999",
        "status_parecer": "APROVADO",
        "maker": "engenheiro.obra@sugoisa.com.br",
        "checker": "engenheiro.obra@sugoisa.com.br", # VIOLAÇÃO: Maker == Checker
        "sod_validado": True,
        "metadados": {"tipo": "CCB"}
    }
    response = client.post("/api/v1/webhooks/quarentena-auditoria", json=payload_violacao, headers=HEADERS_VALIDOS)
    assert response.status_code == 422
    data = response.json()
    assert "Maker e Checker não podem ser o mesmo usuário" in data["detail"]


def test_harness_bloqueio_sod_invalido():
    """
    [HARNESS RÍGIDO]:
    Se sod_validado == False, o sistema DEVE rejeitar imediatamente com HTTP 422.
    """
    payload_sod_falso = {
        "evento": "DAI_QUARENTENA_SUBMETIDA",
        "hash_documento": "sha256_fake_teste_888",
        "status_parecer": "APROVADO",
        "maker": "engenheiro.obra@sugoisa.com.br",
        "checker": "controller@sugoisa.com.br",
        "sod_validado": False, # VIOLAÇÃO: SoD não certificado pelo Cofre PAM
        "metadados": {"tipo": "CCB"}
    }
    response = client.post("/api/v1/webhooks/quarentena-auditoria", json=payload_sod_falso, headers=HEADERS_VALIDOS)
    assert response.status_code == 422


# ==============================================================================
# 🎯 2. TESTE ANTI-ALUCINAÇÃO (Rigor Probatório Factual)
# ==============================================================================
def test_anti_alucinacao_entidade_desconhecida():
    """
    [ANTI-ALUCINAÇÃO]:
    Se uma pessoa ou CNPJ não existe na base factual do Grafo,
    o sistema NÃO PODE especular, inventar cargos ou inventar empresas.
    DEVE responder 'encontrado: False' e 'entidade: null'.
    """
    termo_fantasma = "Entidade_Inexistente_Fantasma_XYZ_999"
    response = client.get(f"/api/v1/grafo/consultar-entidade?termo={termo_fantasma}", headers=HEADERS_VALIDOS)
    assert response.status_code == 200
    data = response.json()
    assert data["encontrado"] is False
    assert data["entidade"] is None


# ==============================================================================
# 🌫️ 3. TESTE DE LÓGICA FUZZY (Matching Semântico e Tons de Cinza)
# ==============================================================================
def test_fuzzy_matching_variacoes_nome():
    """
    [LÓGICA FUZZY]:
    O visitante pode ser buscado por apenas o primeiro nome, sobrenome,
    ou variações em minúsculas/maiúsculas. O resolvedor deve correlacionar.
    """
    # Teste com variação 1: apenas primeiro nome em minúsculo
    resp1 = client.get("/api/v1/grafo/consultar-entidade?termo=ronaldo", headers=HEADERS_VALIDOS)
    assert resp1.status_code == 200
    assert resp1.json()["encontrado"] is True
    assert resp1.json()["entidade"]["nome"] == "Ronaldo Akagui"

    # Teste com variação 2: apenas sobrenome com espaços
    resp2 = client.get("/api/v1/grafo/consultar-entidade?termo=  AKAGUI  ", headers=HEADERS_VALIDOS)
    assert resp2.status_code == 200
    assert resp2.json()["encontrado"] is True
    assert resp2.json()["entidade"]["cargo"] == "Diretoria Executiva / Controller"


# ==============================================================================
# 📚 4. TESTE DE RAG (Recuperação Factual de Relações Corporativas)
# ==============================================================================
def test_rag_recuperacao_relacionamentos_soberanos():
    """
    [RAG PROBATÓRIO]:
    O sistema recupera os vínculos corporativos factuais persistidos no Grafo
    sem desvios ou alucinações.
    """
    response = client.get("/api/v1/grafo/consultar-entidade?termo=SUGOI", headers=HEADERS_VALIDOS)
    assert response.status_code == 200
    entidade = response.json()["entidade"]
    assert entidade["nome"] == "SUGOI CONSTRUTORA S.A."
    assert "Debêntures Opea / CRI" in entidade["relacionamentos_ativos"]
    assert "Empreendimentos Landbank" in entidade["relacionamentos_ativos"]


# ==============================================================================
# ⚡ 5. TESTE DE RAPIDFUZZ (Tolerância a Erro Tipográfico e Limiar de Confiança)
# ==============================================================================
def test_rapidfuzz_tolerancia_erros_digitacao():
    """
    [RAPIDFUZZ TOLERÂNCIA A TYPO]:
    Testa se o RapidFuzz reconhece mesmo com erro de grafia ("Akaguy" com 'y' ou "Tylor"),
    mas bloqueia tentativas de invasão ou nomes fora do limiar de 75%.
    """
    # 1. Erro de grafia leve ("Ronaldo Akaguy" com y) -> DEVE ENCONTRAR com score alto
    resp_typo = client.get("/api/v1/grafo/consultar-entidade?termo=Ronaldo Akaguy", headers=HEADERS_VALIDOS)
    assert resp_typo.status_code == 200
    assert resp_typo.json()["encontrado"] is True
    assert resp_typo.json()["entidade"]["nome"] == "Ronaldo Akagui"

    # 2. Busca por "Tylor" -> DEVE ENCONTRAR Dr. Tylor Code
    resp_tylor = client.get("/api/v1/grafo/consultar-entidade?termo=Tylor", headers=HEADERS_VALIDOS)
    assert resp_tylor.status_code == 200
    assert resp_tylor.json()["encontrado"] is True
    assert resp_tylor.json()["entidade"]["nome"] == "Dr. Tylor Code"

    # 3. Termo completamente alienígena -> HARNESS DEVE BARRAR (encontrado: False)
    resp_barrado = client.get("/api/v1/grafo/consultar-entidade?termo=Invasor Desconhecido Hacker", headers=HEADERS_VALIDOS)
    assert resp_barrado.status_code == 200
    assert resp_barrado.json()["encontrado"] is False
    assert resp_barrado.json()["entidade"] is None

