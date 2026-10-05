# D1 — Onde roda a LLM (local vs. API externa)

**Status:** recomendação — aguardando aprovação humana (P6/P7 do contexto único: nada
roda em produção sem aprovação, e a versão aprovada trava no `prompt_registry`).

## Recomendação

**Modelo local** (open-source, hospedado no próprio Ubuntu Server) para as 3 funções
da LLM — NER, Resolução de Entidades e Chat Tradutor. Dado pericial nunca deixa o
servidor da SUGOI, o que é o requisito mais forte para um sistema de custódia forense
(Arts. 158-A a 158-F do CPP) e reduz a superfície de exposição a LGPD. API externa só
seria reconsiderada se, após o MVP, a qualidade do Chat Tradutor local se mostrar
insuficiente — decisão a revalidar com métricas reais, nunca antecipada aqui.

## Tradeoffs

| Critério | Modelo local | API externa |
|---|---|---|
| Compliance / sigilo forense | Dado nunca sai do servidor — melhor cenário possível | Dado pericial trafega para terceiro — risco alto para um custodiante forense |
| Custo | Previsível (infraestrutura, sem custo por token) | Custo por token pode escalar de forma imprevisível com a Pesca de Rede (ingestão exaustiva, sem descarte prévio) |
| Latência | Depende de CPU/GPU disponível no host — pode exigir modelo menor ou quantizado | Geralmente menor e mais estável, mas sujeita à rede e ao terceiro |
| Precisão em NER jurídico PT-BR | Exige ajuste (prompt engineering, eventual fine-tuning) para igualar SOTA proprietário | Modelos proprietários tendem a ter melhor desempenho pronto, sem ajuste |
| Disponibilidade | Sob controle total da SUGOI | Depende de uptime e política do fornecedor |
| Manutenção | Equipe da SUGOI assume patches e atualizações do modelo | Fornecedor assume a manutenção do modelo |

## Consequência para D4

Escolher modelo local elimina a única chamada de rede externa que o núcleo
precisaria fazer em operação normal — reforça a recomendação de egress zero em D4.
