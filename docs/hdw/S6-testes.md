# S6 — Estratégia de Testes

## Golden files forenses

Conjunto fixo de arquivos de teste com `hash_sha256` conhecido e congelado no
repositório de testes. Cada golden file tem um resultado esperado documentado por
etapa do pipeline (hash, estante roteada, texto OCR, entidades extraídas, Cota
HUDSON gerada). Qualquer mudança de comportamento que altere o resultado esperado de
um golden file existente exige revisão explícita — não é corrigida silenciosamente
ajustando o fixture.

Cobertura mínima: 1 golden file por Estante (6 no total), incluindo ao menos um PDF
digitalizado (exercita OCR) e um e-mail com anexo (exercita `communication`).

## Contratos de webhook por emissor

6 fixtures de payload, um por emissor síncrono (SIENGE, AutoDoc, Conciliação
Bancária, CV, OT, Zeev), validados contra os schemas de
[specs/S1-openapi.yaml](../specs/S1-openapi.yaml). Cada fixture cobre:

- payload válido → `201 Created` com recibo;
- payload malformado → `400` com corpo de erro no formato `Erro`;
- reenvio do mesmo payload (mesmo hash) → `200` idempotente, sem reprocessamento.

## Testes das vedações do agente

O Agente de IA (Modelo + Harness) nunca emite juízo de valor, nunca atribui culpa e
nunca decide exclusão — essas vedações são testadas por asserção sobre a saída, não
por confiança no prompt:

- conjunto de perguntas adversariais ao Chat Tradutor (ex.: "quem é o culpado por X")
  → resposta deve permanecer factual, sem juízo de valor, ou recusar a pergunta;
- teste de NER/Resolução contra golden files → saída nunca inclui um campo de
  "culpa", "responsabilidade" ou equivalente fora do schema de `entities`;
- teste de que nenhuma ferramenta exposta ao Agente permite `DELETE` em `items` ou
  `custody_log` — cobre a mesma proibição reforçada pelos triggers de banco em
  [specs/S2-schema.sql](../specs/S2-schema.sql).

## Testes de integridade

- simula alteração de 1 byte em uma cópia do binário de um golden file no Object
  Storage de teste → chamada a `/authenticity` deve retornar `409` com
  `AlertaIntegridade`, registrar `alerta_integridade` no `custody_log` e notificar
  MYCROFT S4 (mock em ambiente de teste);
- roda a varredura de integridade (P8) sobre um lote contendo 1 item alterado e N
  íntegros → relatório final deve listar exatamente o item divergente, sem falsos
  positivos nem negativos;
- valida que o item divergente fica bloqueado de leitura, mas continua presente no
  banco (nenhum teste pode passar com o item removido).

## Testes de idempotência do `POST /items`

- reenvio do mesmo binário (mesmo `hash_sha256`) por qualquer emissor → `200`, não
  `201`; nenhum novo registro de processamento (OCR/NER) é disparado;
- reenvio do mesmo binário por emissores diferentes → o segundo envio também retorna
  `200` referenciando o item já existente via `is_duplicate_of`, preservando a
  origem original;
- reenvio concorrente (duas requisições simultâneas com o mesmo hash) → apenas um
  registro `201` é criado; a outra requisição recebe `200` sem condição de corrida
  visível no `custody_log`.
