# Sugoi-SA/HUDSON — Sistema HUDSON (S1)

Biblioteca Soberana da SUGOI S.A.: custodiante forense + data warehouse corporativo.
Hash SHA-256 em streaming na recepção, custódia append-only (`custody_log`), zero
exclusão de binário, base agnóstica de hipótese e consulta que jamais bloqueia
ingestão — a trava é sempre de ingestão, nunca de leitura.

Todo item do acervo é:

- **Endereçável** — Cota HUDSON única e determinística ([S8](docs/S8-cota-hudson.md)).
- **Verificável** — hash SHA-256 recomputável sob demanda + cadeia de custódia
  completa ([P5](diagrams/P5-consumo-biblioteca-soberana.md),
  [P7](diagrams/P7-afericao-autenticidade-sob-demanda.md),
  [P8](diagrams/P8-varredura-integridade-acervo.md)).
- **Relacional** — entidades e vínculos prontos para cruzamento por terceiros
  (`entities`/`relationships`), no espírito da Library of Congress / LCC / MARC: um
  catálogo estruturado, reutilizável por quem consome.

Este README é o índice mestre do repositório. Índice completo com status de cada
documento em [`docs/INDEX.md`](docs/INDEX.md).

## Estrutura do repositório

```
.
├── README.md                  # este arquivo — índice mestre
├── 01-c4-contexto.mmd          # 5 diagramas de arquitetura já existentes (não tocados)
├── 02-sequencia-ingestao.mmd
├── 03-flowchart-completo.mmd
├── 04-c4-container-nivel2.mmd
├── 05-c4-component-nivel3.mmd
├── docs/                       # especificações narrativas (S3-S8), decisões (D1-D5) e INDEX.md
├── diagrams/                   # os 8 diagramas novos (P1-P8), cada um em .mmd + .md
└── specs/                      # contratos formais/máquina-legíveis (openapi.yaml, schema.sql)
```

## Arquitetura — diagramas existentes (mapeados na Fase 0, não reescritos)

Fonte de verdade da arquitetura macro, já presente no repositório antes deste pacote
de engenharia. Referenciados pelos 8 diagramas novos e pelas especificações.

| # | Arquivo | Tipo Mermaid | Escopo |
|---|---|---|---|
| 1 | [`01-c4-contexto.mmd`](01-c4-contexto.mmd) | `C4Context` | C4 Nível 1 — Contexto do sistema: HUDSON S1 e as 4 fontes de entrada, WATSON S2, HOLMES S3, MYCROFT S4, consumidores |
| 2 | [`02-sequencia-ingestao.mmd`](02-sequencia-ingestao.mmd) | `sequenceDiagram` | Ingestão e processamento ponta a ponta: hash → custody_log → quarentena → núcleo → agente IA → indexação → lock |
| 3 | [`03-flowchart-completo.mmd`](03-flowchart-completo.mmd) | `flowchart TD` | Flowchart completo alternativo e estável ao C4, cobrindo todos os ramos de decisão |
| 4 | [`04-c4-container-nivel2.mmd`](04-c4-container-nivel2.mmd) | `C4Container` | C4 Nível 2 — Containers: API, Quarentena, Celery Workers, PostgreSQL, Redis, ChromaDB, Object Storage, Agente de IA |
| 5 | [`05-c4-component-nivel3.mmd`](05-c4-component-nivel3.mmd) | `C4Component` | C4 Nível 3 — Componentes do Agente de IA (Modelo + Harness): System Prompt, Memória, Ferramentas, Contexto, Subagents, Skill, NER, Resolução, Chat Tradutor, Telemetria |

Notas técnicas herdadas da versão anterior deste README: `SHOW_LEGEND()` quebra o
parser Mermaid C4 (removida dos 3 diagramas C4) e `Container_Bound` foi corrigido para
`Container_Boundary`.

## Arquitetura — diagramas novos (Fase 1)

| # | Arquivo | Tipo Mermaid | Escopo |
|---|---|---|---|
| P1 | [`diagrams/P1-estados-item.mmd`](diagrams/P1-estados-item.mmd) / [`.md`](diagrams/P1-estados-item.md) | `stateDiagram-v2` | Estados do item — recebido a consultado, ciclo de retido/revisão/liberado, reprocessamento por falha de LLM, proibições explícitas de exclusão |
| P2 | [`diagrams/P2-deployment-fisico.mmd`](diagrams/P2-deployment-fisico.mmd) / [`.md`](diagrams/P2-deployment-fisico.md) | `flowchart TB` (estável, equivalente a C4 Deployment) | Camada física: Ubuntu Server, Docker Compose, rede `seg_quarentena` isolada vs. rede `core`, volumes nomeados, portas publicadas (8000 API, 9000 MinIO), API como única ponte entre redes, nenhum segredo no compose |
| P3 | [`diagrams/P3-schema-hudson.mmd`](diagrams/P3-schema-hudson.mmd) / [`.md`](diagrams/P3-schema-hudson.md) | `erDiagram` | Schema `hudson`: `items` (hash_sha256 UNIQUE, cota UNIQUE, FK self `duplicate_of_item_id`), `entities`, `relationships`, `custody_log` (event_type com CHECK de categorias), `declarations`, `estant_types` (enum das 6 Estantes) |
| P4 | [`diagrams/P4-trava-assincrona-zeev-sla.mmd`](diagrams/P4-trava-assincrona-zeev-sla.mmd) / [`.md`](diagrams/P4-trava-assincrona-zeev-sla.md) | `sequenceDiagram` | Trava assíncrona do Zeev com SLA completo: tarefa aberta → arquivo chega por outro canal → HUDSON confirma por qualquer canal → Zeev fecha; alternativas de timeout de SLA (bloqueio/escalonamento) e confirmação duplicada (idempotência) |
| P5 | [`diagrams/P5-consumo-biblioteca-soberana.mmd`](diagrams/P5-consumo-biblioteca-soberana.mmd) / [`.md`](diagrams/P5-consumo-biblioteca-soberana.md) | `sequenceDiagram` | Consumo: autenticação → RBAC → (a) Chat Tradutor (linguagem natural → filtros determinísticos → tsvector + ChromaDB) ou (b) `/authenticity` (recomputa SHA-256, compara, certidão ou alerta crítico a MYCROFT S4); toda consulta grava evento no custody_log antes de retornar |
| P6 | [`diagrams/P6-excecao-llm-reprocessamento.mmd`](diagrams/P6-excecao-llm-reprocessamento.mmd) / [`.md`](diagrams/P6-excecao-llm-reprocessamento.md) | `flowchart TD` | Exceção da LLM: falha/inconclusão de NER → telemetria (llmops_telemetry) → item segue com extração parcial e flag_reprocess sem bloquear o pipeline → worker de reprocessamento tenta N vezes → escalonamento para revisão humana após o limite |
| P7 | [`diagrams/P7-afericao-autenticidade-sob-demanda.mmd`](diagrams/P7-afericao-autenticidade-sob-demanda.mmd) / [`.md`](diagrams/P7-afericao-autenticidade-sob-demanda.md) | `sequenceDiagram` | Aferição de autenticidade sob demanda (advogado/due diligence) via `/authenticity`: recomputa SHA-256, compara, certidão com cadeia de custódia integral ou divergência crítica notificada a MYCROFT S4; mesma rota do item (b) de P5, aqui detalhada para o cenário de prova pericial — rota idempotente por hash |
| P8 | [`diagrams/P8-varredura-integridade-acervo.mmd`](diagrams/P8-varredura-integridade-acervo.mmd) / [`.md`](diagrams/P8-varredura-integridade-acervo.md) | `flowchart TD` | Varredura de integridade periódica: Celery Beat → lote de itens → recomputa SHA-256 e compara com `items.hash_sha256` → item íntegro segue, divergente é bloqueado de **leitura** (nunca removido) + alerta + revisão humana + MYCROFT S4; verifica também a integridade estrutural (append-only) do `custody_log`; relatório final enviado a MYCROFT S4 |

Convenção: nenhum diagrama tem seta de exclusão de binário; a aferição de documento já
existente aparece intencionalmente em dois diagramas (P5b e P7) e em um endpoint (S1 —
idempotência por hash), cobrindo tanto o fluxo geral de consumo quanto o cenário de
prova pericial dedicado.

## Pacote de especificações (Fase 2)

| Item | Arquivo | Conteúdo |
|---|---|---|
| S1 | [`specs/S1-openapi.yaml`](specs/S1-openapi.yaml) | Contrato OpenAPI 3.1 — `POST /items` (6 emissores + upload humano), 5 endpoints de leitura, `/health`, idempotência por hash |
| S2 | [`specs/S2-schema.sql`](specs/S2-schema.sql) | DDL PostgreSQL 15 — deriva de P3; `custody_log` particionado por ano e append-only (trigger bloqueia UPDATE/DELETE), `items` protegido contra DELETE |
| S3 | [`docs/S3-maquina-estados.md`](docs/S3-maquina-estados.md) | Máquina de estados em tabela — deriva de P1; inclui transições proibidas explícitas |
| S4 | [`docs/S4-rbac-lgpd-matrix.md`](docs/S4-rbac-lgpd-matrix.md) | Matriz RBAC (6 perfis × 6 operações, `delete` proibido a todos) + regras de tarjamento LGPD por campo em exportações |
| S5 | [`docs/S5-nfrs-e-operacao.md`](docs/S5-nfrs-e-operacao.md) | NFRs mensuráveis (hash, busca, OCR, SLA), backup/restore, observabilidade, retenção de 10 anos |
| S6 | [`docs/S6-testes.md`](docs/S6-testes.md) | Golden files forenses, fixtures de webhook por emissor, testes das vedações do agente, testes de integridade e de idempotência |
| S7 | [`docs/S7-metadados-por-estante.md`](docs/S7-metadados-por-estante.md) | "MARC do HUDSON" — campos e indexabilidade (tsvector/ChromaDB) por uma das 6 Estantes |
| S8 | [`docs/S8-cota-hudson.md`](docs/S8-cota-hudson.md) | Especificação da Cota HUDSON — `[ESTANTE]-[WBS]-[AAAA]-[hash8]`, geração determinística, resolução de colisão, expansível sem reclassificar |

**Decisão de organização (registrada na Fase 0):** `docs/` recebe as especificações
narrativas em Markdown (S3-S8), enquanto `specs/` recebe os 2 contratos
máquina-legíveis (S1 `openapi.yaml`, S2 `schema.sql`) — critério: prosa vs. contrato
formal.

## Decisões aprováveis (Fase 3)

Recomendação + tradeoffs — nenhuma decisão foi tomada unilateralmente; todas aguardam
aprovação humana antes de virar padrão de implementação.

| Item | Arquivo | Recomendação (resumo) |
|---|---|---|
| D1 | [`docs/D1-llm-local-vs-api.md`](docs/D1-llm-local-vs-api.md) | LLM local (open-source, no próprio Ubuntu Server) para NER, Resolução de Entidades e Chat Tradutor — dado pericial nunca sai do servidor |
| D2 | [`docs/D2-embeddings-ptbr.md`](docs/D2-embeddings-ptbr.md) | BGE-M3 local (alternativa: multilingual-e5-large); chunking por unidade natural de cada Estante (cláusula, e-mail, página), não por tamanho fixo |
| D3 | [`docs/D3-thresholds-deterministicos.md`](docs/D3-thresholds-deterministicos.md) | Dedup semântico ≥0.95 flag / ≥0.85 revisão humana; merge automático de entidades só para PJ/CNPJ/valores/datas/WBS — **nunca** para PF, sempre revisão humana |
| D4 | [`docs/D4-seguranca-cibernetica.md`](docs/D4-seguranca-cibernetica.md) | Egress zero, segredos via Docker secrets (nunca `.env` versionado), rate limiting por emissor, hardening do Ubuntu (sshd, ufw, fail2ban) |
| D5 | [`docs/D5-roadmap-fases-codificacao.md`](docs/D5-roadmap-fases-codificacao.md) | 4 fases de código (MVP → processamento → IA/governança → aferição/RBAC/LGPD), com ordem de commit sugerida para a Fase 1 |

## Roadmap de codificação (resumo de D5)

| Fase de código | Escopo | Esforço relativo |
|---|---|---|
| 1 — MVP | Webhook, hash em streaming, quarentena, `custody_log`, Object Storage | Médio |
| 2 | Dedup exata, 6 Estantes, OCR, indexação, Cota HUDSON | Alto |
| 3 | NER, Resolução de Entidades, Chat Tradutor, telemetria MYCROFT S4 | Alto |
| 4 | `/authenticity`, RBAC, tarjamento LGPD, varredura de integridade | Médio |

Detalhes e ordem de commit sugerida em [`docs/D5-roadmap-fases-codificacao.md`](docs/D5-roadmap-fases-codificacao.md).

## Convenções do repositório

- Cada diagrama novo (P1-P8) é 1 arquivo `.mmd` + 1 arquivo `.md` (mesmo conteúdo, com
  fence ```` ```mermaid ````), indexado neste README por uma linha.
- Rótulos Mermaid sem acentuação (compatibilidade ampla de renderizador), sintaxe
  validada contra mermaid.live; nenhum diagrama tem seta de exclusão de binário.
- Cada especificação (S1-S8) e cada decisão (D1-D5) é 1 arquivo próprio, nomeado
  `S<n>-slug.ext` / `D<n>-slug.md`.
- `custody_log` é append-only em todas as camadas: modelagem (P3), schema com trigger
  (S2) e regra de RBAC (S4 — `delete` proibido a todos os perfis).
- Toda consulta de qualquer consumidor gera 1 registro em `custody_log` antes de
  retornar — modelado nos 4 diagramas de consumo/aferição (P5, P7, P8) e no
  endpoint correspondente (S1).

## Status do pacote de engenharia

| Fase | Conteúdo | Status |
|---|---|---|
| 0 | Preparação — estrutura de pastas, mapeamento dos 5 diagramas existentes | ✅ concluída |
| 1 | 8 diagramas novos (`diagrams/`) — estados, deployment, ER, sequências, exceção LLM, integridade | ✅ concluída |
| 2 | Especificações de engenharia (`docs/` + `specs/`) — S1 a S8 | ✅ concluída |
| 3 | Decisões aprováveis (D1-D5) — recomendação + tradeoffs, sem decidir sozinho | ✅ concluída |
| 4 | Fechamento — README.md final e `docs/INDEX.md` | ✅ concluída |

Índice completo por arquivo, com status individual, em [`docs/INDEX.md`](docs/INDEX.md).
