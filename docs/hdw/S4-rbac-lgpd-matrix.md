# S4 — Matriz RBAC e Tarjamento LGPD

## Matriz RBAC — perfis × operações

`delete` é proibido para todos os perfis, sem exceção — reforça P3 (Zero Exclusão) e o
bloqueio por trigger de banco em [specs/S2-schema.sql](../specs/S2-schema.sql).
`ingest` só existe pelos 4 canais descritos no contexto único (webhooks, M365, varredura
legada, canal humano do Zeev) — nenhum perfil administra um upload paralelo fora do fluxo.

| Perfil | ingest | read | release | approve_prompt | export | delete |
|---|---|---|---|---|---|---|
| Analista de Quarentena | não (só via canal humano do Zeev) | sim — fila de itens retidos | **sim** — libera itens retidos | não | não | **PROIBIDO** |
| Consumidor Corporativo | não | **sim** — `/search`, `/authenticity`, `/custody-log`, `/timeline`, `/communication-map` | não | não | sim — com tarjamento LGPD | **PROIBIDO** |
| WATSON S2 (auditoria) | não | sim — leitura auditada do acervo | não | não | sim — relatórios de auditoria | **PROIBIDO** |
| HOLMES S3 (sindicância) | não | sim — somente leitura, nunca ingestão (P4 do contexto único) | não | não | sim — com tarjamento LGPD | **PROIBIDO** |
| MYCROFT S4 (governança) | não | sim — telemetria e `prompt_registry` | não | **sim** — único perfil que aprova versão do System Prompt | sim | **PROIBIDO** |
| Admin (infraestrutura) | não — usa os mesmos 4 canais oficiais | sim | sim — pode agir como escalonamento | não — separação de poderes; aprovação de prompt é exclusiva de MYCROFT S4 | sim | **PROIBIDO** |

Toda negação de acesso (`403`) gera registro no `custody_log` como tentativa — ver
diagrama [P5](../diagrams/P5-consumo-biblioteca-soberana.mmd).

## Tarjamento LGPD em exportações

Aplica-se apenas a **exportações** (`export`). Consulta interna por perfil autorizado
não é mascarada — a integridade probatória exige o dado original disponível para os
perfis com base legal de auditoria/sindicância/governança (Art. 158-A a 158-F do CPP).

| Campo / tipo de dado | Regra de tarjamento na exportação |
|---|---|
| Nome completo de PF | Iniciais mantidas, restante mascarado — ex.: `J*** S***` |
| CPF | Mantém os 3 últimos dígitos, restante mascarado |
| CNPJ | Máscara parcial — mantém a raiz (8 primeiros dígitos), mascara filial e DV |
| Telefone | Mantém DDD, mascara os demais dígitos |
| E-mail | Mantém domínio, mascara a parte local — ex.: `j***@empresa.com.br` |
| Endereço | Generalizado para cidade/UF — logradouro e número são mascarados |
| Dados bancários (conta, agência, chave PIX) | Nunca exportados em texto claro — sempre mascarados, mesmo para perfis com `export` |
| Valores contratuais e datas | Não são dados pessoais — não sofrem tarjamento LGPD |
| Hash SHA-256 e Cota HUDSON | Não são dados pessoais — não sofrem tarjamento LGPD |

O tarjamento é aplicado pela API no momento da exportação, nunca alterando o dado
armazenado — o registro original permanece íntegro em `items`/`entities` para fins de
custódia e nova exportação sob perfil diferente.
