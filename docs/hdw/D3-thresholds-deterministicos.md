# D3 — Thresholds Determinísticos (Dedup Semântico e Resolução de Entidades)

**Status:** recomendação — aguardando aprovação humana.

## Dedup semântico (complementar à dedup exata por hash)

A dedup exata (`is_duplicate_of`, por `hash_sha256`) já é automática e determinística
(P3 do contexto único). A dedup **semântica** aqui é um sinal adicional, mais fraco,
para itens que não são bit-a-bit idênticos mas são conteudisticamente quase iguais
(ex.: mesmo contrato exportado duas vezes em formatos diferentes).

| Similaridade (embeddings) | Ação |
|---|---|
| ≥ 0.95 | Marca como quase-duplicata (flag informativo) — não gera `is_duplicate_of`, pois os hashes são diferentes; ambos os itens continuam existindo e sendo custodiados |
| ≥ 0.85 e < 0.95 | Envia para fila de revisão humana — analista decide se são de fato relacionados |
| < 0.85 | Nenhuma ação — considerados itens distintos |

## Resolução de entidades (fuzzy matching)

| Tipo de entidade | Regra de merge |
|---|---|
| PJ / CNPJ, valores, datas, WBS (dados estruturados e objetivos) | Merge automático permitido quando a similaridade de texto normalizado (distância de edição) for ≥ 0.90 |
| PF (pessoa física) | **Nunca merge automático**, mesmo com similaridade de nome igual a 1.0 — sempre vai para fila de revisão humana |

A vedação de merge automático para PF é uma regra dura, não um threshold — mesmo dois
nomes idênticos podem ser pessoas homônimas distintas, e o Agente de IA é vedado de
qualquer juízo de valor sobre identidade de pessoas (P5 do contexto único). Esta regra
é coberta por teste explícito em [docs/S6-testes.md](S6-testes.md).

## Tradeoffs

| Critério | Thresholds mais permissivos | Thresholds mais conservadores (recomendado) |
|---|---|---|
| Volume da fila de revisão humana | Menor — menos itens escalados | Maior — mais itens exigem analista |
| Risco de merge incorreto | Maior — pode fundir entidades distintas | Menor — erra para o lado de pedir revisão |
| Velocidade de catalogação | Maior | Menor, mas mais confiável |
| Adequação a um acervo forense | Baixa — erro de merge compromete prova | Alta — prioriza confiabilidade sobre velocidade |
