# 🔌 ARQUITETURA DE INTEGRAÇÃO — DAI & KAN-SA
## HUDSON Data Warehouse v2.0 — Acesso via OpenVPN + API REST

**Especificação Técnica de Integração**

---

## 📌 METADADOS DO DOCUMENTO

| Campo | Valor |
|:---|:---|
| **Título** | Arquitetura de Integração Dai & Kan-sa com HUDSON |
| **Data** | 08 de Outubro de 2026 |
| **Versão** | 1.0 (Production) |
| **Público** | Equipe de IA (Dai, Kan-sa), Desenvolvedores, DevOps |
| **Status** | ✅ PRONTO PARA IMPLEMENTAÇÃO |
| **HDW Versão** | 2.0 (homologado) |
| **Ambiente** | Linux CentOS 7 @ 192.168.1.122 (Private Network) |
| **Acesso** | OpenVPN (O VPN) + API REST FastAPI |

---

## 🎯 VISÃO GERAL DA ARQUITETURA

```
┌─────────────────────────────────────────────────────────────┐
│                     AGENTES IA EXTERNOS                     │
│                   (Dai, Kan-sa, Robôs)                       │
│                                                              │
│  ┌──────────────────┐              ┌──────────────────┐    │
│  │       Dai        │              │     Kan-sa       │    │
│  │  (Maestro Geral) │              │ (Especialista)   │    │
│  └────────┬─────────┘              └────────┬─────────┘    │
└───────────┼──────────────────────────────────┼──────────────┘
            │                                  │
            │   Acesso Remoto via OpenVPN     │
            │   (Criptografia TLS + mTLS)     │
            │                                  │
┌───────────┼──────────────────────────────────┼──────────────┐
│           │                                  │              │
│  ┌────────▼─────────────────────────────────▼──────┐       │
│  │         Rede Corporativa SUGOI (Privada)       │       │
│  │       192.168.1.0/24 (OpenVPN Gateway)         │       │
│  │              87.102.137.206:1194               │       │
│  └────────┬─────────────────────────────────┬─────┘       │
│           │                                  │              │
│  ┌────────▼──────────────────────────────────▼────┐       │
│  │   HUDSON HDW — Host Linux CentOS 7 (192.168.1.122)  │
│  │                                                  │       │
│  │  ┌──────────────────────────────────────────┐  │       │
│  │  │  FastAPI Server (Uvicorn)                │  │       │
│  │  │  :8000/health                            │  │       │
│  │  │  :8000/api/v1/items/ronda/{ronda_id}   │  │       │
│  │  │  :8000/api/v1/items/search/fuzzy        │  │       │
│  │  │  :8000/api/v1/items/metadados/{item_id}│  │       │
│  │  └──────────────────────────────────────────┘  │       │
│  │                    ↓                            │       │
│  │  ┌──────────────────────────────────────────┐  │       │
│  │  │  SQLAlchemy ORM + Psycopg2              │  │       │
│  │  │  (Abstração SQL + Connection Pooling)   │  │       │
│  │  └──────────────────────────────────────────┘  │       │
│  │                    ↓                            │       │
│  │  ┌──────────────────────────────────────────┐  │       │
│  │  │  PostgreSQL 18.6 (Hudson Schema)        │  │       │
│  │  │  - hudson.items (com metadados v2.0)   │  │       │
│  │  │  - hudson.custody_log (append-only)    │  │       │
│  │  │  - hudson.estant_types (6 estantes)    │  │       │
│  │  │  - Índices: ronda_id, nome_orig, etc   │  │       │
│  │  └──────────────────────────────────────────┘  │       │
│  │                                                  │       │
│  │  🔒 Firewall: Apenas :8000 + SSH para admin   │       │
│  │  🔐 Nenhuma porta pública exposta             │       │
│  └──────────────────────────────────────────────┘       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🔐 CAMADA 1: CONECTIVIDADE VIA OPENVPN

### **1.1 Configuração de VPN (Já em Lugar)**

**Arquivo de Configuração:** `/home/hudson/.ovpn/hudson_vpn.ovpn`

```ini
# hudson_vpn.ovpn (Perfil de Aplicação)

client
proto udp
dev tun
remote 87.102.137.206 1194

# Criptografia
cipher AES-256-CBC
auth SHA256

# Certificados PKI
<ca>
-----BEGIN CERTIFICATE-----
... (CA certificate root) ...
-----END CERTIFICATE-----
</ca>

<cert>
-----BEGIN CERTIFICATE-----
... (Client certificate) ...
-----END CERTIFICATE-----
</cert>

<key>
-----BEGIN PRIVATE KEY-----
... (Private key) ...
-----END PRIVATE KEY-----
</key>

# Roteamento
route 192.168.1.0 255.255.255.0

# Resolução de DNS
resolv-retry infinite
```

### **1.2 Setup para Dai & Kan-sa**

**Cenário A: Agentes Rodando em Linux/Docker (Oracle Cloud)**

```bash
# No container/VM dos agentes:

# 1. Instalar OpenVPN client
apt-get install openvpn

# 2. Copiar perfil (via gestão de secrets segura)
# Exemplo com Kubernetes Secrets:
kubectl create secret generic hudson-vpn --from-file=hudson_vpn.ovpn

# 3. Montar como sidecar container
# docker-compose.yml
services:
  dai-agent:
    image: dai:latest
    depends_on:
      - openvpn-client
    
  openvpn-client:
    image: kylemanna/openvpn-client:latest
    cap_add:
      - NET_ADMIN
    volumes:
      - ./hudson_vpn.ovpn:/vpn/hudson.ovpn:ro
    restart: always
    command: openvpn --config /vpn/hudson.ovpn
```

**Cenário B: Agentes em Windows (Estação de Trabalho)**

```
1. Download: OpenVPN GUI (https://openvpn.net/download-open-vpn/)
2. Instalar
3. Copiar hudson_vpn.ovpn para C:\Users\<username>\OpenVPN\config\
4. Clicar em "Connect"
5. ✅ Conectado → 192.168.1.122 acessível
```

### **1.3 Validação de Conectividade**

```bash
# Dentro do agente (após VPN conectada):

# Verificar IP de tunelamento
ifconfig tun0
# Esperado: inet 10.8.0.x (ou similar OpenVPN range)

# Testar ping ao HDW
ping 192.168.1.122
# Esperado: 64 bytes from 192.168.1.122: icmp_seq=1 ttl=64 time=45.2ms

# Testar acesso à API
curl -s http://192.168.1.122:8000/health
# Esperado: {"status":"ok"}

# Testar conexão ao PostgreSQL (opcional)
psql -h 192.168.1.122 -U hudson -d sugoi -c "SELECT version();"
# Esperado: PostgreSQL 18.6 on ...
```

---

## 🌐 CAMADA 2: API REST FASTAPI

### **2.1 Estrutura de Endpoints**

**Base URL:** `http://192.168.1.122:8000/api/v1`

#### **Endpoint 1: Health Check**

```
GET /health

Descrição: Verifica se API está operacional

Response (200 OK):
{
  "status": "ok",
  "timestamp": "2026-10-08T19:35:22Z",
  "database": "connected",
  "version": "2.0.0"
}

Latência SLA: <50ms
```

#### **Endpoint 2: Listar Itens por Ronda**

```
GET /items/ronda/{ronda_id}

Parâmetros:
  - ronda_id (path): Identificador da ronda (ex: RONDA-2026-10-08)
  - limit (query, default=100): Máximo de registros a retornar
  - offset (query, default=0): Paginação
  - obra_wbs (query, optional): Filtrar por obra

Descrição: Recupera todos os itens de uma ronda específica

Response (200 OK):
{
  "ronda_id": "RONDA-2026-10-08",
  "total_itens": 250,
  "pagina_atual": 0,
  "itens_por_pagina": 100,
  "itens": [
    {
      "item_id": "uuid-1234-5678",
      "nome_arquivo_original": "contrato_assinado.pdf",
      "caminho_origem": "/obras/OB-2026-001/contratos/contrato_assinado.pdf",
      "extensao_original": ".pdf",
      "tamanho_bytes": 2048576,
      "mtime_origem": "2026-09-15T14:22:31Z",
      "ronda_id": "RONDA-2026-10-08",
      "usuario_captura": "hudson-admin",
      "maquina_origem": "server-sugoi-01",
      "estante": "document_text",
      "status_desbloqueio": "desbloqueado",
      "metodo_desbloqueio": "pdfplumber",
      "obra_wbs": "OB-2026-001",
      "data_captura": "2026-10-08T18:35:22Z",
      "cota_hudson": "document_text-OB-2026-001-2026-464468e2"
    },
    { ... }
  ]
}

Latência SLA: <200ms (P95)
```

#### **Endpoint 3: Busca Fuzzy por Nome**

```
GET /items/search/fuzzy

Parâmetros:
  - termo (query, required): Termo de busca (ex: "contrato 2023")
  - obra_wbs (query, optional): Filtrar por obra
  - ronda_id (query, optional): Filtrar por ronda
  - min_score (query, default=80): Score mínimo de similaridade (0-100)
  - limit (query, default=50): Máximo de resultados

Descrição: Busca fuzzy em nome_arquivo_original usando RapidFuzz

Response (200 OK):
{
  "termo_busca": "contrato 2023",
  "resultados_encontrados": 3,
  "itens": [
    {
      "item_id": "uuid-1111",
      "nome_arquivo_original": "contrato_2023_assinado.pdf",
      "score_similaridade": 95,
      "obra_wbs": "OB-2026-001",
      "ronda_id": "RONDA-2026-10-08",
      "estante": "document_text",
      "tamanho_bytes": 1048576,
      "data_captura": "2026-10-08T18:35:22Z"
    },
    {
      "item_id": "uuid-2222",
      "nome_arquivo_original": "contrato_2023_rascunho.pdf",
      "score_similaridade": 92,
      ...
    },
    {
      "item_id": "uuid-3333",
      "nome_arquivo_original": "contrato_2023_anterior.pdf",
      "score_similaridade": 88,
      ...
    }
  ]
}

Latência SLA: <300ms (P95, dependendo do tamanho de hudson.items)
```

#### **Endpoint 4: Recuperar Metadados Completos**

```
GET /items/{item_id}/metadados

Parâmetros:
  - item_id (path): UUID do item

Descrição: Retorna metadados completos de um arquivo específico

Response (200 OK):
{
  "item_id": "uuid-1234-5678",
  "identidade": {
    "nome_arquivo_original": "contrato_assinado.pdf",
    "extensao_original": ".pdf",
    "tamanho_bytes": 2048576
  },
  "origem": {
    "caminho_completo": "/obras/OB-2026-001/contratos/contrato_assinado.pdf",
    "usuario_captura": "hudson-admin",
    "maquina_origem": "server-sugoi-01",
    "data_criacao_original": "2026-09-10T08:00:00Z",
    "data_modificacao_original": "2026-09-15T14:22:31Z"
  },
  "custódia": {
    "data_captura_hudson": "2026-10-08T18:35:22Z",
    "ronda_id": "RONDA-2026-10-08",
    "obra_wbs": "OB-2026-001",
    "cota_hudson": "document_text-OB-2026-001-2026-464468e2"
  },
  "desbloqueio": {
    "status_desbloqueio": "desbloqueado",
    "metodo_desbloqueio": "pdfplumber",
    "data_desbloqueio": "2026-10-08T18:35:23Z",
    "usuario_desbloqueio": "importer_v2"
  },
  "indexacao": {
    "estante": "document_text",
    "full_text_indexado": true,
    "tokens_extraidos": 1250
  }
}

Latência SLA: <100ms
```

#### **Endpoint 5: Recuperar Estatísticas de Ronda**

```
GET /rodas/{ronda_id}/stats

Parâmetros:
  - ronda_id (path): Identificador da ronda

Descrição: Estatísticas agregadas de uma ronda

Response (200 OK):
{
  "ronda_id": "RONDA-2026-10-08",
  "data_ronda": "2026-10-08T18:00:00Z",
  "status_ronda": "concluida",
  "estatisticas": {
    "total_arquivos": 2500,
    "total_sucesso": 2487,
    "total_erros": 10,
    "total_bloqueados": 3,
    "tempo_total_segundos": 1847,
    "taxa_sucesso_percentual": 99.48
  },
  "por_estante": {
    "document_text": 1250,
    "structured_data": 800,
    "image": 350,
    "audio_video": 150,
    "communication": 37,
    "engineering_drawings": 0,
    "nao_classificado": 13
  },
  "por_obra": {
    "OB-2026-001": 500,
    "OB-2026-002": 480,
    "OB-2026-003": 520,
    ...
  }
}

Latência SLA: <150ms
```

---

## 🔒 CAMADA 3: AUTENTICAÇÃO & SEGURANÇA

### **3.1 Mecanismo de Autenticação**

**Opção A: API Key (Simples, Recomendado para v1.0)**

```
Cada agente (Dai, Kan-sa) recebe uma chave API única:

Dai:     X-API-Key: hudson-dai-key-9876543210abcdef
Kan-sa:  X-API-Key: hudson-kansa-key-fedcba0987654321

Header obrigatório em cada request:
GET /api/v1/items/ronda/RONDA-2026-10-08 \
  -H "X-API-Key: hudson-dai-key-9876543210abcdef"

Geração de Chaves:
$ python -c "import secrets; print(secrets.token_urlsafe(32))"
# Armazenar em: /home/hudson/.hudson/api_keys.json (permissões 0600)
```

**Opção B: mTLS (Forte, Para v2.0)**

```
Cada agente tem certificado X.509:

Dai:     /etc/hudson/certs/dai-client.crt + dai-client.key
Kan-sa:  /etc/hudson/certs/kansa-client.crt + kansa-client.key

Request:
curl -s --cert dai-client.crt --key dai-client.key \
  https://192.168.1.122:8443/api/v1/items/ronda/...

Validação no servidor:
- CA root: /etc/hudson/certs/ca.crt
- CN do certificado deve estar na whitelist
```

### **3.2 Rate Limiting**

```
Por API Key (por minuto):

Dai:    2000 requests/min (alta capacidade)
Kan-sa:  500 requests/min (uso moderado)

Resposta ao atingir limite:
HTTP 429 Too Many Requests

{
  "error": "rate_limit_exceeded",
  "retry_after_seconds": 60,
  "limit": 2000,
  "used": 2001,
  "reset_at": "2026-10-08T19:36:22Z"
}
```

### **3.3 Validações de Segurança**

```
✅ Cada request valida:
  1. API Key presente e válida
  2. Origem IP está na whitelist (IP da VPN + Docker network)
  3. Content-Type é JSON (se POST/PUT)
  4. Payload não ultrapassa 10MB
  5. SQL injection: Todas queries via SQLAlchemy ORM (parameterized)
  
✅ Logging:
  - Todos os requests registrados em /var/log/hudson/api.log
  - Tenta de autenticação falhadas em /var/log/hudson/auth.log
  - Sem logging de dados sensíveis (senhas, chaves)
```

---

## 💻 CAMADA 4: IMPLEMENTAÇÃO NO CÓDIGO

### **4.1 Arquivo de Configuração (`config.py`)**

```python
# app/config.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Banco de Dados
    DATABASE_URL: str = "postgresql://hudson:pass@sugoi-postgres:5432/sugoi"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    
    # CORS (Cross-Origin Resource Sharing)
    CORS_ORIGINS: list = [
        "http://192.168.1.122:8000",
        "http://localhost:8000"
    ]
    
    # Rate Limiting
    RATE_LIMITS: dict = {
        "hudson-dai-key-9876543210abcdef": 2000,
        "hudson-kansa-key-fedcba0987654321": 500,
    }
    
    # RapidFuzz Threshold
    FUZZY_MIN_SCORE: int = 80
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/var/log/hudson/api.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### **4.2 Rotas da API (`routers/items.py`)**

```python
# app/routers/items.py

from fastapi import APIRouter, HTTPException, Depends, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from rapidfuzz import fuzz
from app.database import get_db
from app.models import Item
from app.config import settings
from app.security import verify_api_key

router = APIRouter(prefix="/api/v1", tags=["items"])

# Middleware de autenticação
async def api_key_header(x_api_key: str = Header(...)):
    if not verify_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

# ================================================================
# GET /items/ronda/{ronda_id}
# ================================================================

@router.get("/items/ronda/{ronda_id}")
async def listar_itens_por_ronda(
    ronda_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    obra_wbs: Optional[str] = None,
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db),
):
    """
    Retorna todos os itens de uma ronda específica.
    
    Args:
        ronda_id: ID da ronda (ex: RONDA-2026-10-08)
        limit: Máximo de registros (default: 100, max: 1000)
        offset: Paginação (default: 0)
        obra_wbs: Filtro opcional por obra
    
    Returns:
        dict com lista de itens + metadados
    """
    
    query = db.query(Item).filter(Item.ronda_id == ronda_id)
    
    if obra_wbs:
        query = query.filter(Item.obra_wbs == obra_wbs)
    
    total = query.count()
    itens = query.offset(offset).limit(limit).all()
    
    return {
        "ronda_id": ronda_id,
        "total_itens": total,
        "pagina_atual": offset // limit,
        "itens_por_pagina": limit,
        "itens": [
            {
                "item_id": str(item.id),
                "nome_arquivo_original": item.nome_arquivo_original,
                "caminho_origem": item.caminho_origem,
                "extensao_original": item.extensao_original,
                "tamanho_bytes": item.tamanho_bytes,
                "mtime_origem": item.mtime_origem,
                "ronda_id": item.ronda_id,
                "usuario_captura": item.usuario_captura,
                "maquina_origem": item.maquina_origem,
                "estante": item.estante,
                "status_desbloqueio": item.status_desbloqueio,
                "obra_wbs": item.obra_wbs,
                "data_captura": item.data_captura,
                "cota_hudson": item.cota_hudson,
            }
            for item in itens
        ]
    }

# ================================================================
# GET /items/search/fuzzy
# ================================================================

@router.get("/items/search/fuzzy")
async def buscar_fuzzy(
    termo: str = Query(..., min_length=2, max_length=100),
    obra_wbs: Optional[str] = None,
    ronda_id: Optional[str] = None,
    min_score: int = Query(80, ge=0, le=100),
    limit: int = Query(50, ge=1, le=500),
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db),
):
    """
    Busca fuzzy em nome_arquivo_original usando RapidFuzz.
    
    Args:
        termo: Termo de busca (ex: "contrato 2023")
        obra_wbs: Filtro opcional
        ronda_id: Filtro opcional
        min_score: Score mínimo (0-100, default: 80)
        limit: Máximo de resultados (default: 50)
    
    Returns:
        list de itens com score de similaridade
    """
    
    # Query base
    query = db.query(Item)
    
    if obra_wbs:
        query = query.filter(Item.obra_wbs == obra_wbs)
    if ronda_id:
        query = query.filter(Item.ronda_id == ronda_id)
    
    # Buscar todos os itens e fazer fuzzy matching em memória
    # (Para datasets maiores, usar full-text search do PostgreSQL)
    todos_itens = query.all()
    
    resultados = []
    for item in todos_itens:
        score = fuzz.token_sort_ratio(
            termo.lower(),
            (item.nome_arquivo_original or "").lower()
        )
        
        if score >= min_score:
            resultados.append({
                "item_id": str(item.id),
                "nome_arquivo_original": item.nome_arquivo_original,
                "score_similaridade": score,
                "obra_wbs": item.obra_wbs,
                "ronda_id": item.ronda_id,
                "estante": item.estante,
                "tamanho_bytes": item.tamanho_bytes,
                "data_captura": item.data_captura,
            })
    
    # Ordenar por score (descendente) e limitar
    resultados.sort(key=lambda x: x["score_similaridade"], reverse=True)
    resultados = resultados[:limit]
    
    return {
        "termo_busca": termo,
        "resultados_encontrados": len(resultados),
        "itens": resultados
    }

# ================================================================
# GET /items/{item_id}/metadados
# ================================================================

@router.get("/items/{item_id}/metadados")
async def recuperar_metadados(
    item_id: str,
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db),
):
    """
    Retorna metadados completos de um arquivo.
    
    Args:
        item_id: UUID do item
    
    Returns:
        dict com metadados organizados por categoria
    """
    
    item = db.query(Item).filter(Item.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {
        "item_id": str(item.id),
        "identidade": {
            "nome_arquivo_original": item.nome_arquivo_original,
            "extensao_original": item.extensao_original,
            "tamanho_bytes": item.tamanho_bytes,
        },
        "origem": {
            "caminho_completo": item.caminho_origem,
            "usuario_captura": item.usuario_captura,
            "maquina_origem": item.maquina_origem,
            "data_criacao_original": item.data_criacao_original,
            "data_modificacao_original": item.mtime_origem,
        },
        "custódia": {
            "data_captura_hudson": item.data_captura,
            "ronda_id": item.ronda_id,
            "obra_wbs": item.obra_wbs,
            "cota_hudson": item.cota_hudson,
        },
        "desbloqueio": {
            "status_desbloqueio": item.status_desbloqueio,
            "metodo_desbloqueio": item.metodo_desbloqueio,
            "data_desbloqueio": item.data_desbloqueio,
            "usuario_desbloqueio": item.usuario_desbloqueio,
        },
        "indexacao": {
            "estante": item.estante,
            "full_text_indexado": item.full_text_searchable is not None,
            "tokens_extraidos": len((item.full_text_searchable or "").split()),
        }
    }

# ================================================================
# GET /rodas/{ronda_id}/stats
# ================================================================

@router.get("/rodas/{ronda_id}/stats")
async def stats_ronda(
    ronda_id: str,
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db),
):
    """
    Retorna estatísticas de uma ronda.
    """
    
    itens = db.query(Item).filter(Item.ronda_id == ronda_id).all()
    
    if not itens:
        raise HTTPException(status_code=404, detail="Ronda not found")
    
    # Contar por estante
    por_estante = {}
    for item in itens:
        estante = item.estante or "nao_classificado"
        por_estante[estante] = por_estante.get(estante, 0) + 1
    
    # Contar por obra
    por_obra = {}
    for item in itens:
        obra = item.obra_wbs or "desconhecida"
        por_obra[obra] = por_obra.get(obra, 0) + 1
    
    total = len(itens)
    sucesso = len([i for i in itens if i.status_desbloqueio != "bloqueado_permanente"])
    
    return {
        "ronda_id": ronda_id,
        "data_ronda": itens[0].data_captura if itens else None,
        "status_ronda": "concluida",
        "estatisticas": {
            "total_arquivos": total,
            "total_sucesso": sucesso,
            "total_erros": total - sucesso,
            "taxa_sucesso_percentual": round(sucesso / total * 100, 2) if total > 0 else 0,
        },
        "por_estante": por_estante,
        "por_obra": por_obra,
    }
```

---

## 📱 CAMADA 5: EXEMPLOS DE USO (Dai & Kan-sa)

### **Exemplo 1: Dai Recuperar Todos os Itens de uma Ronda**

```python
# agente_dai.py

import requests
from typing import List, Dict

class AgenteDai:
    def __init__(self, api_key: str, hudson_url: str = "http://192.168.1.122:8000"):
        self.api_key = api_key
        self.hudson_url = hudson_url
        self.headers = {"X-API-Key": api_key}
    
    def recuperar_ronda(self, ronda_id: str, obra_wbs: str = None) -> List[Dict]:
        """Recupera todos os itens de uma ronda."""
        
        url = f"{self.hudson_url}/api/v1/items/ronda/{ronda_id}"
        params = {}
        if obra_wbs:
            params["obra_wbs"] = obra_wbs
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"📊 Ronda: {ronda_id}")
        print(f"   Total de itens: {data['total_itens']}")
        print(f"   Itens nesta página: {len(data['itens'])}")
        
        for item in data['itens']:
            print(f"   - {item['nome_arquivo_original']} ({item['estante']})")
        
        return data['itens']

# Uso
dai = AgenteDai(api_key="hudson-dai-key-9876543210abcdef")
itens = dai.recuperar_ronda(
    ronda_id="RONDA-2026-10-08",
    obra_wbs="OB-2026-001"
)
```

### **Exemplo 2: Kan-sa Busca Fuzzy por Contrato**

```python
# agente_kansa.py

import requests
from typing import List, Dict

class AgenteKansa:
    def __init__(self, api_key: str, hudson_url: str = "http://192.168.1.122:8000"):
        self.api_key = api_key
        self.hudson_url = hudson_url
        self.headers = {"X-API-Key": api_key}
    
    def buscar_fuzzy(
        self, 
        termo: str, 
        obra_wbs: str = None, 
        min_score: int = 85
    ) -> List[Dict]:
        """Busca fuzzy por nome de arquivo."""
        
        url = f"{self.hudson_url}/api/v1/items/search/fuzzy"
        params = {
            "termo": termo,
            "min_score": min_score,
        }
        if obra_wbs:
            params["obra_wbs"] = obra_wbs
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"🔍 Busca por: '{termo}'")
        print(f"   Resultados encontrados: {data['resultados_encontrados']}")
        
        for item in data['itens']:
            score = item['score_similaridade']
            print(f"   - {item['nome_arquivo_original']:<40} ({score}% match)")
        
        return data['itens']
    
    def recuperar_metadados(self, item_id: str) -> Dict:
        """Recupera metadados completos de um item."""
        
        url = f"{self.hudson_url}/api/v1/items/{item_id}/metadados"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        metadados = response.json()
        
        print(f"📄 Metadados: {metadados['identidade']['nome_arquivo_original']}")
        print(f"   Tamanho: {metadados['identidade']['tamanho_bytes']} bytes")
        print(f"   Origem: {metadados['origem']['usuario_captura']} @ {metadados['origem']['maquina_origem']}")
        print(f"   Status desbloqueio: {metadados['desbloqueio']['status_desbloqueio']}")
        
        return metadados

# Uso
kansa = AgenteKansa(api_key="hudson-kansa-key-fedcba0987654321")

# Busca fuzzy
resultados = kansa.buscar_fuzzy(
    termo="contrato 2023",
    obra_wbs="OB-2026-001",
    min_score=85
)

# Recuperar metadados do primeiro resultado
if resultados:
    primeiro_item = resultados[0]
    metadados = kansa.recuperar_metadados(primeiro_item['item_id'])
```

### **Exemplo 3: Integração com LangGraph (Cadeia Multi-Agente)**

```python
# langgraph_integration.py

from langgraph.graph import StateGraph, END
from typing import Dict, List
import requests

class HudsonClient:
    """Cliente para HUDSON API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
        self.base_url = "http://192.168.1.122:8000/api/v1"
    
    def buscar_ronda(self, ronda_id: str) -> Dict:
        """Busca uma ronda completa."""
        response = requests.get(
            f"{self.base_url}/items/ronda/{ronda_id}",
            headers=self.headers
        )
        return response.json()
    
    def buscar_fuzzy(self, termo: str, min_score: int = 80) -> List[Dict]:
        """Busca fuzzy."""
        response = requests.get(
            f"{self.base_url}/items/search/fuzzy",
            headers=self.headers,
            params={"termo": termo, "min_score": min_score}
        )
        return response.json()["itens"]

# Estado do grafo
class EstadoPipeline(Dict):
    ronda_id: str
    itens: List[Dict]
    resultados_analise: List[Dict]

# Nó 1: Recuperar Ronda
def nos_recuperar_ronda(state: EstadoPipeline) -> EstadoPipeline:
    hudson = HudsonClient(api_key="hudson-dai-key-...")
    dados = hudson.buscar_ronda(state["ronda_id"])
    state["itens"] = dados["itens"]
    return state

# Nó 2: Analisar Contratos (Kan-sa)
def nos_analisar_contratos(state: EstadoPipeline) -> EstadoPipeline:
    contratos = [i for i in state["itens"] if i["estante"] == "document_text"]
    state["resultados_analise"] = contratos
    return state

# Nó 3: Extrair Metadados
def nos_extrair_metadados(state: EstadoPipeline) -> EstadoPipeline:
    hudson = HudsonClient(api_key="hudson-kansa-key-...")
    for item in state["resultados_analise"]:
        # Recuperar metadados completos
        # item["metadados"] = hudson.recuperar_metadados(item["item_id"])
        pass
    return state

# Construir grafo
workflow = StateGraph(EstadoPipeline)
workflow.add_node("recuperar_ronda", nos_recuperar_ronda)
workflow.add_node("analisar_contratos", nos_analisar_contratos)
workflow.add_node("extrair_metadados", nos_extrair_metadados)

workflow.set_entry_point("recuperar_ronda")
workflow.add_edge("recuperar_ronda", "analisar_contratos")
workflow.add_edge("analisar_contratos", "extrair_metadados")
workflow.add_edge("extrair_metadados", END)

app = workflow.compile()

# Executar
resultado = app.invoke({
    "ronda_id": "RONDA-2026-10-08",
    "itens": [],
    "resultados_analise": []
})
```

---

## 📊 MONITORAMENTO & OBSERVABILIDADE

### **Logs Estruturados**

```bash
# Arquivo: /var/log/hudson/api.log

# Cada request registra:
{
  "timestamp": "2026-10-08T19:35:22.123Z",
  "request_id": "uuid-1234-5678",
  "method": "GET",
  "endpoint": "/api/v1/items/ronda/RONDA-2026-10-08",
  "api_key": "hudson-dai-***" (truncated),
  "status_code": 200,
  "latency_ms": 145,
  "items_returned": 50,
  "ip_source": "10.8.0.5"
}

# Ver logs em tempo real:
tail -f /var/log/hudson/api.log | jq .
```

### **Alertas de Performance**

```
Se latência > 300ms:
  ⚠️ Verificar carga do PostgreSQL
  ⚠️ Verificar índices (EXPLAIN ANALYZE)
  ⚠️ Escalar response para DevOps

Se taxa de erro > 1%:
  🚨 Investigar logs de erro
  🚨 Verificar conectividade de rede
```

---

## 🚀 PLANO DE ROLLOUT

### **Fase 1: Setup Inicial (Dia 1)**

```
✅ VPN: Dai e Kan-sa conectados à rede corporativa
✅ API: Endpoints testados (health check 200 OK)
✅ Auth: API keys geradas e distribuídas
✅ Testes: Requisições manuais (curl/Postman)
```

### **Fase 2: Integração (Dias 2-3)**

```
✅ Dai: Integrado para recuperação de rodas
✅ Kan-sa: Busca fuzzy funcionando
✅ Logs: Monitorados para erros
✅ Performance: Baseline estabelecido
```

### **Fase 3: Automação (Semana 2)**

```
✅ LangGraph: Pipelines multi-agente em execução
✅ Alertas: Configurados em grafana
✅ Escalabilidade: Load test realizado
```

---

## 📞 SUPORTE TÉCNICO

| Dúvida | Resposta |
|:---|:---|
| **VPN não conecta** | Verificar `.ovpn` válido + firewall UDP 1194 |
| **API retorna 403** | Validar X-API-Key no header |
| **Busca fuzzy lenta** | Aumentar min_score para reduzir matches |
| **Latência alta** | Verificar índices PostgreSQL com `\d+ hudson.items` |

---

## 📝 CONCLUSÃO

A arquitetura está **PRONTA PARA INTEGRAÇÃO** com:

✅ Conectividade segura via OpenVPN  
✅ API REST FastAPI com 5 endpoints principais  
✅ Autenticação via API Key (escalável para mTLS)  
✅ Busca fuzzy com RapidFuzz integrada  
✅ Metadados completos de origem  
✅ Rastreamento por ronda_id  
✅ Monitoramento estruturado  
✅ SLAs definidos (<200ms P95)  

**Próximo passo:** Distribuir API keys e documentação para Dai & Kan-sa iniciarem integração.

---

**Especificação Assinada**  
Arquitetura Técnica — SUGOI  
08 de Outubro de 2026

