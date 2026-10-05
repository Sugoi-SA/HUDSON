import logging
from fastapi import APIRouter, Depends, Query, status

from app.core.security import verify_auth_and_signature
from app.schemas.dai_events import ConsultaGrafoResponse, EntidadeGrafo

router = APIRouter(prefix="/api/v1/grafo", tags=["Grafo Corporativo & RAG"])
logger = logging.getLogger("hdc.routers.grafo")


@router.get(
    "/consultar-entidade",
    response_model=ConsultaGrafoResponse,
    status_code=status.HTTP_200_OK,
    summary="Consulta semântica no Grafo Central por nome ou CNPJ/CPF"
)
async def consultar_entidade(
    termo: str = Query(..., description="Nome da pessoa, razão social, CNPJ ou CPF para busca no Grafo"),
    tenant_id: str = Depends(verify_auth_and_signature)
):
    """
    Busca semântica no Grafo Central isolada por Tenant (respeitando segregação de dados).
    Identifica relacionamentos ativos, cargo corporativo e grau de risco preliminar.
    """
    termo_clean = termo.strip()
    logger.info(f"[{tenant_id}] Consultando entidade no Grafo: '{termo_clean}'")

    # Mock pericial representativo (conectável ao Neo4j / ChromaDB):
    if "ronaldo" in termo_clean.lower() or "akagui" in termo_clean.lower():
        return ConsultaGrafoResponse(
            encontrado=True,
            entidade=EntidadeGrafo(
                nome="Ronaldo Akagui",
                cargo="Diretoria Executiva / Controller",
                departamento="Controladoria & Finanças",
                grau_risco="BAIXO",
                relacionamentos_ativos=["SUGOI CONSTRUTORA S.A.", "DAISUGI TECNOLOGIAS", "VBERTI INC"]
            )
        )
    elif "sugoi" in termo_clean.lower():
        return ConsultaGrafoResponse(
            encontrado=True,
            entidade=EntidadeGrafo(
                nome="SUGOI CONSTRUTORA S.A.",
                cargo="Pessoa Jurídica Mantenedora",
                departamento="Sede Central",
                grau_risco="CONTROLADO",
                relacionamentos_ativos=["Empreendimentos Landbank", "Debêntures Opea / CRI", "Canteiros Ativos"]
            )
        )

    # Entidade não cadastrada previamente no Grafo
    return ConsultaGrafoResponse(encontrado=False, entidade=None)
