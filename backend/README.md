# HUDSON S1 - Backend v0

Implementação enxuta e 100% local do núcleo do HUDSON: hash → roteamento de Estante →
cópia de custódia → OCR → indexação `tsvector` → busca. Sem login, RBAC, LGPD ou IA
(deixados para a camada 2, ver `docs/D5-roadmap-fases-codificacao.md`).

## Pré-requisitos de sistema

- PostgreSQL 15+
- Tesseract OCR (`tesseract-ocr` + pacote de idioma `por`)
- Poppler (`poppler-utils`) — necessário apenas para OCR de PDF escaneado via `pdf2image`

No CentOS 7 do servidor:

```bash
sudo yum install -y tesseract tesseract-langpack-por poppler-utils postgresql15-server
```

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # ajuste DATABASE_URL e STORAGE_ROOT
```

## Criar o schema

O schema já está versionado em `../specs/S2-schema.sql` (fonte única — não duplicar em migrations):

```bash
psql "$DATABASE_URL" -f ../specs/S2-schema.sql
```

## Rodar a API

```bash
uvicorn app.main:app --reload
```

- `GET /health`
- `GET /search?q=termo`
- `GET /items/{cota}`

## Importar um backlog

```bash
python -m scripts.import_cli --source "/caminho/da/origem" --wbs COD_EMPREENDIMENTO
```

Idempotente: rodar de novo sobre a mesma origem apenas gera eventos `deduplicacao` no
`custody_log`, nunca duplica o item. Cada arquivo é hasheado (SHA-256 em streaming) antes
de qualquer outra etapa — o hash é a identidade do item, nunca o nome do arquivo.

## Escopo v0 (o que fica de fora, de propósito)

- Sem NER / resolução de entidades / Chat Tradutor (precisam de LLM local — camada 2)
- Sem RBAC fino, LGPD, login/SSO — v0 roda em ambiente de confiança do backlog
- Sem migração para nuvem nem limpeza das origens — decisão adiada explicitamente
- `entities`, `relationships`, `declarations` existem no schema mas não são usadas pela v0
