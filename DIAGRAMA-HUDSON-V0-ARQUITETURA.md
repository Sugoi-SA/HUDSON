# 🏗️ HUDSON v0 — Arquitetura Detalhada com Nós e Fluxos

Diagrama completo mostrando como documentos entram, são processados, armazenados e consultados.

```mermaid
flowchart TD
    %% ===== ESTILOS =====
    classDef input fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    classDef webhook fill:#81C784,stroke:#558B2F,stroke-width:2px,color:#fff
    classDef process fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    classDef custody fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    classDef storage_sql fill:#0288D1,stroke:#01579B,stroke-width:2px,color:#fff
    classDef storage_vec fill:#D84315,stroke:#BF360C,stroke-width:2px,color:#fff
    classDef storage_file fill:#558B2F,stroke:#33691E,stroke-width:2px,color:#fff
    classDef query fill:#9C27B0,stroke:#4A148C,stroke-width:2px,color:#fff
    classDef output fill:#FBC02D,stroke:#F57F17,stroke-width:2px,color:#000
    classDef router fill:#455A64,stroke:#263238,stroke-width:2px,color:#fff

    %% ===== CAMADA 1: INGESTÃO =====
    subgraph ENTRADA["📥 CAMADA 1: INGESTÃO DE DOCUMENTOS"]
        
        subgraph CANAIS["Canais de Entrada"]
            WEBHOOK["🔔 Webhook Zeev<br/>POST /items<br/>trigger: documento gerado"]:::webhook
            CLI["💻 CLI Python<br/>import_cli.py<br/>importação em lote"]:::input
            UPLOAD["📤 Upload HTTP<br/>multipart/form-data<br/>UI futura"]:::input
        end
        
        subgraph META["Extração de Metadados"]
            PARSER["📄 Parser de Arquivo<br/>- Detecção formato<br/>- MIME type validation<br/>- Tamanho/encoding"]:::process
            EXTRACT["🔍 Extrator de Conteúdo<br/>- OCR (Tesseract)<br/>- PDF text extraction<br/>- DOCX parsing"]:::process
        end
        
        WEBHOOK --> PARSER
        CLI --> PARSER
        UPLOAD --> PARSER
        PARSER --> EXTRACT
    end

    %% ===== CAMADA 2: PROCESSAMENTO CORE =====
    subgraph CORE["⚙️ CAMADA 2: PROCESSAMENTO CORE"]
        
        subgraph HASH["Hash & Integridade"]
            HASH_CALC["🔐 SHA-256 Streaming<br/>- Lê arquivo em chunks<br/>- Calcula hash on-the-fly<br/>- Sem carregar em RAM"]:::process
            HASH_STORE["📌 Hash → custody_log<br/>timestamp + sha256<br/>imutável (append-only)"]:::custody
        end
        
        subgraph DEDUP["Deduplicação"]
            HASH_CHECK["🔎 Busca Hash Existente<br/>SELECT * FROM items<br/>WHERE hash_sha256 = ?"]:::process
            DEDUP_LOGIC["⚡ Decision: Duplicado?<br/>SIM → marca como duplicata<br/>NÃO → continua processamento"]:::process
            LOCK_CONCUR["🔒 Mutex de Concorrência<br/>savepoint in transaction<br/>evita race condition"]:::process
        end
        
        HASH_CALC --> HASH_STORE
        HASH_STORE --> HASH_CHECK
        HASH_CHECK --> DEDUP_LOGIC
        DEDUP_LOGIC --> LOCK_CONCUR
    end

    %% ===== CAMADA 3: ROTEAMENTO & CUSTÓDIA =====
    subgraph ROTEAMENTO["🛣️ CAMADA 3: ROTEAMENTO & CUSTÓDIA"]
        
        subgraph ESTANTES["Roteamento por Estante"]
            ROUTER["🧭 Estante Router<br/>Classifica por tipo:<br/>- JURIDICO<br/>- FINANCEIRO<br/>- RH<br/>- OPERACIONAL<br/>- CONTABIL<br/>- ADMINISTRATIVO"]:::router
            
            COTA_GEN["🏷️ Gerador Cota HUDSON<br/>Format: [ESTANTE]-[WBS]-[AAAA]-[hash8]<br/>Exemplo: JURIDICO-001-2026-a1b2c3d4<br/>✅ Determinístico (idempotente)"]:::process
        end
        
        subgraph CUSTODIAL["Armazenamento de Custódia"]
            CUSTODY_PATH["📂 Cria Caminho de Custódia<br/>/var/hudson/storage/<br/>/JURIDICO/<br/>/2026/<br/>/JURIDICO-001-2026-a1b2c3d4/"]:::storage_file
            
            COPY_FILE["📋 Cópia Imutável<br/>cp -p arquivo destino<br/>preserva permissões<br/>mtime original"]:::storage_file
            
            VERIFY_COPY["✔️ Verifica Integridade<br/>SHA-256 pós-cópia<br/>SIM: status = indexado<br/>NÃO: status = falha_processamento + quarentena"]:::process
        end
        
        LOCK_CONCUR --> ROUTER
        ROUTER --> COTA_GEN
        COTA_GEN --> CUSTODY_PATH
        CUSTODY_PATH --> COPY_FILE
        COPY_FILE --> VERIFY_COPY
    end

    %% ===== CAMADA 4: ARMAZENAMENTO DUPLO =====
    subgraph STORAGE["💾 CAMADA 4: ARMAZENAMENTO DUPLO"]
        
        subgraph DB_SQL["Dados Estruturados<br/>PostgreSQL 15"]
            ITEMS_TB["📊 Tabela: items<br/>- item_id (PK)<br/>- cota (UNIQUE)<br/>- hash_sha256 (UNIQUE)<br/>- estante<br/>- status<br/>- criado<br/>- duplicate_of_item_id<br/>- metadados (JSON)"]:::storage_sql
            
            CUSTODY_TB["🔐 Tabela: custody_log<br/>- log_id (PK)<br/>- item_id (FK)<br/>- event_type<br/>- timestamp<br/>- usuario<br/>- ip_address<br/>- ação (APPEND-ONLY)"]:::storage_sql
            
            ENTITIES_TB["👥 Tabela: entities<br/>- entity_id (PK)<br/>- item_id (FK)<br/>- tipo (PESSOA/PJ)<br/>- nome<br/>- cnpj/cpf<br/>- relevância"]:::storage_sql
            
            RELATIONS_TB["🔗 Tabela: relationships<br/>- relation_id (PK)<br/>- entity_a<br/>- entity_b<br/>- tipo_relação<br/>- confiança"]:::storage_sql
            
            TRIGGER["⚠️ Triggers PostgreSQL<br/>- BEFORE DELETE ON items<br/>- BEFORE UPDATE ON items<br/>→ Rejeita: 'ZERO EXCLUSÃO'<br/>→ Append-only garantido"]:::process
        end
        
        subgraph DB_VEC["Busca Semântica<br/>ChromaDB"]
            CHROMA_CHUNKS["📑 Chunks de Texto<br/>- Segmenta por parágrafo<br/>- Max 512 tokens<br/>- Overlap 50 tokens"]:::storage_vec
            
            EMBEDDINGS["🧠 Embeddings PT-BR<br/>Modelo: BGE-M3 ou multilingual-e5<br/>Dimensionalidade: 768<br/>Local ou serverless"]:::storage_vec
            
            SEMANTIC_IDX["🔍 Índice Semântico<br/>ChromaDB armazena:<br/>- embedding (vetor)<br/>- texto original<br/>- item_id (referência)"]:::storage_vec
        end
        
        VERIFY_COPY --> ITEMS_TB
        ITEMS_TB --> CUSTODY_TB
        VERIFY_COPY --> ENTITIES_TB
        ENTITIES_TB --> RELATIONS_TB
        ITEMS_TB --> TRIGGER
        
        EXTRACT --> CHROMA_CHUNKS
        CHROMA_CHUNKS --> EMBEDDINGS
        EMBEDDINGS --> SEMANTIC_IDX
    end

    %% ===== CAMADA 5: INDEXAÇÃO FULL-TEXT =====
    subgraph INDEXING["🔎 CAMADA 5: INDEXAÇÃO FULL-TEXT"]
        
        subgraph FTS["Full-Text Search (PostgreSQL)"]
            TSVECTOR["📋 tsvector PT-BR<br/>Análise lexical português<br/>- Remove stopwords<br/>- Lematização<br/>- Stemming"]:::process
            
            TSVECTOR_STORE["💾 Coluna: tsvector<br/>Armazenado em items<br/>índice GIN para busca rápida<br/>O(log n) complexity"]:::storage_sql
            
            GIN_INDEX["⚡ Índice GIN<br/>CREATE INDEX gin_idx<br/>ON items USING gin(tsvector)"]:::storage_sql
        end
        
        EXTRACT --> TSVECTOR
        TSVECTOR --> TSVECTOR_STORE
        TSVECTOR_STORE --> GIN_INDEX
    end

    %% ===== CAMADA 6: CONSULTA & BUSCA =====
    subgraph QUERY_LAYER["🔍 CAMADA 6: CONSULTA & BUSCA"]
        
        subgraph ENDPOINTS["Endpoints HTTP (FastAPI)"]
            SEARCH_EP["GET /search?query=...<br/>Busca full-text OR semântica<br/>Retorna item_id + score"]:::query
            ITEM_EP["GET /items/{cota}<br/>Retorna item completo<br/>+ entidades relacionadas<br/>+ chain de custódia"]:::query
            AUTH_EP["GET /authenticity<br/>Recomputa SHA-256<br/>Compara com custody_log<br/>Gera certificado de autenticidade"]:::query
        end
        
        subgraph QUERY_LOGIC["Lógica de Busca"]
            HYBRID["🔀 Busca Híbrida<br/>1. Full-text (tsvector)<br/>2. Semântica (ChromaDB)<br/>3. Fusion (combina scores)"]:::process
            
            AUTH["🔐 Autenticação<br/>Header: Authorization: Bearer <API_KEY><br/>Válida contra .env<br/>401 se inválida"]:::process
            
            RBAC_CHECK["👮 Verificação RBAC<br/>Qual estante o usuário pode ver?<br/>(Fase 1.1, não implementado v0)"]:::process
        end
        
        SEARCH_EP --> HYBRID
        ITEM_EP --> AUTH
        SEARCH_EP --> AUTH
        AUTH --> RBAC_CHECK
    end

    %% ===== CAMADA 7: SAÍDA & CONSUMO =====
    subgraph OUTPUT["📤 CAMADA 7: SAÍDA & CONSUMO"]
        
        subgraph RESULT_JSON["Respostas JSON (OpenAPI)"]
            RES_SEARCH["```json<br/>{<br/>  'results': [<br/>    {<br/>      'item_id': '123',<br/>      'cota': 'JURIDICO-...',<br/>      'score': 0.95,<br/>      'preview': '...',<br/>      'entities': [<br/>        {'tipo': 'PJ', 'nome': 'ABC Corp'}<br/>      ]<br/>    }<br/>  ],<br/>  'total': 42<br/>}<br/>```"]:::output
            
            RES_ITEM["```json<br/>{<br/>  'cota': 'JURIDICO-...',<br/>  'hash_sha256': 'a1b2c3...',<br/>  'estante': 'JURIDICO',<br/>  'status': 'indexado',<br/>  'criado': '2026-09-30T...',<br/>  'conteudo': '...',<br/>  'custody_chain': [<br/>    {event: 'criado', ts: '...'},<br/>    {event: 'indexado', ts: '...'}<br/>  ]<br/>}<br/>```"]:::output
        end
        
        subgraph DOWNSTREAM["Consumidores Downstream (Fase 1.1)"]
            WATSON["🤖 WATSON S2<br/>(Não implementado v0)<br/>Consome /search<br/>Agrega resultados<br/>multi-fonte"]:::input
            
            HOLMES["🔍 HOLMES S3<br/>(Não implementado v0)<br/>Consome /items/{cota}<br/>Análise forense<br/>Deep inspection"]:::input
            
            MYCROFT["🧠 MYCROFT S4<br/>(Não implementado v0)<br/>Consome tudo acima<br/>NER + entity linking<br/>LLM-powered analysis"]:::input
        end
        
        HYBRID --> RES_SEARCH
        CUSTODY_TB --> RES_ITEM
        RES_SEARCH -.->|via API| WATSON
        RES_ITEM -.->|via API| HOLMES
        WATSON -.->|via API| MYCROFT
    end

    %% ===== CICLO DE VIDA =====
    subgraph LIFECYCLE["♻️ CICLO DE VIDA: Backup & Integridade"]
        
        BACKUP["💾 Backup Diário (Cron 03h)<br/>pg_dump -Fc hudson.dump<br/>tar -czf hudson_storage.tar.gz<br/>Retenção: 14 dias"]:::process
        
        INTEGRITY_CHECK["🔐 Varredura de Integridade<br/>(Fase 1.2)<br/>SELECT * FROM items<br/>Recomputa SHA-256<br/>Compara com custody_log<br/>Alerta se divergência"]:::process
        
        CUSTODY_TB --> BACKUP
        ITEMS_TB --> INTEGRITY_CHECK
    end

```

---

## 📌 Resumo de Nós por Camada

### **CAMADA 1: Ingestão** 
| Nó | Função | Saída |
|---|---|---|
| 🔔 Webhook Zeev | Recebe trigger de documento | arquivo + metadados |
| 💻 CLI Python | Batch import local | arquivo + estante |
| 📤 Upload HTTP | UI futura | arquivo multipart |
| 📄 Parser | Detecta formato + MIME | formato validado |
| 🔍 Extrator | OCR + text extraction | conteúdo extraído |

### **CAMADA 2: Processamento**
| Nó | Função | Garantia |
|---|---|---|
| 🔐 SHA-256 | Hash streaming | Zero colisão (teórico) |
| 📌 custody_log | Registra hash | Append-only, auditável |
| 🔎 Hash Check | Busca duplicata | Dedup garantida |
| ⚡ Decision | Sim/Não duplicado | Lógica determinística |
| 🔒 Mutex | Evita race condition | Concorrência segura |

### **CAMADA 3: Roteamento & Custódia**
| Nó | Função | Resultado |
|---|---|---|
| 🧭 Estante Router | Classifica 6 estantes | [ESTANTE] definida |
| 🏷️ Cota Generator | Cria identificador único | JURIDICO-001-2026-a1b2c3d4 |
| 📂 Caminho Custódia | Estrutura de pastas | /var/hudson/storage/JURIDICO/2026/... |
| 📋 Cópia Imutável | cp com preservação | Arquivo seguro |
| ✔️ Verifica Integridade | Recomputa SHA-256 | indexado OU quarentena |

### **CAMADA 4: Armazenamento**
| BD | Nó | Propósito | Query Típica |
|---|---|---|---|
| **PostgreSQL** | items | Metadados + status | SELECT * WHERE hash = 'abc...' |
| **PostgreSQL** | custody_log | Auditoria imutável | SELECT * WHERE item_id = 123 ORDER BY timestamp |
| **PostgreSQL** | entities | PJ/PF identificadas | SELECT * WHERE item_id = 123 |
| **PostgreSQL** | relationships | Vínculos | SELECT * WHERE entity_a = 'CNPJ-ABC' |
| **ChromaDB** | embeddings | Semântica PT-BR | query('contrato de aluguel') → [resultado similar] |

### **CAMADA 5: Indexação**
| Nó | Tecnologia | Uso |
|---|---|---|
| 📋 tsvector | PostgreSQL FTS | SELECT * WHERE tsvector @@ plainto_tsquery('português', 'contrato') |
| 💾 GIN Index | PostgreSQL B-tree | O(log n) lookup em tsvector |
| 📑 Chunks | ChromaDB | Segmentação de 512 tokens com overlap |
| 🧠 Embeddings | BGE-M3 | Similaridade semântica |

### **CAMADA 6: Busca**
| Endpoint | Entrada | Saída |
|---|---|---|
| GET /search?query=X | string + API key | [{item_id, cota, score, preview}] |
| GET /items/{cota} | cota + API key | {cota, hash, conteúdo, custody_chain} |
| GET /authenticity | item_id + API key | {verificado: true/false, certificado} |

### **CAMADA 7: Consumo**
| Sistema | Fase | Consome |
|---|---|---|
| WATSON S2 | 1.1 | GET /search (agregação multi-fonte) |
| HOLMES S3 | 1.1 | GET /items/{cota} (análise forense) |
| MYCROFT S4 | 1.1 | Tudo + LLM (NER + entity linking) |

---

## 🔄 Fluxo de Um Arquivo (Exemplo)

**Input**: Arquivo PDF `contrato_aluguel_2026.pdf` via Webhook Zeev

```
1. INGESTÃO
   Webhook → Parser detecta PDF → Extrator OCR
   
2. PROCESSAMENTO
   SHA-256 = a1b2c3d4e5f6g7h8...
   custody_log.insert(hash, timestamp, 'recebido')
   Busca hash em items → NÃO encontrado
   Mutex lock OK
   
3. ROTEAMENTO
   Estante Router → JURIDICO
   Cota = JURIDICO-001-2026-a1b2c3d4
   
4. CUSTÓDIA
   Caminho = /var/hudson/storage/JURIDICO/2026/JURIDICO-001-2026-a1b2c3d4/
   cp contrato_aluguel_2026.pdf → destino
   Verifica SHA-256 → MATCH ✓
   
5. ARMAZENAMENTO
   INSERT INTO items (cota, hash, estante, status='indexado', ...)
   custody_log.insert(item_id, 'indexado', timestamp)
   entities.insert([PJ: 'Imobiliária XYZ'])
   
6. INDEXAÇÃO
   tsvector = to_tsvector('portuguese', conteudo)
   UPDATE items SET tsvector = ... WHERE item_id = 123
   ChromaDB.add(embedding, texto, item_id=123)
   
7. CONSULTA (Fase 1.1+)
   Usuario faz: GET /search?query=aluguel
   → tsvector match: 0.85
   → semantic match: 0.92
   → WATSON agrega com outras fontes
   → HOLMES faz análise profunda
   → MYCROFT enriquece com NER

8. BACKUP (Cron 03h)
   pg_dump -Fc hudson → /backups/postgres/hudson_20260930_030000.dump
   tar -czf /backups/storage/hudson_storage_20260930_030000.tar.gz
```

---

## 🎯 Resumo de Responsabilidades por Nó

| Nó | "Trabalho Sujo" (Harness) | "Inteligência" (Fuzzy) | Nota |
|---|---|---|---|
| Parser + Extrator | ✅ | - | Sem alucinação |
| Hash + Dedup | ✅ | - | Determinístico |
| Roteador | ✅ (regras 6 estantes) | - | Config .env |
| Cota Generator | ✅ | - | Matemático puro |
| PostgreSQL | ✅ | - | Dados estruturados |
| ChromaDB | ✅ | ✅ | Embedding é "fuzzy" |
| Full-text Index | ✅ | - | Determinístico |
| /search endpoint | ✅ | ✅ | Hybrid (FTS + semântica) |
| WATSON/HOLMES/MYCROFT | - | ✅ | Fase 1.1/1.2 (LLM-powered) |

---

## 📁 Estrutura de Diretórios Correspondente

```
/var/hudson/
├── storage/                    ← Custódia física
│   ├── JURIDICO/
│   │   ├── 2026/
│   │   │   ├── JURIDICO-001-2026-a1b2c3d4/
│   │   │   │   ├── contrato_aluguel_2026.pdf
│   │   │   │   └── .metadata (JSON)
│   │   │   └── JURIDICO-002-2026-b3c4d5e6/
│   ├── FINANCEIRO/
│   ├── RH/
│   ├── OPERACIONAL/
│   ├── CONTABIL/
│   └── ADMINISTRATIVO/
│
├── backups/                    ← Recuperação
│   ├── postgres/
│   │   ├── hudson_20260930_030000.dump
│   │   └── hudson_20260930_030000.dump
│   └── storage/
│       ├── hudson_storage_20260930_030000.tar.gz
│       └── hudson_storage_20260930_030000.tar.gz

/home/hudson/HUDSON/
├── backend/
│   ├── app/
│   │   ├── routers/            ← Endpoints HTTP
│   │   ├── services/           ← Lógica (hash, dedup, cota, etc)
│   │   ├── repositories/       ← Acesso BD
│   │   └── schemas/            ← Pydantic contracts
│   ├── tests/                  ← 22 testes pytest
│   ├── deploy/
│   │   ├── hudson-api.service  ← Systemd
│   │   └── backup.sh           ← Cron script
│   └── .env                    ← Config (DATABASE_URL, API_KEY, etc)
```

---

**Documento**: Arquitetura HUDSON v0 com Nós Detalhados  
**Preparado**: 2026-09-30  
**Para**: vmsever.sugoisa.com.br  
**Status**: 🟢 Pronto para Deploy
