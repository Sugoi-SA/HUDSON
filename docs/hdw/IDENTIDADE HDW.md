# ANÁLISE TÉCNICA E ARQUITETURAL: HUDSON DATA WAREHOUSE (HDW)

**Visão Integrada de Arquitetura de Software, Data Warehouse, Arquivologia Forense e Gestão de Processos (BPM)**  
*Organização: SUGOI S.A. & Daisugi Tecnologias*  
*Segmento: Construção Civil / Minha Casa Minha Vida (MCMV)*

---

## 🏛️ 1. O QUÊ? (Conceito, Identidade e Custódia Arquivística Forense)

### Definindo o HUDSON DW
O **HUDSON DW (HDW)** é a **Biblioteca Soberana e Cofre Digital Forense Local** da SUGOI S.A.. Trata-se de um Data Warehouse documental e imutável projetado para armazenar, catalogar, proteger e certificar a autenticidade probatória de **100% dos ativos de informação, documentos e registros operacionais** da empresa.

Ele opera no ecossistema como a fonte única da verdade (*Single Source of Truth - SSOT*), rodando sob infraestrutura Linux e banco de dados PostgreSQL 18.6 (schema `hudson`) na porta `:8000`. Enquanto o módulo parceiro **HUDSON DC (`hdc/`)** funciona como orquestrador de eventos, barramento de mensageria e hub multi-tenant, o **HDW** é o módulo de **custódia estrita, indexação e preservação probatória**.

### Mapeamento do Acervo Institucional e Forense (SUGOI S.A. / MCMV)
O HDW foi desenhado para absorver, indexar e custodiar **todo e qualquer documento útil, probatório ou potencialmente comprometedor**, abrangendo os seguintes pilares operacionais, técnicos e jurídicos:

| Categoria do Acervo | Tipos de Documentos / Fontes Custodiadas | Relevância Forense, Operacional e Normativa |
| :--- | :--- | :--- |
| **Jurídico, Societário e Contratual** | Contratos de empreitada, aditivos, distratos, procurações, atas e e-mails corporativos (`.eml`, `.msg`, `.pst`). | Proteção contra passivos judiciais, comprovação de comunicações formais/comprometedoras e histórico de negociações. |
| **Engenharia e Projetos Executivos** | Plantas CAD/BIM (`.dwg`, `.dxf`, `.rvt`, `.ifc`), memoriais descritivos, RDO (Relatório Diário de Obra) e revisões de projeto. | Vínculo direto com o código WBS da obra (`obra_wbs`) para rastreabilidade de alterações técnicas e medições. |
| **Qualidade e Normas (ISO 9001 / PBQP-H / QSMS)** | Ficha de Verificação de Serviço (FVS), ensaios de rompimento de corpos de prova de concreto (FCK/slump), laudos de sondagem e auditorias. | Garantia de conformidade com exigências da Caixa Econômica Federal e órgãos de acreditação técnica. |
| **Financeiro, Contábil e Fiscal** | Auditorias contábeis, balancetes, medições de empreiteiros, notas fiscais (XML/PDF) e planilhas (`.xlsx`, `.csv`). | Rastreabilidade de custos corporativos, comprovação fiscal e auditoria de medições. |
| **Meio Ambiente e Segurança (QSMS)** | Licenças ambientais (LI/LO), programas de segurança (PGR/PCMSO), entregas de EPI e treinamentos normativos. | Mitigação de multas ambientais e preservação da integridade do trabalho no canteiro de obras. |

---

## ⚙️ 2. COMO? (Arquitetura de TI, Engenharia de Software e Especificações Técnicas)

O HUDSON DW foi desenvolvido sobre uma arquitetura modular em camadas, utilizando tecnologias de ponta em segurança, banco de dados relacional, busca textual, OCR e inteligência artificial.

```
                     ┌───────────────────────────────────────────────┐
                     │          SISTEMAS & AGENTES DE IA             │
                     │       (DAI, KAN-SA, Dr. SaulLM, Usuários)     │
                     └───────────────────────┬───────────────────────┘
                                             │ OpenVPN (TLS/AES-256)
                                             ▼
                     ┌───────────────────────────────────────────────┐
                     │              CAMADA DE REDE E API             │
                     │        FastAPI HTTP REST (Porta :8000)        │
                     │    Autenticação X-API-Key / Rate Limiting     │
                     └───────┬───────────────────────────────┬───────┘
                             │                               │
             ┌───────────────┴──────────────┐ ┌──────────────┴──────────────┐
             │ CLI INGESTÃO (import_cli.py) │ │ MOTOR DE BUSCA & PROCESSAM.  │
             │ - Hash SHA-256 em Streaming   │ │ - Full-Text Search (tsvector)│
             │ - Captura de Metadados de SO │ │ - RapidFuzz (Busca Fuzzy)    │
             │ - HudsonDesbloqueador        │ │ - ChromaDB (Embeddings BGE-M3)│
             └───────────────┬──────────────┘ └──────────────┬──────────────┘
                             │                               │
                             ▼                               ▼
                     ┌───────────────────────────────────────────────┐
                     │            BANCO POSTGRESQL 18.6              │
                     │          Schema: hudson (Imutável)            │
                     │  - custody_log (Triggers Append-Only)         │
                     │  - items (Proibição estrita de DELETE)        │
                     └───────────────────────────────────────────────┘
```

### Componentes de Software e Tecnologias
1. **API REST (FastAPI / Uvicorn)**: Servidor Python na porta `:8000` para consultas por cota, buscas textuais, emissão de relatórios de saúde (`/health`) e auditoria pericial.
2. **CLI de Ingestão e Orquestrador (`scripts/import_cli.py` / `import_cli_v2.py`)**: Script em linha de comando que realiza varredura recursiva de diretórios, extrai metadados do sistema operacional de origem (usuário de captura, hostname, caminho original, timestamps `mtime`), vincula o identificador da rodada (`ronda_id`) e executa o processamento.
3. **Arsenal Forense e Desbloqueador (*HudsonDesbloqueador*)**: Módulo integrado para tratamento automatizado e remoção de restrições em documentos de texto, planilhas e arquivos compactados (PDFs, Word, Excel, ZIP, RAR) utilizando `pdfplumber`, `liboffice` e `rarfile`.
4. **Banco de Dados Relacional Imutável (PostgreSQL 18.6)**: Schema `hudson` gerenciado via SQLAlchemy 2 e Psycopg2.
5. **Motor de Busca Híbrido**:
   * **Busca Textual Tradicional**: Indexação `tsvector` nativa do PostgreSQL em português com ranking `ts_rank`.
   * **Busca Fuzzy (Tolerante a Falhas)**: Integração com a biblioteca **RapidFuzz** para localização rápida de nomes de arquivos mesmo com erros de digitação.
   * **Busca Vetorial / Semântica**: Integração com **ChromaDB** e modelos de *embeddings* locais (como **BGE-M3**), garantindo que dados confidenciais nunca saiam da infraestrutura soberana.

### Especificações Técnicas e Regras Arquivísticas Negociais

1. **Custódia Imutável (*Append-Only*)**:
   - A tabela `custody_log` (particionada por ano: `custody_log_2025`, `_2026`, `_2027`) armazena o histórico de cada evento (recebimento, roteamento, indexação, consulta).
   - Triggers em PL/pgSQL bloqueiam estritamente qualquer instrução `UPDATE` ou `DELETE` no log. A tabela de itens (`items`) bloqueia qualquer tentativa de `DELETE`.
2. **Regra do Zero Exclusão de Binários**: NENHUM arquivo físico armazenado no disco (`STORAGE_ROOT`) pode ser excluído, garantindo a preservação integral da cadeia de custódia.
3. **Deduplicação Criptográfica em Streaming**:
   - Durante a ingestão, o arquivo tem seu hash SHA-256 calculado em blocos de 1 MiB.
   - Caso o hash já exista na base de dados, a cópia física repetida é descartada e o evento de deduplicação é registrado imutavelmente.
4. **Cota HUDSON Determinística**:
   - Todo ativo digital recebe uma cota única no formato `[ESTANTE]-[WBS]-[AAAA]-[HASH8]` (ex: `document_text-OBRA01-2026-3fa2b9c1`).
   - Em caso de colisão, o fragmento do hash se expande automaticamente de 2 em 2 caracteres até 64.
5. **Classificação em 6 Estantes Temáticas**:
   * `document_text`: `.pdf`, `.docx`, `.txt`, `.rtf` (com OCR via Tesseract para PDFs digitalizados).
   * `communication`: `.eml`, `.msg`, `.pst` (e-mails).
   * `engineering_drawings`: `.dwg`, `.dxf`, `.rvt`, `.ifc` (CAD/BIM).
   * `structured_data`: `.xls`, `.xlsx`, `.csv`, `.xml`, `.json`.
   * `image`: `.jpg`, `.png`, `.tif` (com OCR via Tesseract).
   * `audio_video`: `.mp3`, `.mp4`, `.avi`.
6. **Rastreamento por Rodada / Lote (`ronda_id`)**: Agrupa execuções de ingestão massiva, gerando registros agregados na tabela `historico_rodadas` e isolando falhas na tabela `erro_processamento`.
7. **Segurança e Conectividade**:
   - Conexão remota via túnel privado **OpenVPN** (criptografia TLS + mTLS, AES-256-CBC).
   - Autenticação por chave de API (`X-API-Key`) com suporte a *Rate Limiting* por emissor/agente.

---

## 🎯 3. PORQUÊ? (Dores Resolvidas, Propósito Empresarial e Atendimento BPM/ISO)

### Dores Organizacionais e Processuais Resolvidas

| Antes do HUDSON DW | Com o HUDSON DW |
| :--- | :--- |
| ❌ Arquivos dispersos em pastas de rede, e-mails e WhatsApp. | ✅ Acervo centralizado, indexado por WBS e cota determinística. |
| ❌ Risco de alteração ou deleção acidental/intencional de contratos. | ✅ Custódia *append-only* com proibição estrita de deleção de binários. |
| ❌ Dificuldade de apresentar prova pericial em processos judiciais. | ✅ Endpoint `/authenticity` emite certidão de autenticidade com hash SHA-256. |
| ❌ Gargalo em auditorias de qualidade (ISO 9001 / PBQP-H / Caixa). | ✅ Rastreabilidade completa de FVS, laudos de concreto e projetos por obra. |
| ❌ Agentes de IA bloqueados por falta de acesso seguro ao acervo. | ✅ API REST segura via OpenVPN para integração com DAI, KAN-SA e Dr. SaulLM. |

1. **Eliminação do Caos Documental e Fragmentação de Processos (BPM)**: Normalização automática da entrada de arquivos via WBS (`obra_wbs`), organizando o acervo em estantes temáticas e permitindo buscas em milissegundos.
2. **Garantia de Prova Pericial e Blindagem Jurídica**: O endpoint `/authenticity` recalcula o hash SHA-256 do arquivo em disco e o compara com o log de custódia histórico, emitindo certidões com validade probatória para processos judiciais e fiscalizações.
3. **Conformidade Rigorosa com ISO 9001, PBQP-H e QSMS**: Armazena e vincula FVS (Ficha de Verificação de Serviço), laudos de ensaio de concreto (rompimento/FCK) e comprovantes de entrega de EPI diretamente ao código WBS do empreendimento.
4. **Adequação à LGPD e Rastreabilidade de Origem**: O log de custódia registra a máquina de origem, o usuário de captura, o caminho original e quem consultou cada documento, atrelado a uma matriz de permissões (RBAC).
5. **Alimentação Segura para Agentes de Inteligência Artificial**: Agentes externos como **DAI (Smart Reception)**, **KAN-SA** e **Dr. SaulLM** consultam o HDW via API REST segura sobre VPN privada.

### Quem o HDW Atende?
* **Engenheiros de Obra e Gestores de Qualidade**: Para arquivamento e consulta de projetos, FVS, RDOs e laudos de ensaio normativo vinculados à WBS da obra.
* **Departamento Jurídico e Compliance**: Para emissão de provas periciais imutáveis e defesa em auditorias fiscais e trabalhistas.
* **Auditores Internos e Externos (ISO, PBQP-H, Receita Federal, Caixa Econômica Federal)**: Para verificação do histórico sem risco de adulteração.
* **Agentes de Inteligência Artificial e Sistemas Automáticos**: Para consumo de contexto corporativo seguro e estruturado via API e VPN.
