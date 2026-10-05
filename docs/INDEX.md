# 📑 Índice Mestre — Sugoi-SA/HUDSON: Ecossistema HDW & HDC

Este repositório abriga os dois pilares integrados do ecossistema HUDSON, organizados por temas:
1. 🏛️ **HUDSON DW (HDW):** Data Warehouse Soberano da SUGOI S.A. (Biblioteca Forense Digital Local na porta `8000`).
2. 🌐 **HUDSON DC (HDC):** Data Center & Event Hub Multi-Tenant da Daisugi Tecnologias (Orquestrador na porta `9000`).

---

## 🏛️ TEMA 1: HUDSON DW (Data Warehouse Soberano — Cliente SUGOI S.A.)
**Código-fonte:** [`backend/`](../backend/) (FastAPI :8000, PostgreSQL 15, Tesseract OCR, Poppler)  
**Servidor Alvo:** `vmsever.sugoisa.com.br` (CentOS 7 | 32 vCPUs | 31GB RAM | Storage `/financeiro/hudson`)

| Item | Documento | Descrição | Status |
| :--- | :--- | :--- | :--- |
| **KT-TI** | [`docs/hdw/KT-GUIA-INSTALACAO-HDW-LINUX.md`](hdw/KT-GUIA-INSTALACAO-HDW-LINUX.md) | Guia didático passo a passo para a TI da SUGOI instalar o HDW no Linux | ✅ Concluído |
| **HDW-SPEC**| [`docs/hdw/HDW-WORKFLOW-E-ESPECIFICACOES-SUGOI.md`](hdw/HDW-WORKFLOW-E-ESPECIFICACOES-SUGOI.md) | Especificação técnica e workflow de ingestão de pastas da SUGOI | ✅ Concluído |
| **S1** | [`specs/S1-openapi.yaml`](../specs/S1-openapi.yaml) | Contrato OpenAPI 3.1 do HDW (Idempotência e 6 Estantes) | ✅ Concluído |
| **S2** | [`specs/S2-schema.sql`](../specs/S2-schema.sql) | DDL PostgreSQL 15 (Triggers append-only bloqueando DELETE/UPDATE) | ✅ Concluído |
| **S3** | [`docs/hdw/S3-maquina-estados.md`](hdw/S3-maquina-estados.md) | Ciclo de estados do item custodiado | ✅ Concluído |
| **S4** | [`docs/hdw/S4-rbac-lgpd-matrix.md`](hdw/S4-rbac-lgpd-matrix.md) | Matriz RBAC e regras de anonimização LGPD | ✅ Concluído |
| **S5** | [`docs/hdw/S5-nfrs-e-operacao.md`](hdw/S5-nfrs-e-operacao.md) | Requisitos não-funcionais (NFRs) e rotinas de backup | ✅ Concluído |
| **S6** | [`docs/hdw/S6-testes.md`](hdw/S6-testes.md) | Plano de testes e golden files | ✅ Concluído |
| **S7** | [`docs/hdw/S7-metadados-por-estante.md`](hdw/S7-metadados-por-estante.md) | Metadados MARC catalogados por cada uma das 6 Estantes | ✅ Concluído |
| **S8** | [`docs/hdw/S8-cota-hudson.md`](hdw/S8-cota-hudson.md) | Algoritmo determinístico da Cota HUDSON `[ESTANTE]-[WBS]-[AAAA]-[hash8]` | ✅ Concluído |
| **P1 a P8**| [`diagrams/`](../diagrams/) | 8 Diagramas arquiteturais e periciais do HDW | ✅ Concluído |

---

## 🌐 TEMA 2: HUDSON DC (Data Center Central — Daisugi Tecnologias)
**Código-fonte:** [`hdc/`](../hdc/) (FastAPI :9000, Celery, Redis, Docker Compose OCI)  
**Ambiente:** Oracle Cloud Infrastructure (`hudson.daisugi.com.br`) na rede interna `daisugi-net`

| Item | Documento | Descrição | Status |
| :--- | :--- | :--- | :--- |
| **HDC-ARCH**| [`docs/hdc/HDC-ARQUITETURA-E-GOVERNANCA.md`](hdc/HDC-ARQUITETURA-E-GOVERNANCA.md) | Arquitetura, governança multi-tenant e homeostase do HDC | ✅ Concluído |
| **DAI-INT** | [`docs/hdc/DOCUMENTO_INTEGRACAO_DAI_HUDSON.md`](hdc/DOCUMENTO_INTEGRACAO_DAI_HUDSON.md) | Especificação oficial de integração DAI × HUDSON v1.2.0 | ✅ Concluído |
| **HOMOLOG** | [`docs/hdc/HDC-RELATORIO-HOMOLOGACAO-E-CIRCUITO-PAM.md`](hdc/HDC-RELATORIO-HOMOLOGACAO-E-CIRCUITO-PAM.md) | Relatório Oficial de Homologação E2E (PAM, DAI, HDC, HDW) e Testes de SoD | ✅ Concluído |
| **HDC-CODE**| [`hdc/README.md`](../hdc/README.md) | Manual de execução do HDC com Docker Compose e FastAPI :9000 | ✅ Concluído |
| **TESTS**   | [`hdc/tests/`](../hdc/tests/) | Suíte de testes automatizados (API, Harness Anti-Alucinação e Circuito E2E) | ✅ Concluído |
