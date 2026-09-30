# 📊 Comparativa: Only Guillmon (Fuzzy+Harness) vs HUDSON v0

Analisando as similaridades e diferenças arquiteturais entre os dois sistemas.

---

## 🎯 Conceito Central

### Only Guillmon (seu arquivo)
```
Harness (rígido, determinístico)
       ↓
    + 
       ↓
Fuzzy (5 subagentes especialistas com LLM)
       ↓
Saída: Relatórios de Auditoria + Minutas Jurídicas
```

### HUDSON v0 (atual)
```
Harness (rígido, determinístico)
       ↓
    + 
       ↓
Busca Inteligente (Full-text + Semântica)
       ↓
Saída: Documentos Indexados + Pesquisável
       ↓
(Fuzzy com LLM ← Fase 1.1/1.2: WATSON + HOLMES + MYCROFT)
```

---

## 📋 Mapeamento de Componentes

### **HARNESS (Trabalho Sistemático, Sem Alucinação)**

| Componente | Only Guillmon | HUDSON v0 |
|---|---|---|
| **Entrada** | Google Drive local | Webhook Zeev + CLI + Upload |
| **Parsing** | OCR + pdfplumber | OCR (Tesseract) + pdfplumber |
| **Extração** | Estruturação de dados | Conteúdo + Metadados |
| **Armazenamento Duplo** | SQLite + ChromaDB | PostgreSQL + ChromaDB |
| **Deduplicação** | Query manual | Hash SHA-256 + Mutex |
| **Indexação** | Semantic only | Full-text (tsvector) + Semantic |
| **Orquestração** | MetaGPT | FastAPI (routers/services/repos) |

### **FUZZY (Inteligência, LLM)**

| Componente | Only Guillmon | HUDSON v0 |
|---|---|---|
| **Motor de Regras** | 5 Subagentes Persona | (Não implementado v0) |
| **Especialização** | Financeiro, Compliance, Direito, Contencioso, Auditoria | Será: NER, Entity Linking, Chat Tradutor (Fase 1.1) |
| **LLM Backend** | Ollama Local OU Gemini/DeepSeek (switch .env) | Ainda não implementado |
| **Decisões** | Regras fuzzy (0.0-1.0) | Será: Confidence scores + Alerts |
| **Saída Inteligente** | Parecer jurídico + Minuta | Será: Recomendações de ação + Alertas |

---

## 🔄 Fluxo Comparativo

### **Only Guillmon**

```
Google Drive Local
       ↓
Extrator OCR/pdfplumber
       ↓
[HARNESS] Estruturação SQLite + ChromaDB
       ↓
[FUZZY] 5 Subagentes Interpretam
       │
       ├─ Auditor Financeiro → Conciliação
       ├─ Analista Compliance → Validação Quórum
       ├─ Especialista Direito → Art. 1.348 CC
       ├─ Consultor Contencioso → Pareceres
       └─ Relator Auditoria → Matriz Severidade
       ↓
Saída: Relatório Executivo + Minuta Jurídica
```

### **HUDSON v0**

```
Webhook Zeev / CLI / Upload
       ↓
[HARNESS] Parser + OCR
       ↓
Hash SHA-256 → custody_log (imutável)
       ↓
Dedup (sem race condition)
       ↓
Roteador por Estante (6 categorias)
       ↓
Cota HUDSON (determinística)
       ↓
Armazenamento Duplo:
  ├─ PostgreSQL (items + entities + relationships + custody_log)
  └─ ChromaDB (embeddings semânticos)
       ↓
Indexação:
  ├─ Full-text tsvector (português)
  └─ Semantic (BGE-M3)
       ↓
Saída: Documentos Pesquisáveis
       ↓
[FUZZY v1.1] WATSON + HOLMES + MYCROFT (LLM-powered)
       │
       ├─ WATSON (agregação multi-fonte)
       ├─ HOLMES (análise forense profunda)
       └─ MYCROFT (NER + entity linking)
       ↓
Saída: Recomendações Inteligentes + Alertas
```

---

## 🏗️ Arquitetura em Camadas

### **Only Guillmon**

```
┌─────────────────────────────────┐
│   Saída (Relatório + Minuta)    │  ← LLM-based decisions
├─────────────────────────────────┤
│   Fuzzy: 5 Subagentes LLM       │  ← Inteligência
├─────────────────────────────────┤
│   Router LLM: Ollama/Gemini     │  ← Seleção backend
├─────────────────────────────────┤
│   Harness: SQLite + ChromaDB    │  ← Dados estruturados
├─────────────────────────────────┤
│   Parser: OCR + pdfplumber      │  ← Extração
├─────────────────────────────────┤
│   Entrada: Google Drive Local   │  ← Origem
└─────────────────────────────────┘
```

### **HUDSON v0**

```
┌──────────────────────────────────────────────────┐
│   Fase 1.1+ : WATSON + HOLMES + MYCROFT (LLM)   │  ← Inteligência futura
├──────────────────────────────────────────────────┤
│   Saída: Consultas (JSON) + Busca Híbrida       │  ← Respostas estruturadas
├──────────────────────────────────────────────────┤
│   Query Layer: 3 Endpoints HTTP                  │
│   - /search (full-text + semantic)              │
│   - /items/{cota} (detalhe + custody_chain)     │
│   - /authenticity (certificado SHA-256)         │
├──────────────────────────────────────────────────┤
│   Harness: Indexação                             │  ← Trabalho sistemático
│   - tsvector (PostgreSQL FTS)                   │
│   - Embeddings (ChromaDB)                       │
│   - Custody_log (append-only)                   │
├──────────────────────────────────────────────────┤
│   Harness: Roteamento & Custódia                │  ← Determinístico
│   - Estante Router (6 categorias)               │
│   - Cota Generator (determinística)             │
│   - Storage com checksums                       │
├──────────────────────────────────────────────────┤
│   Harness: Processamento Core                    │  ← Zero alucinação
│   - Hash SHA-256 (streaming)                    │
│   - Dedup com mutex                             │
│   - Integridade pós-cópia                       │
├──────────────────────────────────────────────────┤
│   Harness: Ingestão                              │  ← Múltiplos canais
│   - Webhook Zeev                                │
│   - CLI Python                                  │
│   - Upload HTTP (futura)                        │
├──────────────────────────────────────────────────┤
│   Armazenamento Duplo                            │  ← Persistência
│   - PostgreSQL (estruturado + auditoria)        │
│   - ChromaDB (semântica)                        │
│   - File storage (custódia original)            │
└──────────────────────────────────────────────────┘
```

---

## 🔐 Garantias de Segurança

### **Only Guillmon**

| Garantia | Mecanismo |
|---|---|
| Sem alucinação | SQLite + ChromaDB como fonte de verdade |
| Auditoria | ChromaDB rastreá provenance |
| Autenticidade | Hash de entrada (não especificado) |
| Conformidade | LGPD implícita (sem delete permite) |

### **HUDSON v0**

| Garantia | Mecanismo |
|---|---|
| Sem alucinação | Hash SHA-256 verificável |
| Auditoria | custody_log append-only com triggers |
| Autenticabilidade | POST /authenticity (certificado) |
| Zero exclusão | Trigger BEFORE DELETE rejeita |
| Integridade | Recomputa SHA-256 pós-cópia |
| Concorrência | Mutex + savepoint em transaction |
| Privacidade | RBAC + tarjamento LGPD (Fase 1.1) |

---

## 📊 Tabelas de Dados

### **Only Guillmon** (SQLite)

```
Assumido (documentação não especifica):
- documents (id, path, content_text, hash?, embedding_id)
- jurisprudencia (id, title, content, embedding_id)
- (ChromaDB: embeddings + provenance)
```

### **HUDSON v0** (PostgreSQL 15)

```
TABELAS FORMALMENTE DEFINIDAS:

items (PK: item_id)
├─ item_id
├─ cota (UNIQUE) — [ESTANTE]-[WBS]-[AAAA]-[hash8]
├─ hash_sha256 (UNIQUE)
├─ estante (FOREIGN KEY → estant_types)
├─ status (CHECK: recebido, indexado, quarentena, falha_processamento)
├─ criado (TIMESTAMP)
├─ duplicate_of_item_id (SELF-REFERENCE)
└─ metadados (JSONB)

custody_log (PK: log_id, APPEND-ONLY)
├─ log_id
├─ item_id (FK → items)
├─ event_type (recebido, indexado, consultado, verificado)
├─ timestamp
├─ usuario
├─ ip_address
└─ [TRIGGER BEFORE DELETE/UPDATE → REJEITA]

entities (PK: entity_id)
├─ entity_id
├─ item_id (FK → items)
├─ tipo (PESSOA, PJ, ENDERECO, etc)
├─ nome
├─ cpf/cnpj
└─ relevancia (0.0-1.0)

relationships (PK: relation_id)
├─ relation_id
├─ entity_a (FK → entities)
├─ entity_b (FK → entities)
├─ tipo_relacao
└─ confianca (0.0-1.0)

estant_types (PK: estante)
├─ estante (JURIDICO, FINANCEIRO, RH, ...)
└─ descricao

declarations (PK: declaration_id)
├─ declaration_id
├─ item_id (FK → items)
├─ tipo_declaracao
└─ conteudo_json
```

---

## 🧠 Quando Entra Inteligência (Fuzzy)?

### **Only Guillmon (JÁ IMPLEMENTADO)**

✅ **5 Subagentes interpretam dados** conforme ações iniciam:
```
1. Auditor lê SQLite → Reconcilia valores
2. Compliance lê jurisprudência → Valida quórum
3. Direito interpreta → Cita artigos CC
4. Contencioso redige → Parecer jurídico
5. Relator agrega → Matriz severidade
```

### **HUDSON v0 (NÃO IMPLEMENTADO)**

❌ **v0 é puro Harness (determinístico)**

✅ **Fase 1.1 introduz Fuzzy (LLM)**:
```
[NER Automático]
Extrai entidades: PJ, PF, CNPJ, CPF, datas, valores

[Entity Linking]
Vincula: "ABC Corp" + CNPJ-12345... = mesma entidade

[Chat Tradutor]
"Mostre contratos de aluguel entre 2024-2026"
→ Query SQL determinística
→ Enriquecida com insights semânticos

[Inteligência Distribuída]
WATSON: Agrega multi-fonte
HOLMES: Análise forense profunda
MYCROFT: LLM judge final
```

---

## 🎬 Cronograma: Quando Ficam Similares?

### **Today (2026-09-30): HUDSON v0 = Harness Puro**
```
Sem inteligência — apenas indexação e busca estruturada
Similar ao: "Google Docs" (full-text search)
```

### **2026-10: HUDSON Fase 1.1 = Harness + Fuzzy Básico**
```
Entrada: Same harness
Processamento: Full-text + Semantic + NER
Saída: Recomendações automáticas
Similar ao: "Only Guillmon" (mas sem 5 personas específicas)
```

### **2026-11: HUDSON Fase 1.2 = Full Fuzzy**
```
Entrada: Same harness
Processamento: Same
Saída: 5 Personas jurídicas (WATSON, HOLMES, MYCROFT + 2 extras)
Similar ao: "Only Guillmon COMPLETO"
```

---

## 🎯 Resumo em 1 Tabela

| Aspecto | Only Guillmon | HUDSON v0 | HUDSON 1.1+ |
|---|---|---|---|
| **Harness** | SQLite + ChromaDB simples | PostgreSQL + ChromaDB robusto | Mesmo |
| **Fuzzy (LLM)** | ✅ 5 Personas | ❌ Não | ✅ 3+ Personas (WATSON, HOLMES, MYCROFT) |
| **Entrada** | Google Drive | Webhook + CLI | Mesmo + UI |
| **Saída** | Parecer + Minuta | JSON pesquisável | JSON + Recomendações inteligentes |
| **Segurança** | Boa | Excelente (zero-exclusão) | Excelente |
| **Auditoria** | ChromaDB | custody_log (imutável) | Mesmo |
| **Status** | Produção | Beta v0 | Roadmap |

---

## 🚀 Próximo Passo Para HUDSON

### Agora (v0)
✅ Deploy em vmsever  
✅ Validar indexação full-text  
✅ Testar busca semântica  

### Semana que vem (v1.1)
⏳ Integrar NER (Named Entity Recognition)  
⏳ Implementar WATSON + HOLMES  
⏳ Adicionar `/insights` endpoint  

### Próximo mês (v1.2)
⏳ MYCROFT LLM judge  
⏳ Integração oficial Zeev  
⏳ RBAC + LGPD completo  

---

**Documento**: Comparativa Only Guillmon ↔ HUDSON v0  
**Data**: 2026-09-30  
**Conclusão**: Arquiteturalmente similares; HUDSON é mais robusto (zero-exclusão + append-only); Fuzzy (LLM) é roadmap para HUDSON
