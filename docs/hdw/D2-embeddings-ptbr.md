# D2 — Embeddings pt-BR e Estratégia de Chunking

**Status:** recomendação — aguardando aprovação humana.

## Recomendação

Modelo de embeddings **open-source multilíngue, hospedado localmente** (coerente com
D1): **BGE-M3** como padrão — suporta recuperação híbrida nativa (denso + esparso +
multi-vetor), o que complementa bem o `tsvector` do PostgreSQL já usado para busca
lexical. **multilingual-e5-large** como alternativa mais leve, caso a latência de
BGE-M3 em CPU se mostre incompatível com o NFR de busca (p95 < 2s, ver S5).

## Estratégia de chunking (por Estante, não por tamanho fixo)

| Estante | Unidade de chunk | Justificativa |
|---|---|---|
| document_text | por cláusula contratual identificada | corte por tamanho fixo (ex. 512 tokens) pode partir uma cláusula ao meio e perder o contexto jurídico que dá sentido a ela |
| communication | por e-mail/mensagem completa | preserva o contexto integral da thread; cortar no meio de uma mensagem perde o interlocutor e a intenção |
| engineering_drawings | por página/prancha | a legenda e as anotações de uma prancha só fazem sentido junto da prancha inteira |
| structured_data | por documento (NF, OC, medição) | dado estruturado não se beneficia de chunking semântico — o documento inteiro é a unidade |
| image | por imagem | unidade já é atômica |
| audio_video | por segmento de fala (turno de conversa na transcrição) | preserva quem disse o quê, mantendo a atribuição ao interlocutor |

## Tradeoffs

| Critério | BGE-M3 | multilingual-e5-large |
|---|---|---|
| Qualidade em PT-BR | Alta, com suporte a recuperação híbrida | Alta, densa apenas |
| Complementaridade com tsvector | Forte — componente esparso já é próximo de busca lexical | Fraca — só denso, redundante com tsvector em parte dos casos |
| Custo computacional (CPU) | Maior — múltiplos vetores por chunk | Menor — um vetor denso por chunk |
| Simplicidade operacional | Menor — mais parâmetros a ajustar | Maior — modelo mais simples de operar |

## Retenção de proximidade semântica

Chunking por unidade natural do documento (cláusula, mensagem, página) preserva a
coesão semântica que o RAG depende para responder corretamente no Chat Tradutor — um
chunk que corta uma cláusula ao meio produz um embedding que não representa nem o
início nem o fim da ideia, degradando a precisão da busca semântica sem ganho de
desempenho perceptível.
