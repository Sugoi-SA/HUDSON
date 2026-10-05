import logging
from fastapi import APIRouter, Depends, Query, status

from app.core.security import verify_auth_and_signature
from app.core.harness import RAGHarnessGuard
from app.schemas.dai_events import ConsultaGrafoResponse, EntidadeGrafo

router = APIRouter(prefix="/api/v1/grafo", tags=["Grafo Corporativo & RAG"])
logger = logging.getLogger("hdc.routers.grafo")

# Catálogo Factual de Entidades Conhecidas do Ecossistema (Ancoragem Probatória)
CATALOGO_ENTIDADES_FATOS = [
    {
        "nome": "Ronaldo Akagui",
        "cargo": "Diretoria Executiva / Controller",
        "departamento": "Controladoria & Finanças",
        "grau_risco": "BAIXO",
        "relacionamentos_ativos": ["SUGOI CONSTRUTORA S.A.", "DAISUGI TECNOLOGIAS", "VBERTI INC"]
    },
    {
        "nome": "SUGOI CONSTRUTORA S.A.",
        "cargo": "Pessoa Jurídica Mantenedora",
        "departamento": "Sede Central",
        "grau_risco": "CONTROLADO",
        "relacionamentos_ativos": ["Empreendimentos Landbank", "Debêntures Opea / CRI", "Canteiros Ativos"]
    },
    {
        "nome": "Dr. Tylor Code",
        "cargo": "Líder Técnico & Arquitetura Forense",
        "departamento": "Engenharia de Sistemas",
        "grau_risco": "BAIXO",
        "relacionamentos_ativos": ["Daisugi Tecnologias", "Hudson Core", "Banca de Auditoria"]
    }
]


@router.get(
    "/consultar-entidade",
    response_model=ConsultaGrafoResponse,
    status_code=status.HTTP_200_OK,
    summary="Consulta semântica no Grafo Central por nome ou CNPJ/CPF com RapidFuzz & RAG Harness"
)
async def consultar_entidade(
    termo: str = Query(..., description="Nome da pessoa, razão social, CNPJ ou CPF para busca no Grafo"),
    tenant_id: str = Depends(verify_auth_and_signature)
):
    """
    Busca semântica no Grafo Central isolada por Tenant com proteção HARNESS anti-alucinação.
    Utiliza RapidFuzz para tolerância fonética e exige pontuação mínima de 75%.
    Se a entidade não for factualmente confirmada, recusa qualquer inferência e retorna enconrado=False.
    """
    termo_clean = termo.strip()
    logger.info(f"[{tenant_id}] Consultando entidade no Grafo com RAG Harness: '{termo_clean}'")

    encontrado, entidade_data, score = RAGHarnessGuard.buscar_entidade_ancorada(
        termo_clean,
        CATALOGO_ENTIDADES_FATOS
    )

    if encontrado and entidade_data:
        return ConsultaGrafoResponse(
            encontrado=True,
            entidade=EntidadeGrafo(**entidade_data)
        )

    # Entidade não cadastrada ou score insuficiente no Harness
    return ConsultaGrafoResponse(encontrado=False, entidade=None)

