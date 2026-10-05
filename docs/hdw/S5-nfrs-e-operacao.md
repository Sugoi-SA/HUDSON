# S5 — NFRs e Operação

## NFRs mensuráveis

| # | Requisito | Meta | Onde se aplica |
|---|---|---|---|
| NFR-1 | Hash SHA-256 em streaming | < 10 ms por MB | Recepção — antes de qualquer outra etapa (P1 hash primeiro) |
| NFR-2 | Latência de busca (`/search`, Chat Tradutor) | p95 < 2 s | Consumo — diagrama P5 |
| NFR-3 | OCR Tesseract camada dupla | p95 < 30 s por 50 páginas | Núcleo — pipeline OCR/NER |
| NFR-4 | Trava síncrona do Zeev (`POST /items` → HTTP 201) | < 5 s ponta a ponta | Recepção — falha aqui bloqueia a etapa de negócio no Zeev |
| NFR-5 | Backup do Object Storage | diário, incremental | Infraestrutura |
| NFR-6 | Teste de restore do backup | mensal, restauração completa validada | Infraestrutura |
| NFR-7 | Observabilidade mínima | métricas + logs estruturados por contêiner | Todos os containers do compose (ver P2) |
| NFR-8 | Retenção de `custody_log` | 10 anos, sem exceção | Custódia — base legal Art. 158-A a 158-F do CPP |
| NFR-9 | Exclusão de binário ou linha de custódia | nunca — 0 ocorrências toleradas | Todo o sistema — P3 (Zero Exclusão), reforçado por trigger de banco (S2) |
| NFR-10 | Varredura de integridade periódica | cobre 100% do acervo `processed` em ciclo definido pela operação | Celery Beat — diagrama P8 |

## Backup e restore

- Object Storage: backup diário incremental para um segundo volume/bucket fora do host
  de produção. O backup nunca substitui o volume `object_storage_data` — é cópia
  adicional, nunca migração.
- PostgreSQL: `pg_dump`/WAL archiving diário, incluindo as partições de `custody_log`.
- Teste de restore mensal: restaurar o backup mais recente em ambiente isolado e validar
  `/authenticity` de uma amostra de itens antes de considerar o backup válido.

## Observabilidade mínima

- Métricas por contêiner: uso de CPU/memória, latência de request (API), profundidade
  das filas Redis, taxa de falha de NER (`falha_llm` no `custody_log`).
- Logs estruturados (JSON) por contêiner, com correlação por `item_id` quando aplicável.
- Alertas obrigatórios: divergência de integridade (`alerta_integridade`), SLA do Zeev
  vencido, fila de revisão humana acima de um limiar, falha de backup.

## Retenção e exclusão

- `custody_log`: retenção mínima de 10 anos; partições antigas nunca são removidas pela
  aplicação — eventual arquivamento frio é decisão de infraestrutura, não de exclusão.
- Binários no Object Storage: retenção indefinida — não há rotina de expurgo. O volume
  cresce de forma monotônica por desenho (P4 do contexto único — Pesca de Rede).
