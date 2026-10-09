# MANUAL MESTRE DE INFRAESTRUTURA, TOPOLOGIA OPENVPN & MATRIZ DE APIS
## ARQUITETURA DE REDES, SEGURANÇA DE PERÍMETRO, PROTOCOLOS CRIPTOGRÁFICOS E CONTRATOS REST

**Organização:** SUGOI S.A. & Daisugi Tecnologias  
**Sistemas:** Ecossistema Integrado DAI ⇄ HDC (OCI) ⇄ HDW (Linux Local)  
**Coordenação:** PMO de Processos, Riscos & Governança de TI  
**Liderança Técnica:** Engenheiro de Redes & Cibersegurança, Arquiteto OCI e Dr. Taylor  
**Data de Emissão:** 09 de Outubro de 2026  
**Status do Documento:** 🟢 **HOMOLOGADO PARA OPERAÇÃO E INFRAESTRUTURA (V2.0)**  

---

## 🏛️ 1. TOPOLOGIA FÍSICA E LÓGICA DE INFRAESTRUTURA

O ecossistema opera em duas zonas físicas e geográficas rigorosamente segregadas: a **Nuvem Privada Oracle Cloud (OCI)** e o **Servidor Físico On-Premises (CentOS 7)** na sede da SUGOI S.A.:

```
                               TOPOLOGIA GERAL INTEGRADA
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                    ZONA A: NUVEM ORACLE CLOUD (OCI PRIVADA)                 │
 │                                                                             │
 │  ┌─────────────────────────┐  ┌─────────────────────────┐                   │
 │  │      DAI FRONT-END      │  │     LLM OPEN SOURCE     │                   │
 │  │  • SPA React 18 / MUI   │  │  • vLLM / Ollama :8080  │                   │
 │  │  • Portal Web Usuários  │  │  • Llama 3.1 / Qwen 2.5 │                   │
 │  └────────────┬────────────┘  └────────────┬────────────┘                   │
 │               │                            │                                │
 │               └─────────────┬──────────────┘                                │
 │                             ▼                                               │
 │  ┌──────────────────────────────────────────────────────┐                   │
 │  │               HUDSON DATA CENTER (HDC CORE)          │                   │
 │  │  • API Gateway FastAPI (:9000)                       │                   │
 │  │  • Redis 7 (Idempotência, Cache L1, Lockout)         │                   │
 │  │  • Celery Distributed Workers                        │                   │
 │  └──────────────────────────┬───────────────────────────┘                   │
 └─────────────────────────────┼───────────────────────────────────────────────┘
                               │
                               │ Túnel Criptografado OpenVPN (UDP Porta 1194)
                               │ AES-256-CBC / SHA-256 / mTLS
                               ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                ZONA B: DATACENTER LOCAL SUGOI (ON-PREMISES)                 │
 │                 Servidor Físico Linux CentOS 7 (192.168.1.122)              │
 │                                                                             │
 │  ┌──────────────────────────────────────────────────────┐                   │
 │  │           HUDSON DATA WAREHOUSE (HDW SOBERANO)       │                   │
 │  │  • Container hudson-app (FastAPI :8000)              │                   │
 │  │  • Container sugoi-postgres (PostgreSQL 18.6 :5432)  │                   │
 │  │  • Storage Local: /home/hudson/hudson_storage        │                   │
 │  │  • Blindagem Forense: Triggers Imutáveis Append-Only │                   │
 │  └──────────────────────────────────────────────────────┘                   │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔒 2. ESPECIFICAÇÃO DO TÚNEL SEGURO OPENVPN

O acesso ao servidor Linux da SUGOI é totalmente bunkerizado contra ataques externos. Nenhuma porta está aberta diretamente para a internet.

### 2.1. Parâmetros Criptográficos da Conexão
* **IP do Gateway / Servidor VPN:** `87.102.137.206`
* **Porta & Protocolo:** `1194 / UDP` (Menor latência para streaming de binários)
* **Cifra de Criptografia Simétrica:** `AES-256-CBC`
* **Função Hash de Integridade:** `SHA-256`
* **Autenticação Mútua (mTLS):** Certificado digital do cliente (`hudson_vpn.crt`) assinado pela Autoridade Certificadora privada da SUGOI (`ca.crt`).
* **Sub-rede Privada Virtualizada:** `10.8.0.0/24` roteada para a interface física interna `192.168.1.0/24`.

### 2.2. Política de Conexão Estrita
1. **O HDC é o único originador de túnel:** O daemon OpenVPN roda no container do Celery Worker na nuvem OCI e conecta-se ao servidor local.
2. **Estações de trabalho humanas NÃO possuem VPN para o HDW:** Nenhum computador de colaborador ou celular tem chave direta para o banco local. Todos os acessos passam obrigatoriamente pela governança do HDC na nuvem.

---

## 📋 3. MATRIZ INTEGRADA DE APIS & CONTRATOS REST

A matriz a seguir consolida todas as rotas e contratos de comunicação do ecossistema:

| Serviço | Método & Rota | Entrada (Request) | Saída (Response) | Função no Ecossistema |
| :--- | :--- | :--- | :--- | :--- |
| **LLM (OCI)** | `POST /v1/chat/completions` | `{"model": "llama-3.1", "messages": [...]}` | `{"choices": [{"message": {"content": "..."}}]}` | Raciocínio de linguagem natural livre e geração de respostas para a DAI em tempo real. |
| **HDC (OCI)** | `POST /api/v1/eventos/custodiar` | `{"ticket_id": "...", "obra_wbs": "...", "arquivo_base64": "..."}` | `202 Accepted`<br>`{"status": "enfileirado"}` | Padrão Fire-and-Enqueue: recebe arquivos da DAI, valida alçadas e despacha em background. |
| **HDC (OCI)** | `POST /api/v1/busca/consulta-semantica` | `{"query_texto": "...", "obra_wbs": "..."}` | `200 OK`<br>`{"resultados": [{"cota": "...", "hash": "..."}]}` | Busca ultrarrápida via Cache L1 em Redis na nuvem OCI (< 20 ms). |
| **HDC (OCI)** | `POST /api/webhooks/hudson-callback` | `{"ticket_id": "...", "cota": "...", "status": "custodiado"}` | `200 OK` | Callback assíncrono avisando a DAI que o documento foi homologado no cofre. |
| **HDW (Local)**| `GET /health` | Nenhuma | `200 OK`<br>`{"status": "ok"}` | Healthcheck de infraestrutura e pool do banco de dados no Linux. |
| **HDW (Local)**| `GET /items/{cota}` | `cota` na URL + `X-API-Key` | `200 OK`<br>`{"cota": "...", "storage_path": "...", "status": "indexado"}` | Localização de metadados e caminho do binário por cota determinística. |
| **HDW (Local)**| `GET /search` | `?q=texto&limit=50` + `X-API-Key` | `200 OK`<br>`{"total": 1, "results": [...]}` | Busca textual profunda via índice `tsvector` nativo do PostgreSQL em português. |
| **HDW (Local)**| `POST /items/custodia` | Stream Binário + `X-API-Key` + Metadados v2.0 | `201 Created`<br>`{"cota": "...", "hash_sha256": "..."}` | Ingestão soberana: cálculo SHA-256, deduplicação, gravação física e inserção em `custody_log`. |
| **HDW (Local)**| `GET /items/{cota}/authenticity` | `cota` na URL + `X-API-Key` | `200 OK`<br>`{"status_integridade": "100%_INTEGRO"}` | Perícia forense: recálculo do hash no disco físico e confronto com a cadeia de custódia. |

---

## ⚡ 4. POLÍTICAS DE RESILIÊNCIA & CIRCUIT BREAKER

Para assegurar operação contínua mesmo em caso de corte no link de fibra da sede ou manutenções:

```
                            MÁQUINA DE ESTADOS DO CIRCUIT BREAKER
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                          ESTADO NORMAL: CLOSED (FECHADO)                    │
   │  • HDC despacha pacotes diretamente via OpenVPN para o HDW local            │
   │  • Latência média: < 180 ms | Taxa de sucesso: > 99.8%                      │
   └──────────────────────────────────────┬──────────────────────────────────────┘
                                          │ Falhas consecutivas > 3 ou Timeout > 5s
                                          ▼
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                          ESTADO DE FALHA: OPEN (ABERTO)                     │
   │  • O circuito abre imediatamente para não travar a nuvem OCI                │
   │  • O HDC retém todas as custódias no Redis/Celery (Buffer de até 72 horas)   │
   │  • A DAI continua operando normalmente e emitindo protocolos provisórios    │
   └──────────────────────────────────────┬──────────────────────────────────────┘
                                          │ Temporizador de resfriamento (5 min)
                                          ▼
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                       ESTADO DE TESTE: HALF-OPEN (MEIO-ABERTO)              │
   │  • O HDC envia requisição sonda 'GET /health' pelo túnel VPN                │
   │  • Se HTTP 200: Retorna ao estado CLOSED e drena a fila represada           │
   │  • Se Falhar: Retorna ao estado OPEN por mais 5 minutos                     │
   └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 💾 5. PLANO DE DISASTER RECOVERY & CONTINUIDADE DE NEGÓCIOS

* **RPO (Recovery Point Objective):** **Zero (0)**. Cada documento processado no HDW recebe um `commit` relacional individual em `hudson.items` e `hudson.custody_log_YYYY`.
* **RTO (Recovery Time Objective):** **< 1 hora**.
* **Rotina Automatizada de Backup no Servidor Linux:**
  ```bash
  # Backup diário em formato binário comprimido com catálogo forense
  docker exec sugoi-postgres pg_dump -U postgres -Fc -d sugoi > /home/hudson/backups/docker/sugoi_$(date +%Y%m%d_%H%M%S).dump
  # Validação de integridade do arquivo sem necessidade de restauração
  docker exec -i sugoi-postgres pg_restore --list < /home/hudson/backups/docker/ULTIMO_BACKUP.dump | head -20
  ```
* **Espelhamento Criptografado Off-Site:** O diretório de dumps e o acervo `/home/hudson/hudson_storage` são sincronizados semanalmente em bucket privado imutável na OCI com retenção estrita (*Object Lock*).
