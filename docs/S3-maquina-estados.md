# S3 — Máquina de Estados do Item (tabela)

Espelha [diagrams/P1-estados-item.mmd](../diagrams/P1-estados-item.mmd). Toda linha
com registro em `custody_log` usa um `event_type` do CHECK definido em
[specs/S2-schema.sql](../specs/S2-schema.sql).

| Estado fonte | Evento | Estado destino | Responsável | Evento no custody_log | Proibições |
|---|---|---|---|---|---|
| (entrada) | Chegada do binário | Recebido | Sistema (API) | `recebimento` | — |
| Recebido | Hash SHA-256 em streaming | Hasheado | Sistema (API) | `recebimento` | Hash nunca recalculado a partir de cópia |
| Hasheado | Formulário declarativo ou metadados automáticos | Declarado | Humano (Zeev) ou Sistema | `recebimento` | Formulário é etiqueta — nunca filtro |
| Declarado | Triagem leve OK (ClamAV, magic bytes, schema, remetente) | Aprovado | Sistema (Quarentena) | `processamento` | — |
| Declarado | Triagem leve falha | Retido | Sistema (Quarentena) | `retencao` (reason obrigatório) | Item nunca é apagado |
| Retido | Encaminhamento | Revisão Humana | Sistema | `retencao` | — |
| Revisão Humana | Analista libera | Liberado → Aprovado | Humano (Analista) | `liberacao` | — |
| Revisão Humana | Analista fecha sem liberar | Retido Permanente | Humano (Analista) | `retencao` | Estado terminal — nunca reaberto automaticamente; NUNCA excluído |
| Aprovado | Verificação de hash exato — hash inédito | Original | Sistema | `deduplicacao` | — |
| Aprovado | Verificação de hash exato — hash já existe | Duplicata | Sistema | `deduplicacao` | Duplicata nunca é removida — apenas marcada via `is_duplicate_of` |
| Original | Roteamento pelas 6 Estantes | Roteado | Sistema | `roteamento` | Roteamento é determinístico, não heurístico |
| Roteado | OCR + NER | OCR/NER Processado | Sistema (Celery + LLM) | `processamento` | — |
| OCR/NER Processado | NER falha ou inconclusiva | Falha LLM → Flagged Reprocess | Sistema | `falha_llm` | Pipeline principal NÃO é bloqueado — ver P6 |
| Flagged Reprocess | Worker tenta novamente | volta a OCR/NER Processado | Sistema (Worker) | `reprocessamento` | Limite de N tentativas |
| Flagged Reprocess | Limite de tentativas excedido | Revisão Humana | Sistema → Humano | `reprocessamento` | — |
| OCR/NER Processado | Resolução de entidades bem-sucedida | Entidades Resolvidas | Sistema (LLM) | `processamento` | Merge crítico de pessoas nunca é automático — ver D3 (Fase 3) |
| Entidades Resolvidas | Indexação tsvector + ChromaDB | Indexado | Sistema | `indexacao` | — |
| Indexado | Lock de custódia | Locked (processed) | Sistema | `lock_custodia` | A partir daqui, binário e `custody_log` do item são imutáveis |
| Locked | Consulta via endpoints ou Chat Tradutor | Consultado | Sistema (a pedido do Consumidor) | `consulta` | Consulta nunca altera o estado do item |
| Consultado | Nova consulta | Consultado (mesmo estado) | Sistema | `consulta` (novo registro a cada consulta) | — |

## Transições proibidas (explícitas em todo o sistema)

| De | Para | Por quê |
|---|---|---|
| Qualquer estado | Excluído | Zero Exclusão (P3) — nenhuma rota apaga ou sobrescreve o binário original; ver notas em P1 |
| Retido Permanente | Excluído | Retenção permanente não é exclusão — o item continua endereçável |
| Duplicata | Excluído | Duplicata é marcada via `is_duplicate_of`, nunca removida |
| Locked | qualquer estado de edição/exclusão | A partir do lock, só metadados de índice podem ser reprocessados (fluxo WATSON S2 → `s1_audit_findings`) |
| (qualquer linha de `custody_log`) | UPDATE ou DELETE | `custody_log` é append-only — bloqueado por trigger de banco em `specs/S2-schema.sql` |
