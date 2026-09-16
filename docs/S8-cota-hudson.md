# S8 — Cota HUDSON (endereço único do item)

Referência de desenho: Library of Congress Classification (LCC) — um endereço curto,
determinístico e permanente, atribuído uma única vez e nunca renomeado, mesmo quando o
conhecimento sobre o item evolui depois (nova relação, novo vínculo de obra). A
catalogação adicional acontece via `entities`/`relationships`, nunca reescrevendo a
Cota já emitida.

## Formato

```
[ESTANTE]-[EMPREENDIMENTO_WBS]-[AAAA]-[8 chars do SHA-256]
```

Exemplo: `ENG-TORRE_NORTE-2026-a1b2c3d4`

| Segmento | Origem | Regra |
|---|---|---|
| `ESTANTE` | `items.estante` | Código curto de 3 letras (tabela de abreviação abaixo) |
| `EMPREENDIMENTO_WBS` | `items.obra_wbs` | Normalizado: maiúsculas, sem acentos, espaços viram `_`, truncado em 20 caracteres |
| `AAAA` | `items.received_at` | Ano em que o HUDSON custodiou o item — não a data do fato/documento |
| `8 chars do SHA-256` | `items.hash_sha256` | 8 primeiros caracteres hexadecimais, minúsculos |

## Abreviação de Estante

| `estant_types.codigo` | Abreviação na Cota |
|---|---|
| document_text | `DOC` |
| communication | `COM` |
| engineering_drawings | `ENG` |
| structured_data | `STR` |
| image | `IMG` |
| audio_video | `AVD` |

## Geração determinística

```
estante_code   = ABREVIA(items.estante)
wbs_slug       = NORMALIZA(items.obra_wbs)   -- maiusculas, sem acento, _, max 20 chars
ano            = EXTRACT(YEAR FROM items.received_at)
hash8          = SUBSTRING(items.hash_sha256, 1, 8)
cota           = estante_code || '-' || wbs_slug || '-' || ano || '-' || hash8
```

A Cota é calculada uma única vez, no momento em que `estante` é definido (etapa de
roteamento — ver [diagrams/P1-estados-item.mmd](../diagrams/P1-estados-item.mmd)), e
gravada em `items.cota` (`UNIQUE`, ver [specs/S2-schema.sql](../specs/S2-schema.sql)).
Nunca é recalculada depois — mesmo que `obra_wbs` seja corrigido posteriormente por um
processo de catalogação manual, a Cota original permanece válida e endereçável.

## Sem vínculo de obra conhecido

Quando `obra_wbs` não é informado nem inferível no momento do roteamento, usa-se o
segmento fixo `GERAL` no lugar do `EMPREENDIMENTO_WBS`. O vínculo pode ser adicionado
depois via `relationships`, sem jamais reclassificar (renomear) a Cota já emitida —
mesmo princípio da LCC: o número de chamada não muda quando o catálogo aprende mais
sobre a obra.

## Colisão do segmento de hash

8 caracteres hexadecimais (32 bits) tornam colisão dentro do mesmo bucket
`ESTANTE-WBS-AAAA` estatisticamente rara, mas não impossível em grande escala. Em caso
de violação da constraint `UNIQUE (cota)`:

1. reprocessa a geração estendendo o segmento de hash para 12 caracteres;
2. se ainda colidir, estende para 16 caracteres;
3. o item nunca fica sem Cota — a extensão é a única forma de desambiguação, nunca a
   renumeração de itens já existentes.

## Expansibilidade sem reclassificação

Novas Estantes, novos empreendimentos ou novas convenções de WBS não exigem alterar
Cotas já emitidas — o formato é aberto por desenho (princípio LCC): itens antigos
mantêm sua Cota original mesmo quando o vocabulário de classificação cresce.
