# V0 — Status e histórico de avanço

Este documento existe para responder, sem precisar reconstruir conversas anteriores,
duas perguntas: **de onde saímos** e **onde estamos agora**. É atualizado a cada rodada
relevante de trabalho no v0 do backend HUDSON S1.

## De onde saímos

Em 2026-09-22 (commit `3a41cba`), o v0 era um protótipo funcional do núcleo do pipeline
forense (hash SHA-256 → dedup → roteamento por Estante → cópia em custódia → Cota HUDSON
→ OCR/extração → índice full-text em português), implementado como um único arquivo
`main.py` com FastAPI, sem separação de camadas, sem autenticação, sem testes
automatizados, e nunca antes testado em um servidor físico real.

## Auditoria de 2026-09-24

Uma auditoria técnica formal (QA/segurança/arquitetura) foi realizada sobre a Fase 1
completa, comparando a implementação contra as especificações do projeto
(`specs/S1-openapi.yaml`, `docs/S4-rbac-lgpd-matrix.md`, `docs/S5-nfrs-e-operacao.md`,
`docs/S6-testes.md`). **Veredito: NÃO APROVAR**, com 4 achados bloqueadores, 4 críticos,
4 altos e 5 médios/baixos. Os bloqueadores incluíam: frontend inexistente, ausência total
de autenticação, endpoint oficial de ingestão (`POST /items`) inexistente, e zero testes
automatizados no repositório.

Diante do escopo, ficou definido que **esta rodada foca apenas em homologar o núcleo
backend + banco (v0)**, deixando frontend, RBAC completo, canais oficiais de ingestão e
integrações (Zeev, SIENGE etc.) para uma Fase 1.1/1.2 explicitamente separada. Também
ficou definido que backend e frontend devem ser tratados como camadas independentes,
comunicando-se por contrato bem definido (schemas Pydantic + OpenAPI gerado), para que o
crescimento de escopo futuro não exija reescrever partes já prontas.

## O que foi corrigido (com evidência de teste real, não apenas leitura de código)

| Commit | O quê | Evidência de validação |
|---|---|---|
| [`21e9ce4`](../../commit/21e9ce4) | Compatibilidade com Python 3.8 (o runtime disponível no servidor CentOS 7): trocada sintaxe `X \| None` / `dict[str, str]` (exige Python 3.9/3.10+) por `Optional`/`Dict`/`List` do `typing` | Import de teste e os 4 endpoints da API rodando sem erro no servidor real |
| [`830ed44`](../../commit/830ed44) | Reorganização do backend em camadas: `routers/` (HTTP), `services/` (regra de negócio), `schemas/` (contrato Pydantic da API), `repositories/` (acesso a dado) | Mesmo comportamento confirmado byte-a-byte nos 4 endpoints e no import CLI, antes e depois da reorganização |
| [`09b49dd`](../../commit/09b49dd) | Três bloqueadores do v0: (1) autenticação por API key em `/search` e `/items/{cota}`; (2) corrida de concorrência na deduplicação por hash tratada como duplicata em vez de erro; (3) verificação de integridade SHA-256 logo após a cópia em custódia, com alerta e status `falha_processamento` em caso de divergência | Testes reais executados: 6 cenários de autenticação (401/200 corretos); 2 processos de import simultâneos contra o mesmo arquivo novo produzindo exatamente 1 item novo + 1 duplicata sem erros; destino corrompido manualmente detectado e colocado em quarentena de ponta a ponta pelo pipeline real |
| `(próximo)` | Suíte `pytest` automatizada (22 testes) cobrindo hashing, roteamento, geração de Cota, dedup, indexação, verificação de integridade e o teste de concorrência real (threads simultâneas) exigido em `docs/S6-testes.md` — roda contra o PostgreSQL de verdade, não mock, usando transação com savepoint para não poluir o acervo Zero Exclusão (exceto o teste de concorrência, que precisa de duas transações reais e por isso fica com uma linha residual por execução, tagueada `obra_wbs='PYTEST_CONC'`) | `pytest` executado no servidor: 22 passed em 1.35s |

## Onde estamos agora

| Item | Status |
|---|---|
| Servidor Linux (CentOS 7) com PostgreSQL 15 | Funcionando, testado |
| Backend core (hash/dedup/roteamento/OCR/busca) | Funcionando, arquitetura em camadas, testado manualmente |
| Autenticação mínima (API key) | Implementada e validada |
| Corrida em deduplicação | Corrigida e validada com teste de concorrência real |
| Integridade pós-cópia | Implementada e validada (detecção + quarentena) |
| Testes automatizados formais | Implementados — 22 testes `pytest`, rodando contra Postgres real |
| Processo da API supervisionado (systemd) | **Pendente** — hoje roda via `nohup` manual |
| Backup (Postgres + `hudson_storage`) | **Pendente** |
| SO/runtime (CentOS 7 e Python 3.8, ambos EOL) | **Pendente decisão** de migração |
| Frontend | Fora de escopo desta rodada (Fase 1.1/1.2) |
| RBAC completo, `POST /items` oficial, `/authenticity`, filas | Fora de escopo desta rodada (Fase 1.1/1.2) |

## Próximos passos (em ordem sugerida)

1. ~~Testes automatizados mínimos~~ — concluído
2. Unidade systemd para a API, substituindo o processo manual
3. Backup do PostgreSQL e do `hudson_storage`
4. Decisão sobre migração de SO/Python (ambos oficialmente end-of-life)
