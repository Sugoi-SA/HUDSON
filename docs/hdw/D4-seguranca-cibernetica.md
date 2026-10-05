# D4 — Segurança Cibernética

**Status:** recomendação — aguardando aprovação humana.

## Recomendação

| Controle | Recomendação |
|---|---|
| Isolamento de rede | Rede `seg_quarentena` sem rota direta para a rede `core` — já modelado em [diagrams/P2-deployment-fisico.mmd](../diagrams/P2-deployment-fisico.mmd); a API é a única ponte autorizada entre as duas |
| Egress de internet | Zero egress para todos os contêineres do núcleo e da quarentena — a única exceção seria uma chamada ao LLM Provider externo, que D1 recomenda eliminar ao rodar o modelo localmente |
| Gestão de segredos | `.env` nunca versionado (`.gitignore` na raiz e em `backend/`); credenciais de produção via Docker secrets, não variáveis de ambiente em texto claro no `docker-compose.yml` |
| Rate limiting | Por emissor, nos 6 contratos de webhook — throttle configurável para conter abuso ou falha em cascata de um emissor específico |
| Hardening do Ubuntu | `sshd` restrito a autenticação por chave pública (sem senha); `ufw` liberando somente as portas publicadas (8000 API, 9000 MinIO); `fail2ban` para tentativas de força bruta em SSH e HTTP |

## Tradeoffs

| Critério | Postura restritiva (recomendada) | Postura permissiva |
|---|---|---|
| Superfície de ataque | Mínima — egress zero, rede segmentada | Maior — qualquer chamada externa é um vetor potencial |
| Complexidade operacional | Maior — exige configurar rede, secrets e firewall corretamente desde o início | Menor no curto prazo, mas acumula dívida de segurança |
| Adequação a um acervo forense/pericial | Alta — dado sensível nunca trafega sem necessidade | Baixa — inaceitável para custódia com valor probatório |
| Velocidade de desenvolvimento inicial | Ligeiramente mais lenta (setup de segredos e rede) | Mais rápida no MVP, mas exige retrabalho depois |

## Observação sobre a rede de quarentena

O isolamento de rede da quarentena (já tratado como fato de infraestrutura no
contexto único, não como decisão pendente) é reforçado aqui como parte de uma postura
de segurança mais ampla — este documento propõe as camadas adicionais (secrets, rate
limit, hardening de SO) que tornam essa segmentação efetiva na prática.
