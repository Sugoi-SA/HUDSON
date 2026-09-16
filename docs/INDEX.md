# Índice Mestre — Sugoi-SA/HUDSON (Sistema HUDSON S1)

Mapa de toda a documentação do repositório, com status individual. Visão geral e
arquitetura resumida estão no [`README.md`](../README.md) da raiz.

## Diagramas existentes (raiz do repositório) — não tocados neste pacote

| # | Arquivo | Tipo | Status |
|---|---|---|---|
| 1 | [`01-c4-contexto.mmd`](../01-c4-contexto.mmd) | `C4Context` | ✅ validado (herdado) |
| 2 | [`02-sequencia-ingestao.mmd`](../02-sequencia-ingestao.mmd) | `sequenceDiagram` | ✅ validado (herdado) |
| 3 | [`03-flowchart-completo.mmd`](../03-flowchart-completo.mmd) | `flowchart TD` | ✅ validado (herdado) |
| 4 | [`04-c4-container-nivel2.mmd`](../04-c4-container-nivel2.mmd) | `C4Container` | ✅ validado (herdado) |
| 5 | [`05-c4-component-nivel3.mmd`](../05-c4-component-nivel3.mmd) | `C4Component` | ✅ validado (herdado) |

## Diagramas novos — Fase 1 (`diagrams/`)

| # | Arquivo (.mmd + .md) | Tipo | Status |
|---|---|---|---|
| P1 | [`diagrams/P1-estados-item`](../diagrams/P1-estados-item.md) | `stateDiagram-v2` | ✅ concluído |
| P2 | [`diagrams/P2-deployment-fisico`](../diagrams/P2-deployment-fisico.md) | `flowchart TB` | ✅ concluído |
| P3 | [`diagrams/P3-schema-hudson`](../diagrams/P3-schema-hudson.md) | `erDiagram` | ✅ concluído |
| P4 | [`diagrams/P4-trava-assincrona-zeev-sla`](../diagrams/P4-trava-assincrona-zeev-sla.md) | `sequenceDiagram` | ✅ concluído |
| P5 | [`diagrams/P5-consumo-biblioteca-soberana`](../diagrams/P5-consumo-biblioteca-soberana.md) | `sequenceDiagram` | ✅ concluído |
| P6 | [`diagrams/P6-excecao-llm-reprocessamento`](../diagrams/P6-excecao-llm-reprocessamento.md) | `flowchart TD` | ✅ concluído |
| P7 | [`diagrams/P7-afericao-autenticidade-sob-demanda`](../diagrams/P7-afericao-autenticidade-sob-demanda.md) | `sequenceDiagram` | ✅ concluído |
| P8 | [`diagrams/P8-varredura-integridade-acervo`](../diagrams/P8-varredura-integridade-acervo.md) | `flowchart TD` | ✅ concluído |

## Especificações — Fase 2 (`docs/` + `specs/`)

| Item | Arquivo | Status |
|---|---|---|
| S1 | [`specs/S1-openapi.yaml`](../specs/S1-openapi.yaml) | ✅ concluído |
| S2 | [`specs/S2-schema.sql`](../specs/S2-schema.sql) | ✅ concluído |
| S3 | [`docs/S3-maquina-estados.md`](S3-maquina-estados.md) | ✅ concluído |
| S4 | [`docs/S4-rbac-lgpd-matrix.md`](S4-rbac-lgpd-matrix.md) | ✅ concluído |
| S5 | [`docs/S5-nfrs-e-operacao.md`](S5-nfrs-e-operacao.md) | ✅ concluído |
| S6 | [`docs/S6-testes.md`](S6-testes.md) | ✅ concluído |
| S7 | [`docs/S7-metadados-por-estante.md`](S7-metadados-por-estante.md) | ✅ concluído |
| S8 | [`docs/S8-cota-hudson.md`](S8-cota-hudson.md) | ✅ concluído |

**Decisão de organização (Fase 0):** `docs/` recebe especificações narrativas em
Markdown (S3-S8); `specs/` recebe contratos máquina-legíveis (S1 `openapi.yaml`, S2
`schema.sql`).

## Decisões aprováveis — Fase 3 (`docs/`)

Nenhuma foi decidida unilateralmente — todas aguardam aprovação humana antes de virar
padrão de implementação (P6 do contexto único).

| Item | Arquivo | Status |
|---|---|---|
| D1 | [`docs/D1-llm-local-vs-api.md`](D1-llm-local-vs-api.md) | ⏳ recomendação — aguardando aprovação |
| D2 | [`docs/D2-embeddings-ptbr.md`](D2-embeddings-ptbr.md) | ⏳ recomendação — aguardando aprovação |
| D3 | [`docs/D3-thresholds-deterministicos.md`](D3-thresholds-deterministicos.md) | ⏳ recomendação — aguardando aprovação |
| D4 | [`docs/D4-seguranca-cibernetica.md`](D4-seguranca-cibernetica.md) | ⏳ recomendação — aguardando aprovação |
| D5 | [`docs/D5-roadmap-fases-codificacao.md`](D5-roadmap-fases-codificacao.md) | ⏳ recomendação — aguardando aprovação |

## Documentação de referência (local, fora deste repositório GitHub)

Existe apenas na cópia de trabalho local (OneDrive), não publicada neste repositório —
listada aqui só para rastreabilidade de onde veio o contexto usado neste pacote.

| Arquivo local | Conteúdo | Status |
|---|---|---|
| `Claude-Biblioteca/README.md` | Índice original dos 5 diagramas existentes + notas técnicas Mermaid/C4 (conteúdo já incorporado ao README.md da raiz) | referência local — não publicado |
| `KLM_BIBLIOTECA/hudson-s4-guia-implementacao-v6.md` | Guia de implementação do MYCROFT S4 (versão 6) | referência local — não publicado |
| `KLM_BIBLIOTECA/hudson-s4-guia-implementacao-v7.md` / `.docx` | Guia de implementação do MYCROFT S4 (versão 7) | referência local — não publicado |
| `KLM_BIBLIOTECA/hudson-s4-guia-implementacao-v8.md` | Guia de implementação do MYCROFT S4 (versão 8 — mais recente) | referência local — não publicado |

## Status geral do pacote de engenharia

| Fase | Status |
|---|---|
| 0 — Preparação | ✅ concluída |
| 1 — 8 diagramas novos | ✅ concluída |
| 2 — Especificações S1-S8 | ✅ concluída |
| 3 — Decisões D1-D5 | ✅ concluída (recomendações; aprovação humana pendente) |
| 4 — Fechamento (README final + este índice) | ✅ concluída |
