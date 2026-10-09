# ESPECIFICAÇÃO DE ORQUESTRAÇÃO & GATEWAY: DAI ⇄ HDC
## MIDDLEWARE EM NUVEM OCI, PADRÃO FIRE-AND-ENQUEUE, GUARDRAILS DE IA E GOVERNANÇA DE CONCORRÊNCIA

**Organização:** SUGOI S.A. & Daisugi Tecnologias  
**Sistemas Integrados:** DAI (Smart Reception / Front-end) & HUDSON Data Center (HDC / Hub OCI)  
**Coordenação:** PMO de Processos, Riscos & Governança de TI  
**Liderança Técnica:** Arquiteto de Nuvem OCI & Especialista em Sistemas de Alta Concorrência  
**Ambiente:** Oracle Cloud Infrastructure (OCI) — `hudson.daisugi.com.br:9000`  
**Data de Emissão:** 09 de Outubro de 2026  
**Status do Documento:** 🟢 **HOMOLOGADO PARA PRODUÇÃO (CONTRATO DE INTERFACE V2.0)**  

---

## 🎯 1. VISÃO GERAL E PAPEL DO GATEWAY HDC

O **HUDSON DC (HDC)** opera na nuvem **Oracle Cloud (OCI)** como a primeira camada de recepção, escudo e inteligência entre a interface web da **DAI** e o cofre documental **HDW**.

Para que a experiência do usuário humano na DAI seja fluida (sem travamentos, "telas brancas" ou lentidões), o HDC implementa três pilares de engenharia:
1. **Desacoplamento Assíncrono (*Fire and Enqueue*):** Responde a qualquer requisição da DAI em **menos de 150 ms** com `HTTP 202 Accepted`, enviando a tarefa pesada para filas em background;
2. **Harness de Segurança e Guardrails Atômicos:** Valida previamente alçadas e permissões do operador antes de qualquer acesso a documentos, aplicando a **Regra das 3 Tentativas de Acesso Negado (Lockout no Redis)**;
3. **Cache L1 de Alta Performance:** Responde a consultas por cota, buscas por status e listagens de obras em **menos de 20 ms** direto da memória RAM do Redis 7 na nuvem.

---

## ⚙️ 2. TOPOLOGIA TÉCNICA E FLUXO DO MIDDLEWARE

```
                                FLUXO DE INTEGRAÇÃO DAI ⇄ HDC
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                           DAI FRONT-END (CLIENTE)                           │
   │  Envia: Payload JSON + Bearer JWT + Assinatura HMAC (X-Daisugi-Signature)  │
   └──────────────────────────────────────┬──────────────────────────────────────┘
                                          │ HTTPS / TLS 1.3 (Porta :9000)
                                          ▼
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                 HDC API GATEWAY (FASTAPI ASGI - NUVEM OCI)                  │
   │  1. Validação de Assinatura Anti-Tampering (HMAC SHA-256)                   │
   │  2. Extração de Identidade e Perfil do Usuário via JWT                       │
   │  3. Verificação do Guardrail de Alçada (Pre-Retrieval)                      │
   └──────────────────┬───────────────────────────────────┬──────────────────────┘
                      │                                   │
                      ▼                                   ▼
   ┌─────────────────────────────────────┐ ┌─────────────────────────────────────┐
   │  GUARDRAIL: ACESSO NEGADO DETECTADO │ │    GUARDRAIL: ACESSO AUTORIZADO     │
   │  • Incrementa Redis: failed_user    │ │  • Trava Idempotência (SETNX)       │
   │  • Se contador = 3: BLOQUEIA CONTA  │ │  • Checa Cache L1 no Redis (< 20ms) │
   │  • Registra violação forense        │ │  • Se Miss: Enfileira job no Celery │
   │  • Retorna HTTP 403 amigável        │ │  • Retorna HTTP 202 Accepted (<150ms│
   └─────────────────────────────────────┘ └─────────────────────────────────────┘
```

---

## 🛡️ 3. O HARNESS DE SEGURANÇA E GUARDRAILS DA IA

O Harness de Segurança é uma camada de código intermediária que intercepta **todas as intenções de busca ou comandos vindos da DAI ou da LLM** antes de qualquer chamada ao banco de dados ou ao servidor Linux:

### 3.1. Validação de Alçadas *Pre-Retrieval*
Antes de executar qualquer busca semântica ou pesquisa textual, o Guardrail cruza as credenciais do usuário com a matriz de alçadas:
* **Filtro Injetado Automaticamente:** O HDC adiciona silenciosamente cláusulas restritivas nas queries:
  ```python
  # Injeção forçada de contexto pelo Guardrail do HDC
  query_params["obra_wbs"] = user_session.obras_autorizadas  # ex: ['OBRA-FLORES-2026']
  query_params["nivel_sigilo"] = user_session.nivel_maximo    # ex: 'OPERACIONAL'
  ```
* Se um usuário com perfil *Engenheiro de Campo* tentar solicitar: *"Exibir contrato societário da Diretoria"*, o Guardrail detecta a quebra de alçada e aborta a execução sem consultar o HDW.

### 3.2. A Regra dos 3 Bloqueios (Account Lockout no Redis)
Para coibir tentativas maliciosas de enumeração de dados ou espionagem corporativa:
1. **Contador Atômico no Redis:** Cada tentativa não autorizada é registrada em uma chave com tempo de vida de 24 horas:
   ```python
   chave_tentativa = f"hdc:failed_access:{tenant_id}:{user_id}"
   falhas = redis_client.incr(chave_tentativa)
   redis_client.expire(chave_tentativa, 86400) # Janela de 24 horas
   ```
2. **Disparo do Bloqueio (3ª Falha):**
   * Ao atingir `falhas >= 3`:
     * O status do usuário é alterado para `SUSPENDED_SECURITY` no repositório de identidades;
     * Um evento imutável de violação é disparado e gravado no `custody_log` do HDW contendo: IP de origem, timestamp UTC, usuário e a query tentada;
     * Um alerta P1 com notificação imediata via Slack/E-mail é remetido ao PMO e ao time de Segurança da Informação;
     * A resposta à DAI passa a ser:
       > ⛔ *"Sua conta foi suspensa temporariamente devido a 3 tentativas consecutivas de acesso a acervos não autorizados. Entre em contato com a equipe de Segurança da Informação da SUGOI."*

---

## ⚡ 4. O PADRÃO FIRE-AND-ENQUEUE & CACHE L1

### 4.1. Idempotência Criptográfica no Redis 7
Para garantir que cliques duplos do operador ou falhas transitórias de conexão não dupliquem eventos de custódia:
* Todo envio recebe um `ticket_id` exclusivo gerado na DAI.
* O HDC executa uma trava atômica no Redis antes de qualquer processamento:
  ```python
  lock_adquirido = redis_client.set(
      f"hdc:idemp:{tenant_id}:{ticket_id}",
      "PROCESSANDO",
      nx=True,  # Só define se a chave NÃO existir
      ex=600    # Expira em 10 minutos
  )
  if not lock_adquirido:
      return JSONResponse(status_code=200, content={"status": "ja_em_processamento", "ticket_id": ticket_id})
  ```

### 4.2. Cache L1 de Metadados e Buscas
* O HDC mantém em sua memória Redis as informações de catálogo mais recentes:
  * Lista de WBS ativas da SUGOI;
  * Últimos 1.000 documentos custodiados por obra;
  * Mapeamento de Cota ➔ Hash SHA-256 ➔ Status.
* **Métrica de Performance:** **90% das consultas simples** são resolvidas diretamente no Redis do HDC em **< 20 ms**, eliminando qualquer carga sobre a CPU do servidor Linux CentOS 7.

---

## 📋 5. CONTRATOS DE API & SCHEMAS REST (DAI ⇄ HDC)

### 5.1. Rota de Despacho de Documento: `POST /api/v1/eventos/custodiar`
* **Cabeçalhos:**
  * `Authorization: Bearer <JWT_DO_USUARIO>`
  * `X-Daisugi-Tenant-ID: SUGOI-SA`
  * `X-Daisugi-Signature: <HMAC_SHA256>`

#### Exemplo de Payload de Requisição (DAI ➔ HDC):
```json
{
  "ticket_id": "TCK-SUGOI-20261009-0042",
  "obra_wbs": "OBRA-FLORES-2026",
  "estante": "document_text",
  "nome_arquivo_original": "FVS_Alvenaria_TorreA_Pav04.pdf",
  "usuario_captura": "ronaldo.akagui",
  "maquina_origem": "estacao-engenharia-01",
  "arquivo_base64": "JVBERi0xLjQKJcTl8uXr...",
  "metadados": {
    "etapa_obra": "Alvenaria",
    "responsavel_tecnico": "Eng. Roberto Silva",
    "fvs_numero": "FVS-104"
  }
}
```

#### Exemplo de Resposta Imediata (HDC ➔ DAI - Tempo < 150 ms):
```json
{
  "status": "enfileirado",
  "ticket_id": "TCK-SUGOI-20261009-0042",
  "mensagem": "Documento validado com sucesso e encaminhado para a esteira de custódia soberana.",
  "timestamp_recebimento": "2026-10-09T12:15:30.104Z"
}
```

---

### 5.2. Rota de Busca Inteligente / Consulta: `POST /api/v1/busca/consulta-semantica`
* **Finalidade:** Chamada executada pelo módulo de Chat da DAI ao interpretar uma pergunta do usuário.

#### Exemplo de Requisição (DAI ➔ HDC):
```json
{
  "query_texto": "laudo rompimento concreto laje torre B",
  "obra_wbs": "OBRA-FLORES-2026",
  "estante": "document_text",
  "limite": 5
}
```

#### Exemplo de Resposta (HDC ➔ DAI - Tempo < 20 ms via Cache L1):
```json
{
  "total": 1,
  "fonte": "cache_l1_redis",
  "resultados": [
    {
      "cota": "document_text-OBRA-FLORES-2026-2026-464468e2",
      "hash_sha256": "464468e27158f894987e82c35dcdda08fe0b3fb647cb9ab8d4ccceebc6067a59",
      "nome_arquivo_original": "Laudo_Concreto_Laje_TorreB_FCK30.pdf",
      "status": "indexado",
      "data_recebimento": "2026-10-08T22:01:13Z",
      "score_relevancia": 0.94,
      "resumo_ia": "Ensaio de rompimento aos 28 dias acusando resistência de 32,4 MPa. Conforme norma ABNT NBR 5739."
    }
  ]
}
```

---

## 🔒 6. PROTEÇÃO DE BORDA & RATE LIMITING

Para resguardar a integridade da nuvem corporativa OCI:
1. **WAF (Web Application Firewall):** Bloqueio nativo contra SQL Injection, Cross-Site Scripting (XSS) e tentativas de Path Traversal.
2. **Rate Limiting:**
   * Usuários comuns: Máximo de **60 requisições por minuto**;
   * Módulo de Chat: Máximo de **20 mensagens de IA por minuto**;
   * Ultrapassagem do limite: Retorna imediatamente `HTTP 429 Too Many Requests`.
