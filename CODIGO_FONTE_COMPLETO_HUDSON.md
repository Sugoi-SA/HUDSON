# Sindicância — Código-fonte completo

Gerado em 2026-09-08 13:01 a partir do estado atual do projeto.

## Índice

- [.env.example](#-env-example)
- [Makefile](#makefile)
- [backend/.dockerignore](#backend-dockerignore)
- [backend/.env.example](#backend-env-example)
- [backend/.flake8](#backend-flake8)
- [backend/Dockerfile](#backend-dockerfile)
- [backend/alembic.ini](#backend-alembic-ini)
- [backend/app/__init__.py](#backend-app-__init__-py)
- [backend/app/casos/__init__.py](#backend-app-casos-__init__-py)
- [backend/app/casos/router.py](#backend-app-casos-router-py)
- [backend/app/casos/schemas.py](#backend-app-casos-schemas-py)
- [backend/app/casos/servico.py](#backend-app-casos-servico-py)
- [backend/app/celery_app.py](#backend-app-celery_app-py)
- [backend/app/core/__init__.py](#backend-app-core-__init__-py)
- [backend/app/core/config.py](#backend-app-core-config-py)
- [backend/app/core/database.py](#backend-app-core-database-py)
- [backend/app/fuzzy/__init__.py](#backend-app-fuzzy-__init__-py)
- [backend/app/fuzzy/engine.py](#backend-app-fuzzy-engine-py)
- [backend/app/fuzzy/rules.py](#backend-app-fuzzy-rules-py)
- [backend/app/fuzzy/variables.py](#backend-app-fuzzy-variables-py)
- [backend/app/grafo/__init__.py](#backend-app-grafo-__init__-py)
- [backend/app/grafo/driver.py](#backend-app-grafo-driver-py)
- [backend/app/grafo/excecoes.py](#backend-app-grafo-excecoes-py)
- [backend/app/grafo/labels.py](#backend-app-grafo-labels-py)
- [backend/app/grafo/repositorio.py](#backend-app-grafo-repositorio-py)
- [backend/app/grafo/router.py](#backend-app-grafo-router-py)
- [backend/app/grafo/schemas.py](#backend-app-grafo-schemas-py)
- [backend/app/ingestao/__init__.py](#backend-app-ingestao-__init__-py)
- [backend/app/ingestao/chroma_client.py](#backend-app-ingestao-chroma_client-py)
- [backend/app/ingestao/extratores.py](#backend-app-ingestao-extratores-py)
- [backend/app/ingestao/router.py](#backend-app-ingestao-router-py)
- [backend/app/ingestao/schemas.py](#backend-app-ingestao-schemas-py)
- [backend/app/ingestao/servico.py](#backend-app-ingestao-servico-py)
- [backend/app/main.py](#backend-app-main-py)
- [backend/app/models/__init__.py](#backend-app-models-__init__-py)
- [backend/app/models/audit_log.py](#backend-app-models-audit_log-py)
- [backend/app/models/base.py](#backend-app-models-base-py)
- [backend/app/models/caso.py](#backend-app-models-caso-py)
- [backend/app/models/diligencia.py](#backend-app-models-diligencia-py)
- [backend/app/models/documento.py](#backend-app-models-documento-py)
- [backend/app/models/entidade.py](#backend-app-models-entidade-py)
- [backend/app/models/nucleo_investigativo.py](#backend-app-models-nucleo_investigativo-py)
- [backend/app/models/relacao.py](#backend-app-models-relacao-py)
- [backend/migrations/env.py](#backend-migrations-env-py)
- [backend/migrations/script.py.mako](#backend-migrations-script-py-mako)
- [backend/migrations/versions/0001_schema_inicial.py](#backend-migrations-versions-0001_schema_inicial-py)
- [backend/pytest.ini](#backend-pytest-ini)
- [backend/requirements.txt](#backend-requirements-txt)
- [backend/tests/test_fuzzy_engine.py](#backend-tests-test_fuzzy_engine-py)
- [docker-compose.yml](#docker-compose-yml)
- [frontend/.dockerignore](#frontend-dockerignore)
- [frontend/.gitignore](#frontend-gitignore)
- [frontend/Dockerfile](#frontend-dockerfile)
- [frontend/index.html](#frontend-index-html)
- [frontend/nginx.conf](#frontend-nginx-conf)
- [frontend/package.json](#frontend-package-json)
- [frontend/postcss.config.js](#frontend-postcss-config-js)
- [frontend/src/App.jsx](#frontend-src-app-jsx)
- [frontend/src/api/client.js](#frontend-src-api-client-js)
- [frontend/src/components/GrafoEntidades.jsx](#frontend-src-components-grafoentidades-jsx)
- [frontend/src/components/ListaCasos.jsx](#frontend-src-components-listacasos-jsx)
- [frontend/src/components/PainelEntidade.jsx](#frontend-src-components-painelentidade-jsx)
- [frontend/src/index.css](#frontend-src-index-css)
- [frontend/src/main.jsx](#frontend-src-main-jsx)
- [frontend/src/pages/PaginaPrincipal.jsx](#frontend-src-pages-paginaprincipal-jsx)
- [frontend/src/utils/fuzzy.js](#frontend-src-utils-fuzzy-js)
- [frontend/tailwind.config.js](#frontend-tailwind-config-js)
- [frontend/vite.config.js](#frontend-vite-config-js)

## .env.example

```bash
# Copie este arquivo para .env e ajuste as senhas antes de subir o stack.

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=app
POSTGRES_PORT=5432

# Neo4j
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpassword
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687

# Redis
REDIS_PASSWORD=redispassword
REDIS_PORT=6379

# ChromaDB
CHROMA_PORT=8000

# Backend (FastAPI)
BACKEND_PORT=8000
APP_NAME=Sindicancia API
DEBUG=false
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:80

# Frontend (nginx servindo o build do Vite)
FRONTEND_PORT=80

```

## Makefile

```makefile
.PHONY: help build up down logs migrate test lint reset

# `make` sem argumentos mostra a ajuda.
.DEFAULT_GOAL := help

help: ## Lista todos os alvos disponíveis
	@echo "Alvos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

build: ## Builda as imagens Docker de todos os serviços
	docker compose build

up: ## Sobe todos os serviços em background
	docker compose up -d

down: ## Para e remove os containers (mantém os volumes/dados)
	docker compose down

logs: ## Segue os logs de todos os serviços
	docker compose logs -f

migrate: ## Roda as migrations do Alembic no backend (upgrade head)
	docker compose exec backend alembic upgrade head

test: ## Roda a suíte de testes (pytest) no backend
	docker compose exec backend pytest

lint: ## Roda o flake8 no código do backend
	docker compose exec backend flake8 app

reset: ## Para tudo e REMOVE os volumes — apaga todos os dados persistidos
	docker compose down -v

```

## backend/.dockerignore

```text
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
.env
storage/
.git

```

## backend/.env.example

```bash
# Copie este arquivo para .env e ajuste os valores.
# Deve refletir as credenciais definidas no docker-compose.yml (raiz do projeto).

DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/app

APP_NAME=Sindicancia API
DEBUG=true

# Origens permitidas para CORS, separadas por vírgula
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Módulo de ingestão documental (backend/app/ingestao/)
STORAGE_DIR=./storage/documentos
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Módulo de grafo de entidades (backend/app/grafo/)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpassword

```

## backend/.flake8

```ini
[flake8]
max-line-length = 110
# E203/W503: conflitam com o estilo de formatação usado no projeto
# (espaço antes de ":" em slices, quebra de linha antes de operador binário).
extend-ignore = E203, W503
exclude = .venv,venv,__pycache__,migrations/versions,storage

```

## backend/Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

# Dependências de sistema:
#   - tesseract-ocr (+ idioma pt): OCR de imagens em app/ingestao/extratores.py
#   - libpq5: cliente PostgreSQL (psycopg2-binary já embute o essencial, mas
#     libpq5 garante compatibilidade em algumas variações do slim)
#   - curl: usado pelo HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-por \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala as dependências Python antes de copiar o código da aplicação,
# para reaproveitar o cache de camadas do Docker quando só o código muda.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuário não-root
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

```

## backend/alembic.ini

```ini
[alembic]
script_location = migrations
prepend_sys_path = .

# A URL de conexão NÃO fica aqui — migrations/env.py a lê de
# app.core.config.get_settings().database_url (mesma fonte de verdade do
# resto da aplicação: variável de ambiente DATABASE_URL / .env).
sqlalchemy.url =

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S

```

## backend/app/__init__.py

```python

```

## backend/app/casos/__init__.py

```python
"""Módulo de casos: listagem paginada e criação (CRUD mínimo sobre `casos`)."""
from app.casos.router import router

__all__ = ["router"]

```

## backend/app/casos/router.py

```python
"""Endpoints HTTP do módulo de casos."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.casos.schemas import CasoCreate, CasoListResponse, CasoResponse
from app.casos.servico import criar_caso, listar_casos
from app.core.database import get_db

router = APIRouter(prefix="/api/casos", tags=["casos"])


@router.get("", response_model=CasoListResponse, summary="Lista casos, com paginação")
def obter_casos(
    limit: int = Query(50, ge=1, le=200, description="Tamanho da página."),
    offset: int = Query(0, ge=0, description="Quantos registros pular."),
    db: Session = Depends(get_db),
) -> CasoListResponse:
    itens, total = listar_casos(db, limit=limit, offset=offset)
    return CasoListResponse(
        casos=[CasoResponse.model_validate(item) for item in itens],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=CasoResponse, status_code=201, summary="Cria um novo caso")
def criar_novo_caso(dados: CasoCreate, db: Session = Depends(get_db)) -> CasoResponse:
    caso = criar_caso(db, dados)
    return CasoResponse.model_validate(caso)

```

## backend/app/casos/schemas.py

```python
"""Schemas Pydantic do módulo de casos."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CasoBase(BaseModel):
    tema: str
    subcategoria: str | None = None
    objeto_central: str | None = None
    problema_enunciado: str | None = None
    status: str = "aberto"


class CasoCreate(CasoBase):
    """Corpo de POST /api/casos."""


class CasoResponse(CasoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    criado_em: datetime
    atualizado_em: datetime


class CasoListResponse(BaseModel):
    """Resposta de GET /api/casos: uma página de casos + metadados de paginação."""

    casos: list[CasoResponse]
    total: int = Field(description="Número total de casos no banco (não só nesta página).")
    limit: int
    offset: int

```

## backend/app/casos/servico.py

```python
"""Regras de negócio do módulo de casos (CRUD mínimo sobre a tabela `casos`)."""
from sqlalchemy.orm import Session

from app.casos.schemas import CasoCreate
from app.models.caso import Caso


def listar_casos(db: Session, limit: int, offset: int) -> tuple[list[Caso], int]:
    """Lista casos paginados, do mais recente para o mais antigo.

    Returns:
        Tupla (itens da página, total de casos no banco).
    """
    total = db.query(Caso).count()
    itens = (
        db.query(Caso)
        # Desempate por id: sem ele, casos com o mesmo `criado_em` (comum em
        # cargas em lote) poderiam mudar de ordem entre páginas.
        .order_by(Caso.criado_em.desc(), Caso.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return itens, total


def criar_caso(db: Session, dados: CasoCreate) -> Caso:
    caso = Caso(**dados.model_dump())
    db.add(caso)
    db.commit()
    db.refresh(caso)
    return caso

```

## backend/app/celery_app.py

```python
"""App Celery para tarefas assíncronas em background.

Ainda não há tarefas "reais" registradas — este módulo é o ponto de partida
para mover trabalho pesado (ex.: extração de texto/OCR e indexação no
ChromaDB do módulo app/ingestao/, ou processamento em lote no grafo/motor
fuzzy) para fora do ciclo de requisição/resposta do FastAPI.

Rodar o worker localmente (a partir de backend/):
    celery -A app.celery_app worker --loglevel=info

No docker-compose, isso roda no serviço opcional `celery_worker`.
"""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sindicancia",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
)


@celery_app.task(name="app.celery_app.ping")
def ping() -> str:
    """Tarefa de exemplo, só para verificar se o worker está de pé."""
    return "pong"

```

## backend/app/core/__init__.py

```python

```

## backend/app/core/config.py

```python
"""Configurações da aplicação, carregadas de variáveis de ambiente / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Sindicancia API"
    debug: bool = False

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/app"

    cors_origins: str = "http://localhost:3000"

    # Módulo de ingestão documental (app/ingestao/)
    storage_dir: str = "./storage/documentos"
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # Módulo de grafo de entidades (app/grafo/)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4jpassword"

    # Celery (app/celery_app.py) — worker de tarefas assíncronas em background
    celery_broker_url: str = "redis://:redispassword@localhost:6379/0"
    celery_result_backend_url: str = "redis://:redispassword@localhost:6379/1"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

```

## backend/app/core/database.py

```python
"""Engine, sessão e dependência de banco de dados (PostgreSQL via SQLAlchemy)."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Dependência do FastAPI: abre uma sessão por requisição e garante o fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

```

## backend/app/fuzzy/__init__.py

```python
"""Motor de inferência fuzzy Mamdani (scikit-fuzzy) do Grau de Certeza.

Uso:
    from app.fuzzy import inferir

    grau_certeza, status = inferir(
        confiabilidade=0.9,  # Confiabilidade da Fonte
        forca=0.85,          # Força da Conexão
        cobertura=0.8,       # Cobertura Probatória
    )
"""
from app.fuzzy.engine import ResultadoFuzzy, calcular_grau_certeza, inferir
from app.fuzzy.rules import REGRAS, RegraFuzzy
from app.fuzzy.variables import NIVEIS, PESOS_SAIDA

__all__ = [
    "inferir",
    "calcular_grau_certeza",
    "ResultadoFuzzy",
    "REGRAS",
    "RegraFuzzy",
    "PESOS_SAIDA",
    "NIVEIS",
]

```

## backend/app/fuzzy/engine.py

```python
"""Motor de inferência fuzzy Mamdani do Grau de Certeza.

Entradas (0.0 a 1.0):
    - confiabilidade: Confiabilidade da Fonte
    - forca:          Força da Conexão
    - cobertura:      Cobertura Probatória

Pipeline:
    1. Fuzzificação: cada entrada é convertida em graus de pertinência nos
       5 níveis linguísticos (Muito Baixa..Muito Alta) via skfuzzy.
    2. Inferência: as 5 regras Mamdani (app.fuzzy.rules.REGRAS) são avaliadas
       com o operador E = mínimo entre os 3 antecedentes.
    3. Desfuzzificação por média ponderada (GCV):

           GCV = Σ(pertinência_i × peso_i) / Σ(peso_i)

       onde pertinência_i é a força de disparo da regra i e peso_i é o valor
       representativo do termo de saída dessa regra.
    4. Classificação do GCV em um status linguístico final.

Caso nenhuma das 5 regras dispare de forma significativa — ou seja, os 3
critérios estão em níveis muito diferentes entre si e não descrevem nenhum
dos 5 padrões "diagonais" — o caso é classificado como "Lacuna": não há
evidência suficiente/coerente para posicionar o Grau de Certeza.
"""
from dataclasses import dataclass

from app.fuzzy.rules import REGRAS
from app.fuzzy.variables import cobertura_probatoria, confiabilidade_fonte, forca_conexao

# Abaixo deste limiar de soma das forças de disparo, nenhuma regra descreve
# adequadamente a combinação de entradas.
LIMIAR_DISPARO_MINIMO = 1e-6

STATUS_LACUNA = "Lacuna"

# Limiares de corte do GCV para os status que correspondem a uma das 5 regras.
# Avaliados em ordem, do maior para o menor.
FAIXAS_STATUS: tuple[tuple[float, str], ...] = (
    (0.85, "Confirmado"),
    (0.65, "Indício Forte"),
    (0.45, "Indício Moderado"),
    (0.25, "Inferência"),
    (0.00, "Descartado"),
)


@dataclass(frozen=True)
class ResultadoFuzzy:
    """Resultado completo da inferência, útil para auditoria (audit_log)."""

    grau_certeza: float
    status: str
    regra_dominante: int | None
    disparos: dict[int, float]


def _classificar_por_gcv(gcv: float) -> str:
    for limiar, status in FAIXAS_STATUS:
        if gcv >= limiar:
            return status
    return "Descartado"  # guarda de segurança; sempre coberto pelo limiar 0.00


def calcular_grau_certeza(confiabilidade: float, forca: float, cobertura: float) -> ResultadoFuzzy:
    """Executa a inferência fuzzy completa e retorna o resultado detalhado.

    Args:
        confiabilidade: Confiabilidade da Fonte, 0.0 a 1.0.
        forca: Força da Conexão, 0.0 a 1.0.
        cobertura: Cobertura Probatória, 0.0 a 1.0.

    Returns:
        ResultadoFuzzy com o grau de certeza (0.0-1.0), o status linguístico,
        a regra de maior disparo e o disparo de cada uma das 5 regras.
    """
    mu_confiabilidade = confiabilidade_fonte.fuzzificar(confiabilidade)
    mu_forca = forca_conexao.fuzzificar(forca)
    mu_cobertura = cobertura_probatoria.fuzzificar(cobertura)

    disparos = {regra.numero: regra.forca_disparo(mu_confiabilidade, mu_forca, mu_cobertura) for regra in REGRAS}

    soma_pesos = sum(disparos.values())

    if soma_pesos < LIMIAR_DISPARO_MINIMO:
        return ResultadoFuzzy(grau_certeza=0.0, status=STATUS_LACUNA, regra_dominante=None, disparos=disparos)

    # Desfuzzificação: GCV = Σ(pertinência × peso) / Σ(peso)
    gcv = sum(disparos[regra.numero] * regra.peso for regra in REGRAS) / soma_pesos
    gcv = round(gcv, 2)

    regra_dominante = max(disparos, key=disparos.get)
    status = _classificar_por_gcv(gcv)

    return ResultadoFuzzy(grau_certeza=gcv, status=status, regra_dominante=regra_dominante, disparos=disparos)


def inferir(confiabilidade: float, forca: float, cobertura: float) -> tuple[float, str]:
    """API simplificada: recebe os 3 critérios e retorna (grau_certeza, status).

    Args:
        confiabilidade: Confiabilidade da Fonte, 0.0 a 1.0.
        forca: Força da Conexão, 0.0 a 1.0.
        cobertura: Cobertura Probatória, 0.0 a 1.0.

    Returns:
        Tupla (grau_certeza: float entre 0.0 e 1.0, status: str), onde status
        é um de: "Confirmado", "Indício Forte", "Indício Moderado",
        "Inferência", "Lacuna", "Descartado".
    """
    resultado = calcular_grau_certeza(confiabilidade, forca, cobertura)
    return resultado.grau_certeza, resultado.status

```

## backend/app/fuzzy/rules.py

```python
"""As 5 regras de inferência Mamdani do motor fuzzy.

Cada regra é "diagonal": exige que as 3 entradas estejam no MESMO nível
linguístico, combinadas pelo operador E (t-norma mínimo — Mamdani clássico),
e aponta para um termo de saída com peso associado (ver
`app.fuzzy.variables.PESOS_SAIDA`), usado na desfuzzificação GCV.
"""
from dataclasses import dataclass

from app.fuzzy.variables import PESOS_SAIDA


@dataclass(frozen=True)
class RegraFuzzy:
    numero: int
    nivel_antecedente: str  # nível comum das 3 entradas, ex.: "muito_alta"
    termo_consequente: str  # termo de saída, ex.: "confirmado"
    descricao: str

    @property
    def peso(self) -> float:
        return PESOS_SAIDA[self.termo_consequente]

    def forca_disparo(
        self,
        mu_confiabilidade: dict[str, float],
        mu_forca: dict[str, float],
        mu_cobertura: dict[str, float],
    ) -> float:
        """Grau de disparo da regra: mínimo (E lógico) das pertinências dos
        3 antecedentes no nível desta regra."""
        return min(
            mu_confiabilidade[self.nivel_antecedente],
            mu_forca[self.nivel_antecedente],
            mu_cobertura[self.nivel_antecedente],
        )


REGRAS: tuple[RegraFuzzy, ...] = (
    RegraFuzzy(
        numero=1,
        nivel_antecedente="muito_alta",
        termo_consequente="confirmado",
        descricao=(
            "SE Confiabilidade da Fonte é Muito Alta E Força da Conexão é Muito Alta "
            "E Cobertura Probatória é Muito Alta ENTÃO Grau de Certeza é Confirmado."
        ),
    ),
    RegraFuzzy(
        numero=2,
        nivel_antecedente="alta",
        termo_consequente="indicio_forte",
        descricao=(
            "SE Confiabilidade da Fonte é Alta E Força da Conexão é Alta "
            "E Cobertura Probatória é Alta ENTÃO Grau de Certeza é Indício Forte."
        ),
    ),
    RegraFuzzy(
        numero=3,
        nivel_antecedente="media",
        termo_consequente="indicio_moderado",
        descricao=(
            "SE Confiabilidade da Fonte é Média E Força da Conexão é Média "
            "E Cobertura Probatória é Média ENTÃO Grau de Certeza é Indício Moderado."
        ),
    ),
    RegraFuzzy(
        numero=4,
        nivel_antecedente="baixa",
        termo_consequente="inferencia",
        descricao=(
            "SE Confiabilidade da Fonte é Baixa E Força da Conexão é Baixa "
            "E Cobertura Probatória é Baixa ENTÃO Grau de Certeza é Inferência."
        ),
    ),
    RegraFuzzy(
        numero=5,
        nivel_antecedente="muito_baixa",
        termo_consequente="descartado",
        descricao=(
            "SE Confiabilidade da Fonte é Muito Baixa E Força da Conexão é Muito Baixa "
            "E Cobertura Probatória é Muito Baixa ENTÃO Grau de Certeza é Descartado."
        ),
    ),
)

```

## backend/app/fuzzy/variables.py

```python
"""Variáveis linguísticas do motor de inferência fuzzy.

Universo de discurso: todas as variáveis (3 de entrada + 1 de saída) vivem
em [0.0, 1.0], o mesmo domínio já usado pelos campos fuzzy do schema
PostgreSQL (`entidades.nivel_certeza_fuzzy`, `documentos.confiabilidade_fonte`,
`relacoes.grau_pertinencia_fuzzy`, `diligencias.grau_fuzzy_resultante`).

Cada variável tem 5 níveis (conjuntos fuzzy) linguísticos:
    Muito Baixa, Baixa, Média, Alta, Muito Alta

As entradas usam funções de pertinência trapezoidais nos extremos ("ombros")
e triangulares no meio, uniformemente espaçadas e com sobreposição — o
desenho clássico para variáveis fuzzy de propósito geral.
"""
from dataclasses import dataclass, field

import numpy as np
import skfuzzy as fuzz

# Universo de discurso comum: 0.00 a 1.00 em passos de 0.01
UNIVERSO = np.linspace(0.0, 1.0, 101)

NIVEIS: tuple[str, ...] = ("muito_baixa", "baixa", "media", "alta", "muito_alta")


@dataclass
class VariavelLinguistica:
    """Variável fuzzy com 5 níveis (Muito Baixa..Muito Alta) sobre [0, 1]."""

    nome: str
    universo: np.ndarray = field(default_factory=lambda: UNIVERSO)

    def __post_init__(self) -> None:
        u = self.universo
        self.muito_baixa = fuzz.trapmf(u, [0.00, 0.00, 0.05, 0.25])
        self.baixa = fuzz.trimf(u, [0.05, 0.25, 0.45])
        self.media = fuzz.trimf(u, [0.30, 0.50, 0.70])
        self.alta = fuzz.trimf(u, [0.55, 0.75, 0.95])
        self.muito_alta = fuzz.trapmf(u, [0.75, 0.95, 1.00, 1.00])

    def funcao_pertinencia(self, nivel: str) -> np.ndarray:
        return getattr(self, nivel)

    def fuzzificar(self, valor_crisp: float) -> dict[str, float]:
        """Grau de pertinência de `valor_crisp` (0.0-1.0) em cada um dos 5 níveis."""
        valor_crisp = float(np.clip(valor_crisp, 0.0, 1.0))
        return {
            nivel: float(fuzz.interp_membership(self.universo, self.funcao_pertinencia(nivel), valor_crisp))
            for nivel in NIVEIS
        }


# As 3 variáveis linguísticas de entrada do motor
confiabilidade_fonte = VariavelLinguistica("Confiabilidade da Fonte")
forca_conexao = VariavelLinguistica("Força da Conexão")
cobertura_probatoria = VariavelLinguistica("Cobertura Probatória")

# Valores representativos (peso/centróide) de cada termo de saída — usados na
# desfuzzificação GCV. Não incluem "Lacuna", que não é consequente de
# nenhuma regra: é o status atribuído quando nenhuma das 5 regras dispara
# (ver app/fuzzy/engine.py).
PESOS_SAIDA: dict[str, float] = {
    "confirmado": 0.95,
    "indicio_forte": 0.75,
    "indicio_moderado": 0.55,
    "inferencia": 0.35,
    "descartado": 0.10,
}

```

## backend/app/grafo/__init__.py

```python
"""Módulo de grafo de entidades (Neo4j): nós tipados (pessoa física,
pessoa jurídica, conta, evento), arestas tipadas para relações, consulta
de vínculos em 1-2 saltos e detecção de comunidades.

Uso (em app/main.py):
    from app.grafo import router as grafo_router
    from app.grafo.driver import inicializar_esquema, fechar_driver

    app.include_router(grafo_router)
    # no startup: inicializar_esquema()
    # no shutdown: fechar_driver()
"""
from app.grafo.repositorio import (
    adicionar_entidade,
    consultar_vinculos,
    criar_relacao,
    identificar_comunidades,
)
from app.grafo.router import router

__all__ = [
    "router",
    "adicionar_entidade",
    "criar_relacao",
    "consultar_vinculos",
    "identificar_comunidades",
]

```

## backend/app/grafo/driver.py

```python
"""Driver Neo4j (singleton) e utilidades de conexão/esquema."""
import logging
from functools import lru_cache

from neo4j import Driver, GraphDatabase

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_driver() -> Driver:
    settings = get_settings()
    return GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))


def fechar_driver() -> None:
    """Fecha a conexão com o Neo4j. Chamar no shutdown da aplicação."""
    if get_driver.cache_info().currsize:
        get_driver().close()
        get_driver.cache_clear()


def inicializar_esquema() -> None:
    """Cria a constraint de unicidade em `Entidade.id`, se ainda não
    existir. Idempotente — seguro de chamar a cada startup da aplicação."""
    with get_driver().session() as sessao:
        sessao.run("CREATE CONSTRAINT entidade_id_unico IF NOT EXISTS FOR (e:Entidade) REQUIRE e.id IS UNIQUE")
    logger.info("Esquema do grafo Neo4j verificado (constraint Entidade.id).")

```

## backend/app/grafo/excecoes.py

```python
"""Exceções do módulo de grafo de entidades."""


class EntidadeNaoEncontrada(Exception):
    """Levantada ao referenciar, no grafo, uma entidade que não existe."""

    def __init__(self, entidade_id: str) -> None:
        super().__init__(f"Entidade '{entidade_id}' não encontrada no grafo.")
        self.entidade_id = entidade_id

```

## backend/app/grafo/labels.py

```python
"""Conversão de `tipo` / `tipo_relacao` (texto livre, vindo do PostgreSQL)
em labels e tipos de relacionamento Neo4j seguros.

O driver do Neo4j não permite parametrizar labels de nó nem tipos de
relacionamento em Cypher (apenas valores de propriedade) — eles precisam
ser interpolados diretamente na string da consulta. Por isso, todo `tipo`
e `tipo_relacao` passa por sanitização aqui antes de entrar em uma query,
para não permitir Cypher injection via esses campos.
"""
import re

_CARACTERES_INVALIDOS = re.compile(r"[^A-Za-z0-9_]")

# Tipos de entidade previstos explicitamente no domínio (pessoas físicas,
# pessoas jurídicas, contas, eventos) mapeados para labels canônicos.
TIPO_PARA_LABEL: dict[str, str] = {
    "pessoa_fisica": "PessoaFisica",
    "pessoa_juridica": "PessoaJuridica",
    "conta": "Conta",
    "evento": "Evento",
}


def tipo_para_label(tipo: str) -> str:
    """Converte um `tipo` de entidade em um label Neo4j seguro.

    Usa o mapeamento canônico para os 4 tipos previstos; para qualquer
    outro valor, sanitiza a string recebida (mantém apenas [A-Za-z0-9_]) e
    garante que o resultado comece com uma letra.
    """
    if tipo in TIPO_PARA_LABEL:
        return TIPO_PARA_LABEL[tipo]
    return _rotulo_seguro(tipo, prefixo_generico="TipoDesconhecido")


def tipo_relacao_para_neo4j(tipo_relacao: str) -> str:
    """Normaliza um `tipo_relacao` livre para um tipo de relacionamento
    Neo4j seguro, em UPPER_SNAKE_CASE (convenção usual do Cypher)."""
    normalizado = _rotulo_seguro(tipo_relacao.upper(), prefixo_generico="RELACIONADO_A")
    return normalizado


def _rotulo_seguro(bruto: str, *, prefixo_generico: str) -> str:
    limpo = _CARACTERES_INVALIDOS.sub("_", bruto.strip()).strip("_")
    if not limpo:
        return prefixo_generico
    if not (limpo[0].isalpha() or limpo[0] == "_"):
        limpo = f"_{limpo}"
    return limpo

```

## backend/app/grafo/repositorio.py

```python
"""Operações sobre o grafo de entidades no Neo4j.

Modelo:
    - Nós `:Entidade` (label comum) + um label secundário pelo tipo
      (`PessoaFisica`, `PessoaJuridica`, `Conta`, `Evento`, ou um label
      derivado do `tipo` para valores não previstos — ver `app.grafo.labels`).
      Propriedade `id` (mesmo UUID da tabela `entidades` do PostgreSQL),
      com constraint de unicidade (`app.grafo.driver.inicializar_esquema`).
    - Arestas tipadas dinamicamente pelo `tipo_relacao` (normalizado para
      UPPER_SNAKE_CASE), com propriedade `id` (mesmo UUID de `relacoes`).

Funções: `adicionar_entidade`, `criar_relacao`, `consultar_vinculos` (1-2
hops) e `identificar_comunidades` (Louvain via Neo4j GDS, com fallback para
componentes conexos se o plugin GDS não estiver instalado).
"""
import json
import logging
import uuid
from collections import deque
from collections.abc import Iterable

from neo4j.exceptions import ClientError

from app.grafo.driver import get_driver
from app.grafo.excecoes import EntidadeNaoEncontrada
from app.grafo.labels import tipo_para_label, tipo_relacao_para_neo4j

logger = logging.getLogger(__name__)


def adicionar_entidade(
    entidade_id: str,
    tipo: str,
    nome: str,
    caso_id: str,
    atributos: dict | None = None,
    nivel_certeza_fuzzy: float | None = None,
    e_seed: bool = False,
) -> None:
    """Cria ou atualiza (MERGE por `id`) um nó `:Entidade` no grafo, com um
    label secundário correspondente ao seu tipo (pessoa física, pessoa
    jurídica, conta, evento, ...). Idempotente: chamar de novo com o mesmo
    `entidade_id` atualiza as propriedades em vez de duplicar o nó.
    """
    label = tipo_para_label(tipo)
    consulta = (
        "MERGE (e:Entidade {id: $id}) "
        f"SET e:`{label}`, "
        "e.tipo = $tipo, e.nome = $nome, e.caso_id = $caso_id, "
        "e.nivel_certeza_fuzzy = $nivel_certeza_fuzzy, e.e_seed = $e_seed, "
        "e.atributos_json = $atributos_json"
    )
    with get_driver().session() as sessao:
        sessao.run(
            consulta,
            id=entidade_id,
            tipo=tipo,
            nome=nome,
            caso_id=caso_id,
            nivel_certeza_fuzzy=nivel_certeza_fuzzy,
            e_seed=e_seed,
            atributos_json=json.dumps(atributos or {}, ensure_ascii=False),
        )


def criar_relacao(
    relacao_id: str,
    caso_id: str,
    origem_id: str,
    destino_id: str,
    tipo_relacao: str,
    grau_pertinencia_fuzzy: float | None = None,
    evidencia_id: str | None = None,
) -> None:
    """Cria (MERGE por `id`) uma aresta tipada entre duas entidades já
    existentes no grafo.

    Raises:
        EntidadeNaoEncontrada: se a entidade de origem ou de destino não
        existir no grafo.
    """
    tipo_neo4j = tipo_relacao_para_neo4j(tipo_relacao)
    consulta = (
        "MATCH (origem:Entidade {id: $origem_id}), (destino:Entidade {id: $destino_id}) "
        f"MERGE (origem)-[r:`{tipo_neo4j}` {{id: $relacao_id}}]->(destino) "
        "SET r.caso_id = $caso_id, r.tipo_relacao = $tipo_relacao, "
        "r.grau_pertinencia_fuzzy = $grau_pertinencia_fuzzy, r.evidencia_id = $evidencia_id "
        "RETURN origem.id AS origem, destino.id AS destino"
    )
    with get_driver().session() as sessao:
        registro = sessao.run(
            consulta,
            origem_id=origem_id,
            destino_id=destino_id,
            relacao_id=relacao_id,
            caso_id=caso_id,
            tipo_relacao=tipo_relacao,
            grau_pertinencia_fuzzy=grau_pertinencia_fuzzy,
            evidencia_id=evidencia_id,
        ).single()

        if registro is None:
            faltante = origem_id if not _entidade_existe(sessao, origem_id) else destino_id
            raise EntidadeNaoEncontrada(faltante)


def _entidade_existe(sessao, entidade_id: str) -> bool:
    resultado = sessao.run("MATCH (e:Entidade {id: $id}) RETURN e LIMIT 1", id=entidade_id).single()
    return resultado is not None


def consultar_vinculos(entidade_id: str, profundidade: int = 2) -> dict:
    """Consulta os vínculos de uma entidade em 1 a `profundidade` saltos.

    Args:
        entidade_id: id da entidade central.
        profundidade: número de saltos (1 ou 2).

    Returns:
        {"entidade_central": id, "nos": [...], "arestas": [...]}, com todos
        os nós e arestas alcançados dentro da profundidade pedida
        (deduplicados).

    Raises:
        ValueError: se `profundidade` não for 1 nem 2.
        EntidadeNaoEncontrada: se a entidade central não existir no grafo.
    """
    if profundidade not in (1, 2):
        raise ValueError("profundidade deve ser 1 ou 2.")

    # `*1..N` não aceita parâmetro no Cypher — profundidade já está
    # restrita a {1, 2} acima, então a interpolação abaixo é segura.
    consulta = (
        "MATCH (origem:Entidade {id: $id}) "
        f"OPTIONAL MATCH caminho = (origem)-[*1..{profundidade}]-(vizinho) "
        "RETURN origem, collect(DISTINCT caminho) AS caminhos"
    )
    with get_driver().session() as sessao:
        registro = sessao.run(consulta, id=entidade_id).single()

    if registro is None:
        raise EntidadeNaoEncontrada(entidade_id)

    nos: dict[str, dict] = {}
    arestas: dict[str, dict] = {}

    def _registrar_no(no) -> None:
        nos[no["id"]] = _no_para_dict(no)

    _registrar_no(registro["origem"])

    for caminho in registro["caminhos"]:
        if caminho is None:
            continue
        for no in caminho.nodes:
            _registrar_no(no)
        for rel in caminho.relationships:
            chave = rel.get("id") or rel.element_id
            arestas[chave] = _relacao_para_dict(rel)

    return {
        "entidade_central": entidade_id,
        "nos": list(nos.values()),
        "arestas": list(arestas.values()),
    }


def _no_para_dict(no) -> dict:
    return {
        "id": no["id"],
        "tipo": no.get("tipo"),
        "nome": no.get("nome"),
        "labels": sorted(no.labels),
        "caso_id": no.get("caso_id"),
        "nivel_certeza_fuzzy": no.get("nivel_certeza_fuzzy"),
        "e_seed": no.get("e_seed"),
    }


def _relacao_para_dict(rel) -> dict:
    return {
        "id": rel.get("id"),
        "tipo": rel.type,
        "origem_id": rel.start_node["id"],
        "destino_id": rel.end_node["id"],
        "caso_id": rel.get("caso_id"),
        "grau_pertinencia_fuzzy": rel.get("grau_pertinencia_fuzzy"),
        "evidencia_id": rel.get("evidencia_id"),
    }


def identificar_comunidades(caso_id: str) -> list[dict]:
    """Identifica comunidades (clusters de entidades fortemente conectadas
    entre si) dentro de um caso.

    Usa o algoritmo de Louvain via Neo4j Graph Data Science (GDS) quando o
    plugin está instalado; caso contrário, cai para uma detecção mais
    simples por componentes conexos (BFS em Python) como aproximação.

    Returns:
        Lista de {"entidade_id": str, "comunidade": int}.
    """
    try:
        return _comunidades_via_louvain(caso_id)
    except ClientError as erro:
        mensagem = str(erro)
        if "Unknown function" not in mensagem and "Unknown procedure" not in mensagem:
            raise
        logger.warning(
            "Plugin Graph Data Science indisponível no Neo4j (%s); "
            "usando componentes conexos como aproximação de comunidades.",
            mensagem,
        )
        return _comunidades_via_componentes_conexos(caso_id)


def _comunidades_via_louvain(caso_id: str) -> list[dict]:
    nome_grafo = f"comunidades-{uuid.uuid4().hex}"
    with get_driver().session() as sessao:
        sessao.run(
            "CALL gds.graph.project.cypher("
            "$nome, "
            "'MATCH (n:Entidade) WHERE n.caso_id = $caso_id RETURN id(n) AS id', "
            "'MATCH (a:Entidade)-[r]-(b:Entidade) "
            "WHERE a.caso_id = $caso_id AND b.caso_id = $caso_id "
            "RETURN id(a) AS source, id(b) AS target', "
            "{parameters: {caso_id: $caso_id}}) "
            "YIELD graphName",
            nome=nome_grafo,
            caso_id=caso_id,
        )
        try:
            resultado = sessao.run(
                "CALL gds.louvain.stream($nome) "
                "YIELD nodeId, communityId "
                "RETURN gds.util.asNode(nodeId).id AS entidade_id, communityId AS comunidade",
                nome=nome_grafo,
            )
            return [
                {"entidade_id": registro["entidade_id"], "comunidade": registro["comunidade"]}
                for registro in resultado
            ]
        finally:
            sessao.run("CALL gds.graph.drop($nome, false)", nome=nome_grafo)


def _comunidades_via_componentes_conexos(caso_id: str) -> list[dict]:
    """Aproximação de comunidades sem GDS: cada componente conexo do
    subgrafo do caso vira uma "comunidade" (id sequencial)."""
    consulta = (
        "MATCH (a:Entidade {caso_id: $caso_id}) "
        "OPTIONAL MATCH (a)-[]-(b:Entidade {caso_id: $caso_id}) "
        "RETURN a.id AS origem, collect(DISTINCT b.id) AS vizinhos"
    )
    with get_driver().session() as sessao:
        registros = list(sessao.run(consulta, caso_id=caso_id))

    adjacencia: dict[str, set[str]] = {}
    for registro in registros:
        origem = registro["origem"]
        adjacencia.setdefault(origem, set())
        for vizinho in registro["vizinhos"]:
            if vizinho is not None:
                adjacencia[origem].add(vizinho)
                adjacencia.setdefault(vizinho, set()).add(origem)

    return list(_componentes_conexos(adjacencia))


def _componentes_conexos(adjacencia: dict[str, set[str]]) -> Iterable[dict]:
    visitados: set[str] = set()
    proxima_comunidade = 0
    for no in adjacencia:
        if no in visitados:
            continue
        fila = deque([no])
        visitados.add(no)
        while fila:
            atual = fila.popleft()
            yield {"entidade_id": atual, "comunidade": proxima_comunidade}
            for vizinho in adjacencia[atual]:
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    fila.append(vizinho)
        proxima_comunidade += 1

```

## backend/app/grafo/router.py

```python
"""Endpoints HTTP do módulo de grafo de entidades."""
from fastapi import APIRouter, HTTPException, Query

from app.grafo.excecoes import EntidadeNaoEncontrada
from app.grafo.repositorio import consultar_vinculos
from app.grafo.schemas import VinculosResponse

router = APIRouter(prefix="/api/grafo", tags=["grafo"])


@router.get(
    "/vinculos/{entidade_id}",
    response_model=VinculosResponse,
    summary="Subárvore de relacionamentos de uma entidade (1-2 saltos)",
)
def obter_vinculos(
    entidade_id: str,
    profundidade: int = Query(2, ge=1, le=2, description="Número de saltos a partir da entidade: 1 ou 2."),
) -> VinculosResponse:
    """Retorna todos os nós e arestas alcançados a partir de `entidade_id`
    dentro de `profundidade` saltos no grafo (Neo4j)."""
    try:
        resultado = consultar_vinculos(entidade_id, profundidade=profundidade)
    except EntidadeNaoEncontrada as erro:
        raise HTTPException(status_code=404, detail=str(erro)) from erro
    return VinculosResponse(**resultado)

```

## backend/app/grafo/schemas.py

```python
"""Schemas Pydantic do módulo de grafo de entidades."""
from pydantic import BaseModel


class NoGrafo(BaseModel):
    id: str
    tipo: str | None
    nome: str | None
    labels: list[str]
    caso_id: str | None
    nivel_certeza_fuzzy: float | None
    e_seed: bool | None


class ArestaGrafo(BaseModel):
    id: str | None
    tipo: str
    origem_id: str
    destino_id: str
    caso_id: str | None
    grau_pertinencia_fuzzy: float | None
    evidencia_id: str | None


class VinculosResponse(BaseModel):
    """Resposta de GET /api/grafo/vinculos/{entidade_id}: a subárvore de
    relacionamentos de uma entidade em 1-2 saltos."""

    entidade_central: str
    nos: list[NoGrafo]
    arestas: list[ArestaGrafo]


class ComunidadeItem(BaseModel):
    entidade_id: str
    comunidade: int

```

## backend/app/ingestao/__init__.py

```python
"""Módulo de ingestão documental: upload, hashing SHA-256, extração de
texto (PDF/DOCX/OCR) e indexação semântica no ChromaDB.

Uso (em app/main.py):
    from app.ingestao import router as documentos_router
    app.include_router(documentos_router)
"""
from app.ingestao.router import router

__all__ = ["router"]

```

## backend/app/ingestao/chroma_client.py

```python
"""Cliente ChromaDB: indexação do conteúdo textual dos documentos para
busca semântica (RAG).

Conecta ao serviço `chromadb` do docker-compose.yml via HTTP. A coleção usa
a função de embedding padrão do ChromaDB (não requer chave de API externa).
"""
from functools import lru_cache

import chromadb

from app.core.config import get_settings

NOME_COLECAO = "documentos"

TAMANHO_CHUNK = 1500
SOBREPOSICAO_CHUNK = 200


@lru_cache
def get_chroma_client() -> chromadb.ClientAPI:
    settings = get_settings()
    return chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)


def get_colecao_documentos():
    return get_chroma_client().get_or_create_collection(name=NOME_COLECAO)


def dividir_em_chunks(texto: str, tamanho: int = TAMANHO_CHUNK, sobreposicao: int = SOBREPOSICAO_CHUNK) -> list[str]:
    """Divide um texto longo em pedaços sobrepostos, unidade de indexação
    do ChromaDB (documentos muito longos prejudicam a qualidade do embedding
    e a granularidade da busca semântica)."""
    texto = texto.strip()
    if not texto:
        return []
    if len(texto) <= tamanho:
        return [texto]

    chunks = []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + tamanho
        chunks.append(texto[inicio:fim])
        inicio = fim - sobreposicao
    return chunks


def indexar_documento(documento_id: str, caso_id: str, texto: str, metadados_extra: dict | None = None) -> int:
    """Indexa o texto de um documento no ChromaDB, dividido em chunks.

    Cada chunk vira um "documento" na coleção, com id `{documento_id}::{n}`
    e metadados apontando de volta para o documento e o caso no PostgreSQL.

    Returns:
        Número de chunks efetivamente indexados.
    """
    chunks = dividir_em_chunks(texto)
    if not chunks:
        return 0

    colecao = get_colecao_documentos()
    ids = [f"{documento_id}::{indice}" for indice in range(len(chunks))]
    metadados = [
        {"documento_id": documento_id, "caso_id": caso_id, "chunk_indice": indice, **(metadados_extra or {})}
        for indice in range(len(chunks))
    ]
    colecao.add(ids=ids, documents=chunks, metadatas=metadados)
    return len(chunks)


def remover_indexacao(documento_id: str, quantidade_chunks: int) -> None:
    """Remove os chunks de um documento da coleção (ex.: ao excluir o
    documento no PostgreSQL)."""
    if quantidade_chunks <= 0:
        return
    ids = [f"{documento_id}::{indice}" for indice in range(quantidade_chunks)]
    get_colecao_documentos().delete(ids=ids)

```

## backend/app/ingestao/extratores.py

```python
"""Extração de texto por tipo de arquivo (PDF, DOCX, imagens via OCR).

A extração nunca lança exceção: se falhar (arquivo corrompido, dependência
de OCR ausente etc.) apenas loga um aviso e retorna string vazia — a
ingestão do documento no PostgreSQL não deve falhar por causa da extração
de texto para a indexação semântica.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EXTENSOES_IMAGEM: frozenset[str] = frozenset({".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"})
EXTENSOES_SUPORTADAS: frozenset[str] = frozenset({".pdf", ".docx", *EXTENSOES_IMAGEM})


def extrair_texto(caminho: Path) -> str:
    """Extrai o texto de `caminho` de acordo com sua extensão.

    Retorna string vazia para extensões não reconhecidas ou em caso de
    qualquer falha na extração.
    """
    extensao = caminho.suffix.lower()
    try:
        if extensao == ".pdf":
            return _extrair_pdf(caminho)
        if extensao == ".docx":
            return _extrair_docx(caminho)
        if extensao in EXTENSOES_IMAGEM:
            return _extrair_imagem(caminho)
    except Exception:
        logger.warning("Falha ao extrair texto de %s", caminho, exc_info=True)
        return ""
    return ""


def _extrair_pdf(caminho: Path) -> str:
    from pypdf import PdfReader

    leitor = PdfReader(str(caminho))
    return "\n".join(pagina.extract_text() or "" for pagina in leitor.pages).strip()


def _extrair_docx(caminho: Path) -> str:
    import docx

    documento = docx.Document(str(caminho))
    return "\n".join(paragrafo.text for paragrafo in documento.paragraphs).strip()


def _extrair_imagem(caminho: Path) -> str:
    """OCR via pytesseract. Requer o binário do Tesseract instalado no
    sistema (não é resolvido via pip) — se ausente, `extrair_texto` captura
    a exceção e devolve string vazia."""
    import pytesseract
    from PIL import Image

    with Image.open(caminho) as imagem:
        return pytesseract.image_to_string(imagem, lang="por+eng").strip()

```

## backend/app/ingestao/router.py

```python
"""Endpoints HTTP do módulo de ingestão documental."""
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.ingestao.schemas import DocumentoUploadResponse
from app.ingestao.servico import processar_upload

router = APIRouter(prefix="/api/documentos", tags=["documentos"])


@router.post(
    "/upload",
    response_model=DocumentoUploadResponse,
    status_code=201,
    summary="Upload e indexação de um documento (PDF, DOCX ou imagem)",
)
def upload_documento(
    caso_id: uuid.UUID = Form(..., description="ID do caso ao qual o documento pertence."),
    arquivo: UploadFile = File(..., description="PDF, DOCX ou imagem (PNG/JPG/TIFF/BMP)."),
    tipo_documento: str | None = Form(None, description="Ex.: 'contrato', 'e-mail', 'ata de reunião'."),
    descricao: str | None = Form(None),
    confiabilidade_fonte: float | None = Form(None, ge=0.0, le=1.0),
    inserido_por: str | None = Form(None, description="Identificação de quem realizou o upload."),
    db: Session = Depends(get_db),
) -> DocumentoUploadResponse:
    """Recebe o upload de um documento via `multipart/form-data`:

    1. calcula o SHA-256 do arquivo (rejeita duplicatas);
    2. salva o arquivo em disco e seus metadados na tabela `documentos`;
    3. extrai o texto (PDF/DOCX/OCR de imagem) e o indexa no ChromaDB para
       busca semântica.
    """
    documento, trechos_indexados = processar_upload(
        db=db,
        caso_id=caso_id,
        arquivo=arquivo,
        tipo_documento=tipo_documento,
        descricao=descricao,
        confiabilidade_fonte=confiabilidade_fonte,
        inserido_por=inserido_por,
    )
    return DocumentoUploadResponse(
        id=documento.id,
        caso_id=documento.caso_id,
        tipo_documento=documento.tipo_documento,
        arquivo_path=documento.arquivo_path,
        hash_sha256=documento.hash_sha256,
        descricao=documento.descricao,
        confiabilidade_fonte=(
            float(documento.confiabilidade_fonte) if documento.confiabilidade_fonte is not None else None
        ),
        data_insercao=documento.data_insercao,
        inserido_por=documento.inserido_por,
        trechos_indexados=trechos_indexados,
    )

```

## backend/app/ingestao/schemas.py

```python
"""Schemas Pydantic do módulo de ingestão documental."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DocumentoUploadResponse(BaseModel):
    """Resposta de POST /api/documentos/upload."""

    id: uuid.UUID
    caso_id: uuid.UUID
    tipo_documento: str | None
    arquivo_path: str
    hash_sha256: str
    descricao: str | None
    confiabilidade_fonte: float | None
    data_insercao: datetime
    inserido_por: str | None
    trechos_indexados: int = Field(
        description="Número de trechos (chunks) indexados no ChromaDB para busca semântica. "
        "0 se o texto não pôde ser extraído do arquivo."
    )

```

## backend/app/ingestao/servico.py

```python
"""Orquestra a ingestão de um documento:

    1. valida a extensão e o caso de destino;
    2. grava o arquivo em disco em streaming, calculando o SHA-256;
    3. rejeita duplicatas (mesmo hash já cadastrado);
    4. extrai o texto (PDF/DOCX/imagem);
    5. persiste os metadados na tabela `documentos` (PostgreSQL);
    6. indexa o texto extraído no ChromaDB para busca semântica.

A indexação semântica (passo 6) é best-effort: se o ChromaDB estiver
indisponível, o documento permanece cadastrado no PostgreSQL normalmente.
"""
import hashlib
import logging
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingestao.chroma_client import indexar_documento
from app.ingestao.extratores import EXTENSOES_SUPORTADAS, extrair_texto
from app.models.caso import Caso
from app.models.documento import Documento

logger = logging.getLogger(__name__)

TAMANHO_BLOCO = 1024 * 1024  # 1 MiB, para não carregar o arquivo inteiro em memória


def _extensao_valida(nome_arquivo: str) -> str:
    extensao = Path(nome_arquivo).suffix.lower()
    if extensao not in EXTENSOES_SUPORTADAS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Extensão '{extensao or '(nenhuma)'}' não suportada. "
                f"Extensões aceitas: {', '.join(sorted(EXTENSOES_SUPORTADAS))}."
            ),
        )
    return extensao


def _salvar_e_calcular_hash(arquivo: UploadFile, diretorio_destino: Path, extensao: str) -> tuple[Path, str]:
    """Grava o upload em disco em streaming, calculando o SHA-256 ao mesmo
    tempo. O nome final do arquivo é derivado do hash (nunca do nome
    original enviado pelo cliente), evitando path traversal."""
    diretorio_destino.mkdir(parents=True, exist_ok=True)

    sha256 = hashlib.sha256()
    arquivo.file.seek(0)
    with tempfile.NamedTemporaryFile(dir=diretorio_destino, suffix=extensao, delete=False) as tmp:
        caminho_temporario = Path(tmp.name)
        while bloco := arquivo.file.read(TAMANHO_BLOCO):
            sha256.update(bloco)
            tmp.write(bloco)

    return caminho_temporario, sha256.hexdigest()


def processar_upload(
    db: Session,
    caso_id: uuid.UUID,
    arquivo: UploadFile,
    tipo_documento: str | None,
    descricao: str | None,
    confiabilidade_fonte: float | None,
    inserido_por: str | None,
) -> tuple[Documento, int]:
    """Executa o pipeline completo de ingestão de um documento.

    Returns:
        Tupla (documento, trechos_indexados_no_chromadb).

    Raises:
        HTTPException: 400 sem nome de arquivo, 404 se o caso não existir,
        415 se a extensão não for suportada, 409 se o hash SHA-256 já
        estiver cadastrado.
    """
    if not arquivo.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nome do arquivo ausente.")

    extensao = _extensao_valida(arquivo.filename)

    caso = db.get(Caso, caso_id)
    if caso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Caso {caso_id} não encontrado.")

    settings = get_settings()
    diretorio_caso = Path(settings.storage_dir) / str(caso_id)
    caminho_temporario, hash_sha256 = _salvar_e_calcular_hash(arquivo, diretorio_caso, extensao)

    documento_existente = db.query(Documento).filter_by(hash_sha256=hash_sha256).first()
    if documento_existente is not None:
        caminho_temporario.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Este arquivo já foi cadastrado (documento {documento_existente.id}).",
        )

    caminho_final = diretorio_caso / f"{hash_sha256}{extensao}"
    if caminho_final.exists():
        # Mesmo conteúdo já salvo em disco (registro correspondente pode ter
        # sido removido do banco sem apagar o arquivo) — reaproveita.
        caminho_temporario.unlink(missing_ok=True)
    else:
        shutil.move(str(caminho_temporario), str(caminho_final))

    texto_extraido = extrair_texto(caminho_final)

    documento = Documento(
        caso_id=caso_id,
        tipo_documento=tipo_documento,
        arquivo_path=str(caminho_final),
        hash_sha256=hash_sha256,
        descricao=descricao,
        confiabilidade_fonte=confiabilidade_fonte,
        inserido_por=inserido_por,
    )
    db.add(documento)
    try:
        db.commit()
    except IntegrityError:
        # Corrida entre a checagem acima e o INSERT: outra requisição
        # cadastrou o mesmo hash entre os dois passos.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este arquivo já foi cadastrado (hash SHA-256 duplicado).",
        ) from None
    db.refresh(documento)

    trechos_indexados = 0
    if texto_extraido:
        try:
            trechos_indexados = indexar_documento(
                documento_id=str(documento.id),
                caso_id=str(caso_id),
                texto=texto_extraido,
                metadados_extra={
                    "tipo_documento": tipo_documento or "",
                    "arquivo_original": arquivo.filename,
                },
            )
        except Exception:
            logger.warning("Falha ao indexar documento %s no ChromaDB", documento.id, exc_info=True)

    return documento, trechos_indexados

```

## backend/app/main.py

```python
"""Ponto de entrada da aplicação FastAPI.

Rodar localmente (a partir da pasta backend/):
    uvicorn app.main:app --reload
"""
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.casos import router as casos_router
from app.core.config import get_settings
from app.core.database import get_db
from app.grafo import router as grafo_router
from app.grafo.driver import fechar_driver, inicializar_esquema
from app.ingestao import router as documentos_router

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(casos_router)
app.include_router(documentos_router)
app.include_router(grafo_router)


@app.on_event("startup")
def on_startup() -> None:
    # O schema do PostgreSQL é gerenciado pelo Alembic (backend/migrations/),
    # não por Base.metadata.create_all() — rode `make migrate` (ou
    # `alembic upgrade head`) antes de subir a aplicação pela primeira vez.
    try:
        inicializar_esquema()
    except Exception:
        # O grafo de entidades é um enriquecimento sobre o PostgreSQL: se o
        # Neo4j ainda não estiver disponível no boot, a API sobe mesmo
        # assim (as rotas de /api/grafo falharão até ele voltar).
        logger.warning("Não foi possível inicializar o esquema do Neo4j no startup.", exc_info=True)


@app.on_event("shutdown")
def on_shutdown() -> None:
    fechar_driver()


@app.get("/", tags=["health"])
def root() -> dict:
    return {"app": settings.app_name, "status": "ok"}


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}

```

## backend/app/models/__init__.py

```python
"""Agrega todos os models para que Base.metadata os enxergue e os
relationships declarados por string (ex: "Caso") sejam resolvidos."""
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.caso import Caso
from app.models.diligencia import Diligencia
from app.models.documento import Documento
from app.models.entidade import Entidade
from app.models.nucleo_investigativo import NucleoInvestigativo
from app.models.relacao import Relacao

__all__ = [
    "Base",
    "Caso",
    "Entidade",
    "Documento",
    "Relacao",
    "NucleoInvestigativo",
    "Diligencia",
    "AuditLog",
]

```

## backend/app/models/audit_log.py

```python
"""Model: audit_log"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    tabela_afetada: Mapped[str] = mapped_column(String, nullable=False)
    registro_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    operacao: Mapped[str] = mapped_column(String, nullable=False)
    dados_anteriores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dados_novos: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    usuario: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} tabela_afetada={self.tabela_afetada!r} operacao={self.operacao!r}>"

```

## backend/app/models/base.py

```python
"""Base declarativa compartilhada por todos os models."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

```

## backend/app/models/caso.py

```python
"""Model: casos"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Caso(Base):
    __tablename__ = "casos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tema: Mapped[str] = mapped_column(String, nullable=False)
    subcategoria: Mapped[str | None] = mapped_column(String, nullable=True)
    objeto_central: Mapped[str | None] = mapped_column(Text, nullable=True)
    problema_enunciado: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relacionamentos
    entidades: Mapped[list["Entidade"]] = relationship(back_populates="caso", cascade="all, delete-orphan")
    documentos: Mapped[list["Documento"]] = relationship(back_populates="caso", cascade="all, delete-orphan")
    relacoes: Mapped[list["Relacao"]] = relationship(back_populates="caso", cascade="all, delete-orphan")
    nucleos_investigativos: Mapped[list["NucleoInvestigativo"]] = relationship(
        back_populates="caso", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Caso id={self.id} tema={self.tema!r} status={self.status!r}>"

```

## backend/app/models/diligencia.py

```python
"""Model: diligencias"""
import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Diligencia(Base):
    __tablename__ = "diligencias"
    __table_args__ = (CheckConstraint("prioridade BETWEEN 1 AND 5", name="ck_diligencias_prioridade"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nucleo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nucleos_investigativos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    prioridade: Mapped[int] = mapped_column(Integer, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    prazo_limite: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsavel: Mapped[str | None] = mapped_column(String, nullable=True)
    resultado_sintese: Mapped[str | None] = mapped_column(Text, nullable=True)
    grau_fuzzy_resultante: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)

    # Relacionamentos
    nucleo: Mapped["NucleoInvestigativo"] = relationship(back_populates="diligencias")

    def __repr__(self) -> str:
        return f"<Diligencia id={self.id} prioridade={self.prioridade} status={self.status!r}>"

```

## backend/app/models/documento.py

```python
"""Model: documentos"""
import uuid
from datetime import datetime

from sqlalchemy import CHAR, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Documento(Base):
    __tablename__ = "documentos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("casos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    tipo_documento: Mapped[str | None] = mapped_column(String, nullable=True)
    arquivo_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    hash_sha256: Mapped[str] = mapped_column(CHAR(64), unique=True, nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    confiabilidade_fonte: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    data_insercao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    inserido_por: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relacionamentos
    caso: Mapped["Caso"] = relationship(back_populates="documentos")
    relacoes_como_evidencia: Mapped[list["Relacao"]] = relationship(back_populates="evidencia")

    def __repr__(self) -> str:
        return f"<Documento id={self.id} hash_sha256={self.hash_sha256!r}>"

```

## backend/app/models/entidade.py

```python
"""Model: entidades"""
import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Entidade(Base):
    __tablename__ = "entidades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("casos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    atributos: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    nivel_certeza_fuzzy: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    e_seed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relacionamentos
    caso: Mapped["Caso"] = relationship(back_populates="entidades")

    relacoes_como_origem: Mapped[list["Relacao"]] = relationship(
        back_populates="entidade_origem",
        foreign_keys="Relacao.entidade_origem_id",
        cascade="all, delete-orphan",
    )
    relacoes_como_destino: Mapped[list["Relacao"]] = relationship(
        back_populates="entidade_destino",
        foreign_keys="Relacao.entidade_destino_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Entidade id={self.id} tipo={self.tipo!r} nome={self.nome!r}>"

```

## backend/app/models/nucleo_investigativo.py

```python
"""Model: nucleos_investigativos"""
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NucleoInvestigativo(Base):
    __tablename__ = "nucleos_investigativos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("casos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    titulo: Mapped[str] = mapped_column(String, nullable=False)
    objeto_especifico: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)

    # Relacionamentos
    caso: Mapped["Caso"] = relationship(back_populates="nucleos_investigativos")
    diligencias: Mapped[list["Diligencia"]] = relationship(back_populates="nucleo", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<NucleoInvestigativo id={self.id} titulo={self.titulo!r}>"

```

## backend/app/models/relacao.py

```python
"""Model: relacoes"""
import uuid

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Relacao(Base):
    __tablename__ = "relacoes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("casos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entidade_origem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entidade_destino_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidencia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="SET NULL"), nullable=True, index=True
    )

    tipo_relacao: Mapped[str] = mapped_column(String, nullable=False)
    grau_pertinencia_fuzzy: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)

    # Relacionamentos
    caso: Mapped["Caso"] = relationship(back_populates="relacoes")
    entidade_origem: Mapped["Entidade"] = relationship(
        back_populates="relacoes_como_origem", foreign_keys=[entidade_origem_id]
    )
    entidade_destino: Mapped["Entidade"] = relationship(
        back_populates="relacoes_como_destino", foreign_keys=[entidade_destino_id]
    )
    evidencia: Mapped["Documento | None"] = relationship(back_populates="relacoes_como_evidencia")

    def __repr__(self) -> str:
        return f"<Relacao id={self.id} tipo_relacao={self.tipo_relacao!r}>"

```

## backend/migrations/env.py

```python
"""Ambiente de execução do Alembic.

Usa a mesma configuração e os mesmos models do resto da aplicação
(app.core.config, app.models) em vez de duplicar a connection string no
alembic.ini — uma única fonte de verdade (DATABASE_URL / .env).
"""
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Garante que `app` seja importável quando o Alembic roda a partir de
# backend/ (via `alembic upgrade head` ou `make migrate`).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Usado por `alembic revision --autogenerate` para comparar o schema real
# do banco com os models declarados em app/models/.
target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", get_settings().database_url)


def run_migrations_offline() -> None:
    """Gera o SQL das migrations sem se conectar a um banco (`--sql`)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica as migrations conectando de fato ao banco (modo normal)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

```

## backend/migrations/script.py.mako

```html
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

```

## backend/migrations/versions/0001_schema_inicial.py

```python
"""schema inicial: casos, entidades, documentos, relacoes,
nucleos_investigativos, diligencias, audit_log

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "casos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tema", sa.String(), nullable=False),
        sa.Column("subcategoria", sa.String(), nullable=True),
        sa.Column("objeto_central", sa.Text(), nullable=True),
        sa.Column("problema_enunciado", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "entidades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "caso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("casos.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("atributos", postgresql.JSONB(), nullable=True),
        sa.Column("nivel_certeza_fuzzy", sa.Numeric(3, 2), nullable=True),
        sa.Column("e_seed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_entidades_caso_id", "entidades", ["caso_id"])

    op.create_table(
        "documentos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "caso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("casos.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("tipo_documento", sa.String(), nullable=True),
        sa.Column("arquivo_path", sa.Text(), nullable=True),
        sa.Column("hash_sha256", sa.CHAR(64), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("confiabilidade_fonte", sa.Numeric(3, 2), nullable=True),
        sa.Column("data_insercao", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("inserido_por", sa.String(), nullable=True),
    )
    op.create_index("ix_documentos_caso_id", "documentos", ["caso_id"])
    # unique=True: mesmo índice que SQLAlchemy geraria para
    # `mapped_column(unique=True, index=True)` no model Documento.
    op.create_index("ix_documentos_hash_sha256", "documentos", ["hash_sha256"], unique=True)

    op.create_table(
        "relacoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "caso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("casos.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "entidade_origem_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entidades.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "entidade_destino_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entidades.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evidencia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documentos.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tipo_relacao", sa.String(), nullable=False),
        sa.Column("grau_pertinencia_fuzzy", sa.Numeric(3, 2), nullable=True),
    )
    op.create_index("ix_relacoes_caso_id", "relacoes", ["caso_id"])
    op.create_index("ix_relacoes_entidade_origem_id", "relacoes", ["entidade_origem_id"])
    op.create_index("ix_relacoes_entidade_destino_id", "relacoes", ["entidade_destino_id"])
    op.create_index("ix_relacoes_evidencia_id", "relacoes", ["evidencia_id"])

    op.create_table(
        "nucleos_investigativos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "caso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("casos.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("objeto_especifico", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
    )
    op.create_index("ix_nucleos_investigativos_caso_id", "nucleos_investigativos", ["caso_id"])

    op.create_table(
        "diligencias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "nucleo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("nucleos_investigativos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prioridade", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("prazo_limite", sa.Date(), nullable=True),
        sa.Column("responsavel", sa.String(), nullable=True),
        sa.Column("resultado_sintese", sa.Text(), nullable=True),
        sa.Column("grau_fuzzy_resultante", sa.Numeric(3, 2), nullable=True),
        sa.CheckConstraint("prioridade BETWEEN 1 AND 5", name="ck_diligencias_prioridade"),
    )
    op.create_index("ix_diligencias_nucleo_id", "diligencias", ["nucleo_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tabela_afetada", sa.String(), nullable=False),
        sa.Column("registro_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operacao", sa.String(), nullable=False),
        sa.Column("dados_anteriores", postgresql.JSONB(), nullable=True),
        sa.Column("dados_novos", postgresql.JSONB(), nullable=True),
        sa.Column("usuario", sa.String(), nullable=True),
        sa.Column("timestamp_utc", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("diligencias")
    op.drop_table("nucleos_investigativos")
    op.drop_table("relacoes")
    op.drop_table("documentos")
    op.drop_table("entidades")
    op.drop_table("casos")

```

## backend/pytest.ini

```ini
[pytest]
pythonpath = .
testpaths = tests

```

## backend/requirements.txt

```text
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.12
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
alembic==1.13.2
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1

# Módulo de ingestão documental (backend/app/ingestao/)
pypdf==5.0.1
python-docx==1.1.2
Pillow==10.4.0
pytesseract==0.3.13
chromadb==0.5.15

# Módulo de grafo de entidades (backend/app/grafo/)
neo4j==5.24.0

# Motor de inferência fuzzy (backend/app/fuzzy/)
numpy==1.26.4
scipy==1.13.1
networkx==3.3
scikit-fuzzy==0.5.0

# Testes e lint
pytest==8.3.3
flake8==7.1.1

# Celery worker (backend/app/celery_app.py)
celery==5.4.0
redis==5.0.8

```

## backend/tests/test_fuzzy_engine.py

```python
"""Testes do motor de inferência fuzzy (backend/app/fuzzy/).

Cobre os 6 cenários de status do Grau de Certeza: Confirmado, Indício Forte,
Indício Moderado, Inferência, Descartado e Lacuna.

Os valores de entrada de cada cenário "alinhado" foram escolhidos no pico da
função de pertinência do nível correspondente (ex.: 0.95 é o pico de
"muito_alta"), de forma que apenas uma regra dispare com força 1.0 e o GCV
resultante seja exatamente o peso daquela regra — tornando o resultado
esperado exato, não apenas aproximado.
"""
import pytest

from app.fuzzy import inferir
from app.fuzzy.engine import calcular_grau_certeza


@pytest.mark.parametrize(
    ("cenario", "confiabilidade", "forca", "cobertura", "grau_esperado", "status_esperado"),
    [
        ("entradas muito altas", 0.95, 0.95, 0.95, 0.95, "Confirmado"),
        ("entradas médias-altas", 0.75, 0.75, 0.75, 0.75, "Indício Forte"),
        ("entradas médias", 0.50, 0.50, 0.50, 0.55, "Indício Moderado"),
        ("entradas baixas", 0.25, 0.25, 0.25, 0.35, "Inferência"),
        ("entradas muito baixas", 0.02, 0.02, 0.02, 0.10, "Descartado"),
    ],
)
def test_cenarios_com_entradas_alinhadas(cenario, confiabilidade, forca, cobertura, grau_esperado, status_esperado):
    grau_certeza, status = inferir(confiabilidade, forca, cobertura)

    assert status == status_esperado, f"[{cenario}] status esperado {status_esperado!r}, obtido {status!r}"
    assert grau_certeza == pytest.approx(grau_esperado, abs=1e-6), (
        f"[{cenario}] grau de certeza esperado {grau_esperado}, obtido {grau_certeza}"
    )
    assert 0.0 <= grau_certeza <= 1.0


def test_entradas_divergentes_geram_lacuna():
    """Quando os 3 critérios apontam para níveis muito diferentes entre si,
    nenhuma das 5 regras (que exigem o MESMO nível nas 3 entradas) dispara
    de forma significativa: o caso vira uma Lacuna, não um ponto na escala.

    Aqui: Confiabilidade da Fonte muito alta (0.95), Força da Conexão muito
    baixa (0.02) e Cobertura Probatória média (0.50) — três níveis distintos,
    sem nenhum nível em comum entre as 3 variáveis.
    """
    grau_certeza, status = inferir(confiabilidade=0.95, forca=0.02, cobertura=0.50)

    assert status == "Lacuna"
    assert grau_certeza == 0.0


def test_resultado_detalhado_identifica_a_regra_dominante():
    resultado = calcular_grau_certeza(confiabilidade=0.95, forca=0.95, cobertura=0.95)

    assert resultado.status == "Confirmado"
    assert resultado.grau_certeza == pytest.approx(0.95)
    assert resultado.regra_dominante == 1  # "Muito Alta / Muito Alta / Muito Alta -> Confirmado"
    assert resultado.disparos[1] == pytest.approx(1.0)
    assert all(disparo == pytest.approx(0.0) for numero, disparo in resultado.disparos.items() if numero != 1)


def test_resultado_detalhado_sem_regra_dominante_na_lacuna():
    resultado = calcular_grau_certeza(confiabilidade=0.95, forca=0.02, cobertura=0.50)

    assert resultado.status == "Lacuna"
    assert resultado.regra_dominante is None
    assert all(disparo == pytest.approx(0.0) for disparo in resultado.disparos.values())


@pytest.mark.parametrize("valor", [-0.5, 1.5])
def test_valores_fora_de_0_1_sao_limitados_ao_universo(valor):
    """Entradas fora de [0, 1] são recortadas (clip) em vez de quebrar a
    fuzzificação ou estourar o intervalo do grau de certeza."""
    grau_certeza, status = inferir(valor, valor, valor)

    assert 0.0 <= grau_certeza <= 1.0
    assert status in {
        "Confirmado",
        "Indício Forte",
        "Indício Moderado",
        "Inferência",
        "Descartado",
        "Lacuna",
    }

```

## docker-compose.yml

```yaml
# docker-compose.yml
# Stack: PostgreSQL + Neo4j + Redis + ChromaDB + backend (FastAPI) +
# frontend (React/nginx) + worker Celery opcional.
# Todos os serviços com estado usam volumes nomeados para persistência.
# Configure credenciais no arquivo .env (veja .env.example).

# Variáveis de ambiente compartilhadas por backend e celery_worker: ambos
# rodam a mesma imagem/código e precisam falar com os mesmos serviços de
# dados, usando os hostnames internos do compose (não localhost).
x-backend-env: &backend-env
  DATABASE_URL: postgresql+psycopg2://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@postgres:5432/${POSTGRES_DB:-app}
  NEO4J_URI: bolt://neo4j:7687
  NEO4J_USER: ${NEO4J_USER:-neo4j}
  NEO4J_PASSWORD: ${NEO4J_PASSWORD:-neo4jpassword}
  CHROMA_HOST: chromadb
  CHROMA_PORT: 8000
  CELERY_BROKER_URL: redis://:${REDIS_PASSWORD:-redispassword}@redis:6379/0
  CELERY_RESULT_BACKEND_URL: redis://:${REDIS_PASSWORD:-redispassword}@redis:6379/1
  STORAGE_DIR: /app/storage/documentos
  APP_NAME: ${APP_NAME:-Sindicancia API}
  DEBUG: ${DEBUG:-false}
  CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000,http://localhost:5173}

services:
  postgres:
    image: postgres:16.4-alpine
    container_name: postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-app}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  neo4j:
    image: neo4j:5.24-community
    container_name: neo4j
    restart: unless-stopped
    environment:
      NEO4J_AUTH: ${NEO4J_USER:-neo4j}/${NEO4J_PASSWORD:-neo4jpassword}
      # apoc: procedures utilitárias. graph-data-science: algoritmos de grafo
      # (Louvain para detecção de comunidades, usado em backend/app/grafo/).
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    ports:
      - "${NEO4J_HTTP_PORT:-7474}:7474" # Neo4j Browser
      - "${NEO4J_BOLT_PORT:-7687}:7687" # Bolt protocol
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import
      - neo4j_plugins:/plugins
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:7474 || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7.4-alpine
    container_name: redis
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes", "--requirepass", "${REDIS_PASSWORD:-redispassword}"]
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD-SHELL", "redis-cli -a ${REDIS_PASSWORD:-redispassword} ping | grep PONG"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  chromadb:
    image: chromadb/chroma:0.5.15
    container_name: chromadb
    restart: unless-stopped
    environment:
      IS_PERSISTENT: "TRUE"
      PERSIST_DIRECTORY: /chroma/chroma
      ANONYMIZED_TELEMETRY: "FALSE"
    ports:
      - "${CHROMA_PORT:-8000}:8000"
    volumes:
      - chroma_data:/chroma/chroma
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/heartbeat || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: backend
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      neo4j:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_healthy
    environment:
      <<: *backend-env
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    volumes:
      - documentos_storage:/app/storage/documentos
    networks:
      - backend

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: frontend
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    ports:
      - "${FRONTEND_PORT:-80}:80"
    networks:
      - backend

  # Serviço opcional: worker Celery para tarefas assíncronas em background
  # (ex.: extração/OCR e indexação pesada do módulo app/ingestao/, hoje
  # síncronas na própria requisição HTTP). Usa a MESMA imagem do backend —
  # só muda o comando executado no container.
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: celery_worker
    restart: unless-stopped
    command: ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]
    depends_on:
      postgres:
        condition: service_healthy
      neo4j:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_healthy
    environment:
      <<: *backend-env
    volumes:
      - documentos_storage:/app/storage/documentos
    networks:
      - backend

networks:
  backend:
    driver: bridge

volumes:
  postgres_data:
  neo4j_data:
  neo4j_logs:
  neo4j_import:
  neo4j_plugins:
  redis_data:
  chroma_data:
  documentos_storage:

```

## frontend/.dockerignore

```text
node_modules
dist
.git
.env
.env.local

```

## frontend/.gitignore

```text
node_modules
dist
dist-ssr
.env
.env.local
*.local

```

## frontend/Dockerfile

```dockerfile
# frontend/Dockerfile
# Build multi-stágio: compila o app Vite/React com Node 20 e serve os
# arquivos estáticos resultantes (dist/) com nginx.

# ---- estágio de build ----
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* ./
# `npm ci` (instalação reprodutível) requer um package-lock.json commitado.
# Como este projeto ainda não tem um (nenhum `npm install` rodou fora do
# container), usamos `npm install` por enquanto — troque para `npm ci`
# assim que o lockfile existir no repositório.
RUN npm install

COPY . .
RUN npm run build

# ---- estágio de serviço ----
FROM nginx:1.27-alpine AS serve

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

```

## frontend/index.html

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sindicância — Grafo de Investigação</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>

```

## frontend/nginx.conf

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # SPA: qualquer rota sem arquivo estático correspondente cai no
    # index.html (roteamento no lado do cliente).
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy para a API FastAPI. Fora do Vite dev server (que só faz proxy em
    # desenvolvimento — ver vite.config.js), é o nginx que assume esse papel
    # em produção. Assume um serviço/host chamado "backend" na porta 8000
    # (ex.: um serviço `backend` no mesmo docker-compose) — ajuste conforme
    # o nome real do serviço da API no seu ambiente.
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}

```

## frontend/package.json

```json
{
  "name": "sindicancia-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "cytoscape": "^3.30.2",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.13",
    "vite": "^5.4.6"
  }
}

```

## frontend/postcss.config.js

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}

```

## frontend/src/App.jsx

```jsx
import PaginaPrincipal from './pages/PaginaPrincipal.jsx'

export default function App() {
  return <PaginaPrincipal />
}

```

## frontend/src/api/client.js

```javascript
// Cliente HTTP para a API FastAPI. Usa caminhos relativos (/api/...): em
// desenvolvimento o Vite faz o proxy para http://localhost:8000 (ver
// vite.config.js); em produção, assume-se que backend e frontend ficam
// atrás do mesmo domínio/reverse proxy.

const BASE_URL = '/api'

async function requisitar(caminho, opcoes) {
  const resposta = await fetch(`${BASE_URL}${caminho}`, opcoes)
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null)
    throw new Error(corpo?.detail ?? `Erro ${resposta.status} ao acessar ${caminho}`)
  }
  return resposta.json()
}

/**
 * GET /api/casos?limit=&offset= — lista paginada.
 * Retorna { casos, total, limit, offset }.
 */
export function listarCasos(limit = 50, offset = 0) {
  return requisitar(`/casos?limit=${limit}&offset=${offset}`)
}

/** POST /api/casos — cria um novo caso. */
export function criarCaso(dados) {
  return requisitar('/casos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  })
}

/** GET /api/grafo/vinculos/{entidadeId}?profundidade=1|2 */
export function obterVinculos(entidadeId, profundidade = 2) {
  return requisitar(`/grafo/vinculos/${encodeURIComponent(entidadeId)}?profundidade=${profundidade}`)
}

```

## frontend/src/components/GrafoEntidades.jsx

```jsx
import { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'
import { corPorGrauCerteza, statusPorGrauCerteza } from '../utils/fuzzy.js'

const LARGURA_MINIMA_ARESTA = 1
const LARGURA_MAXIMA_ARESTA = 8

function larguraAresta(grau) {
  const valor = typeof grau === 'number' ? grau : 0
  return LARGURA_MINIMA_ARESTA + valor * (LARGURA_MAXIMA_ARESTA - LARGURA_MINIMA_ARESTA)
}

/** Converte {nos, arestas} (formato de GET /api/grafo/vinculos/{id}) em
 * elementos do Cytoscape. */
function construirElementos(nos, arestas) {
  const elementosNos = nos.map((no) => ({
    data: {
      ...no,
      id: no.id,
      label: no.nome ?? no.id,
      grau: no.nivel_certeza_fuzzy,
      status: statusPorGrauCerteza(no.nivel_certeza_fuzzy),
    },
  }))

  const elementosArestas = arestas.map((aresta) => ({
    data: {
      ...aresta,
      id: aresta.id ?? `${aresta.origem_id}->${aresta.destino_id}`,
      source: aresta.origem_id,
      target: aresta.destino_id,
      label: aresta.tipo,
      grau: aresta.grau_pertinencia_fuzzy,
    },
  }))

  return [...elementosNos, ...elementosArestas]
}

const FOLHA_DE_ESTILO = [
  {
    selector: 'node',
    style: {
      'background-color': (ele) => corPorGrauCerteza(ele.data('grau')),
      label: 'data(label)',
      'font-size': 10,
      color: '#1e293b',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': 4,
      width: 34,
      height: 34,
      'border-width': 2,
      'border-color': '#ffffff',
    },
  },
  {
    selector: 'edge',
    style: {
      width: (ele) => larguraAresta(ele.data('grau')),
      'line-color': '#94a3b8',
      'target-arrow-color': '#94a3b8',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      label: 'data(label)',
      'font-size': 8,
      color: '#475569',
      'text-rotation': 'autorotate',
      'text-background-color': '#f8fafc',
      'text-background-opacity': 0.8,
      'text-background-padding': 1,
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-color': '#2563eb',
      'border-width': 4,
    },
  },
]

const LAYOUT_FORCE_DIRECTED = {
  // 'cose' (Compound Spring Embedder) é o layout force-directed nativo do
  // Cytoscape.js — não requer nenhuma extensão adicional.
  name: 'cose',
  animate: true,
  randomize: true,
  idealEdgeLength: 120,
  nodeRepulsion: 9000,
  fit: true,
  padding: 30,
}

/**
 * Grafo interativo de entidades e relações, renderizado com Cytoscape.js.
 *
 * Props:
 *   - nos: [{ id, tipo, nome, nivel_certeza_fuzzy, ... }]
 *   - arestas: [{ id, origem_id, destino_id, tipo, grau_pertinencia_fuzzy, ... }]
 *   - onSelecionarEntidade(dadosDoNo | null): chamado ao clicar num nó
 *     (ou null ao clicar no fundo, para limpar a seleção).
 */
export default function GrafoEntidades({ nos, arestas, onSelecionarEntidade, className }) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)

  // Guarda o callback mais recente numa ref para que o efeito de
  // criação/destruição do grafo abaixo não precise re-executar (e
  // recalcular o layout do zero) toda vez que o componente pai passar uma
  // nova identidade de função.
  const onSelecionarEntidadeRef = useRef(onSelecionarEntidade)
  useEffect(() => {
    onSelecionarEntidadeRef.current = onSelecionarEntidade
  }, [onSelecionarEntidade])

  useEffect(() => {
    if (!containerRef.current) return undefined

    const cy = cytoscape({
      container: containerRef.current,
      elements: construirElementos(nos, arestas),
      style: FOLHA_DE_ESTILO,
      layout: LAYOUT_FORCE_DIRECTED,
      wheelSensitivity: 0.2,
    })

    cy.on('tap', 'node', (evento) => {
      onSelecionarEntidadeRef.current?.(evento.target.data())
    })

    cy.on('tap', (evento) => {
      if (evento.target === cy) {
        onSelecionarEntidadeRef.current?.(null)
      }
    })

    cyRef.current = cy

    return () => {
      cy.destroy()
      cyRef.current = null
    }
  }, [nos, arestas])

  return <div ref={containerRef} className={className ?? 'h-full w-full'} />
}

```

## frontend/src/components/ListaCasos.jsx

```jsx
const ESTILO_STATUS = {
  aberto: 'bg-amber-100 text-amber-700',
  em_andamento: 'bg-blue-100 text-blue-700',
  encerrado: 'bg-slate-200 text-slate-600',
}

/**
 * Lista lateral de casos.
 *
 * Props:
 *   - casos: [{ id, tema, subcategoria, status, ... }]
 *   - carregando: bool
 *   - casoSelecionadoId: string | null
 *   - onSelecionarCaso(caso): void
 */
export default function ListaCasos({ casos, carregando, casoSelecionadoId, onSelecionarCaso }) {
  return (
    <div className="p-3">
      <h2 className="mb-3 px-1 text-xs font-semibold uppercase tracking-wide text-slate-400">Casos</h2>

      {carregando && <p className="px-1 text-sm text-slate-400">Carregando casos…</p>}

      {!carregando && casos.length === 0 && <p className="px-1 text-sm text-slate-400">Nenhum caso encontrado.</p>}

      <ul className="space-y-1">
        {casos.map((caso) => {
          const selecionado = caso.id === casoSelecionadoId
          return (
            <li key={caso.id}>
              <button
                type="button"
                onClick={() => onSelecionarCaso(caso)}
                className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                  selecionado ? 'bg-blue-50 text-blue-700' : 'text-slate-700 hover:bg-slate-100'
                }`}
              >
                <p className="truncate font-medium">{caso.tema}</p>
                {caso.subcategoria && <p className="truncate text-xs text-slate-400">{caso.subcategoria}</p>}
                {caso.status && (
                  <span
                    className={`mt-1 inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${
                      ESTILO_STATUS[caso.status] ?? 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {caso.status}
                  </span>
                )}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

```

## frontend/src/components/PainelEntidade.jsx

```jsx
import { corPorStatus, statusPorGrauCerteza } from '../utils/fuzzy.js'

function Campo({ rotulo, valor }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-slate-400">{rotulo}</dt>
      <dd className="truncate font-medium text-slate-700" title={typeof valor === 'string' ? valor : undefined}>
        {valor === null || valor === undefined || valor === '' ? '—' : valor}
      </dd>
    </div>
  )
}

/**
 * Painel lateral com os detalhes da entidade selecionada no grafo.
 *
 * Props:
 *   - entidade: os `data()` do nó do Cytoscape.js selecionado, ou null.
 */
export default function PainelEntidade({ entidade }) {
  if (!entidade) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-sm text-slate-400">
        Selecione uma entidade no grafo para ver os detalhes.
      </div>
    )
  }

  const grau = entidade.grau ?? entidade.nivel_certeza_fuzzy
  const status = entidade.status ?? statusPorGrauCerteza(grau)
  const cor = corPorStatus(status)

  return (
    <div className="space-y-4 p-4">
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Entidade selecionada</h2>
        <p className="mt-1 text-lg font-semibold text-slate-900">{entidade.nome ?? entidade.label ?? entidade.id}</p>
      </div>

      <dl className="space-y-2 text-sm">
        <Campo rotulo="ID" valor={entidade.id} />
        <Campo rotulo="Tipo" valor={entidade.tipo} />
        <Campo rotulo="Caso" valor={entidade.caso_id} />

        <div className="flex items-center justify-between gap-3">
          <dt className="text-slate-400">Status (grau fuzzy)</dt>
          <dd className="flex items-center gap-2 font-medium" style={{ color: cor }}>
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: cor }} />
            {status}
          </dd>
        </div>

        <Campo rotulo="Nível de certeza" valor={typeof grau === 'number' ? grau.toFixed(2) : null} />

        {'e_seed' in entidade && <Campo rotulo="Entidade semente" valor={entidade.e_seed ? 'Sim' : 'Não'} />}
      </dl>
    </div>
  )
}

```

## frontend/src/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html,
body,
#root {
  height: 100%;
}

```

## frontend/src/main.jsx

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

```

## frontend/src/pages/PaginaPrincipal.jsx

```jsx
import { useCallback, useEffect, useState } from 'react'
import GrafoEntidades from '../components/GrafoEntidades.jsx'
import ListaCasos from '../components/ListaCasos.jsx'
import PainelEntidade from '../components/PainelEntidade.jsx'
import { listarCasos, obterVinculos } from '../api/client.js'
import { CORES_POR_STATUS } from '../utils/fuzzy.js'

function LegendaStatus() {
  return (
    <div className="absolute bottom-3 left-3 z-10 rounded-md border border-slate-200 bg-white/90 p-2 text-xs shadow-sm backdrop-blur">
      <p className="mb-1 font-semibold text-slate-500">Grau de certeza</p>
      <ul className="space-y-0.5">
        {Object.entries(CORES_POR_STATUS).map(([status, cor]) => (
          <li key={status} className="flex items-center gap-1.5 text-slate-600">
            <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: cor }} />
            {status}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function PaginaPrincipal() {
  const [casos, setCasos] = useState([])
  const [carregandoCasos, setCarregandoCasos] = useState(true)
  const [casoSelecionado, setCasoSelecionado] = useState(null)

  const [entidadeIdConsulta, setEntidadeIdConsulta] = useState('')
  const [grafo, setGrafo] = useState({ nos: [], arestas: [] })
  const [carregandoGrafo, setCarregandoGrafo] = useState(false)
  const [entidadeSelecionada, setEntidadeSelecionada] = useState(null)

  const [erro, setErro] = useState(null)

  useEffect(() => {
    let cancelado = false

    async function carregar() {
      try {
        const dados = await listarCasos()
        if (!cancelado) setCasos(dados.casos)
      } catch {
        if (!cancelado) setErro('Não foi possível carregar a lista de casos.')
      } finally {
        if (!cancelado) setCarregandoCasos(false)
      }
    }

    carregar()
    return () => {
      cancelado = true
    }
  }, [])

  const carregarVinculos = useCallback(async (entidadeId) => {
    if (!entidadeId) return

    setCarregandoGrafo(true)
    setErro(null)
    try {
      const dados = await obterVinculos(entidadeId)
      setGrafo({ nos: dados.nos, arestas: dados.arestas })
      setEntidadeSelecionada(null)
    } catch (erroRequisicao) {
      setErro(erroRequisicao.message || `Não foi possível carregar os vínculos de "${entidadeId}".`)
      setGrafo({ nos: [], arestas: [] })
    } finally {
      setCarregandoGrafo(false)
    }
  }, [])

  function aoSubmeterBusca(evento) {
    evento.preventDefault()
    carregarVinculos(entidadeIdConsulta.trim())
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900">
      <aside className="w-72 shrink-0 overflow-y-auto border-r border-slate-200 bg-white">
        <ListaCasos
          casos={casos}
          carregando={carregandoCasos}
          casoSelecionadoId={casoSelecionado?.id}
          onSelecionarCaso={setCasoSelecionado}
        />
      </aside>

      <main className="flex flex-1 flex-col">
        <header className="border-b border-slate-200 bg-white px-4 py-3">
          <form onSubmit={aoSubmeterBusca} className="flex items-center gap-2">
            <label htmlFor="entidade-id" className="whitespace-nowrap text-sm font-medium text-slate-600">
              ID da entidade central:
            </label>
            <input
              id="entidade-id"
              type="text"
              value={entidadeIdConsulta}
              onChange={(evento) => setEntidadeIdConsulta(evento.target.value)}
              placeholder="UUID da entidade"
              className="flex-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={carregandoGrafo || !entidadeIdConsulta.trim()}
              className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {carregandoGrafo ? 'Carregando…' : 'Ver vínculos'}
            </button>
          </form>
          {erro && <p className="mt-2 text-sm text-red-600">{erro}</p>}
        </header>

        <div className="relative flex-1">
          <GrafoEntidades
            nos={grafo.nos}
            arestas={grafo.arestas}
            onSelecionarEntidade={setEntidadeSelecionada}
            className="absolute inset-0"
          />
          {grafo.nos.length > 0 && <LegendaStatus />}
        </div>
      </main>

      <aside className="w-80 shrink-0 overflow-y-auto border-l border-slate-200 bg-white">
        <PainelEntidade entidade={entidadeSelecionada} />
      </aside>
    </div>
  )
}

```

## frontend/src/utils/fuzzy.js

```javascript
// Mapeamento de grau de certeza fuzzy -> status -> cor, espelhando as
// faixas usadas pelo motor de inferência fuzzy do backend
// (backend/app/fuzzy/engine.py: FAIXAS_STATUS) para que o grafo use a
// mesma semântica de cores em toda a aplicação.
//
// grau === null/undefined (sem dado) é tratado como "Lacuna", assim como o
// motor fuzzy trata a ausência de disparo de regras.

export const CORES_POR_STATUS = {
  Confirmado: '#16a34a', // verde
  'Indício Forte': '#65a30d', // verde-oliva
  'Indício Moderado': '#eab308', // amarelo
  Inferência: '#f97316', // laranja
  Lacuna: '#f43f5e', // vermelho (dado insuficiente/inconsistente)
  Descartado: '#dc2626', // vermelho
}

const COR_PADRAO = '#9ca3af' // cinza, para status desconhecido

/** Classifica um grau de certeza (0.0-1.0) num dos 6 status do motor fuzzy. */
export function statusPorGrauCerteza(grau) {
  if (grau === null || grau === undefined || Number.isNaN(grau)) return 'Lacuna'
  if (grau >= 0.85) return 'Confirmado'
  if (grau >= 0.65) return 'Indício Forte'
  if (grau >= 0.45) return 'Indício Moderado'
  if (grau >= 0.25) return 'Inferência'
  return 'Descartado'
}

export function corPorStatus(status) {
  return CORES_POR_STATUS[status] ?? COR_PADRAO
}

/** Atalho: grau de certeza -> cor, passando pela classificação de status. */
export function corPorGrauCerteza(grau) {
  return corPorStatus(statusPorGrauCerteza(grau))
}

```

## frontend/tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
}

```

## frontend/vite.config.js

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Encaminha /api/* para o backend FastAPI (uvicorn app.main:app --reload)
      // durante o desenvolvimento, evitando problemas de CORS.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

```

