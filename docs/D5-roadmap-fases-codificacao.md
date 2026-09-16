# D5 — Roadmap de Fases de Codificação

**Status:** recomendação — aguardando aprovação humana.

## Recomendação

| Fase de código | Escopo | Esforço relativo |
|---|---|---|
| **1 — MVP** | Recepção webhook (`POST /items`), hash SHA-256 em streaming, quarentena (4 validações leves), `custody_log`, Object Storage (MinIO) | Médio — fundação do sistema, mas escopo contido a ingestão e custódia |
| **2** | Deduplicação exata, roteamento pelas 6 Estantes, OCR Tesseract, indexação (tsvector + ChromaDB), geração da Cota HUDSON | Alto — motor de processamento e integração com Tesseract/ChromaDB |
| **3** | NER, Resolução de Entidades, Chat Tradutor, telemetria para MYCROFT S4 | Alto — integração da LLM, prompt engineering, governança de IA |
| **4** | `/authenticity`, RBAC completo, tarjamento LGPD em exportações, varredura de integridade periódica | Médio — em grande parte composição do que já existe nas fases anteriores, mais testes de segurança |

## Ordem de commit sugerida dentro da Fase 1

1. `specs/S2-schema.sql` aplicado via Alembic (schema `hudson`)
2. Modelos SQLAlchemy espelhando o schema
3. `GET /health`
4. `POST /items` — hash em streaming + primeiro registro em `custody_log` + resposta `201`/`200` idempotente
5. Quarentena — as 4 validações leves e o estado `retido`
6. Fila de revisão humana (liberação manual)

## Tradeoffs

| Critério | Ordem proposta (ingestão → processamento → IA → consumo) | Ordem alternativa (consumo cedo, para demo) |
|---|---|---|
| Risco de retrabalho | Baixo — cada fase depende apenas da anterior | Maior — endpoints de leitura ficariam sem dado real para consultar até a Fase 2/3 |
| Valor demonstrável cedo | Menor no curto prazo | Maior — dashboard/demo funcional mais rápido, mas sobre dados incompletos |
| Alinhamento com o contexto único | Alto — replica a ordem P1→P8 dos diagramas e a trava de custódia desde a entrada | Baixo — inverteria a prioridade de "hash primeiro" estabelecida como inegociável |

A ordem proposta segue a mesma sequência lógica da Fase 1 de diagramas (P1 a P8) e do
contexto único (P1 — hash primeiro): nada é consultável de forma significativa antes
de existir com integridade custodiada.
