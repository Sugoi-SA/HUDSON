# 🌐 HUDSON DC (HDC) — Arquitetura, Governança & Hub Orquestrador
**Módulo:** HUDSON Data Center (HUDSON PAI)  
**Porta de Operação:** `9000` (FastAPI)  
**Ambiente:** Oracle Cloud Infrastructure (OCI) — `hudson.daisugi.com.br`  
**Coordenação:** Dr. Tylor Code & Especialista em Sistemas de Alta Concorrência  

---

## 1. Identidade e Papel no Ecossistema
O **HUDSON DC (HDC)** é o núcleo orquestrador multi-tenant e broker de eventos da **Daisugi Tecnologias**. Ele opera em simbiose com:
* **DAI (Smart Reception Framework):** Interface empática de portaria e acolhimento (FastAPI :8001 / Streamlit :8501).
* **KAN-SA:** Motor de auditoria pericial e laudos técnicos de obras e finanças.
* **Kigyou:** Governança corporativa e travas de segurança de ERP.
* **Cofre PAM-IGA:** Governança de acessos privilegiados com dupla alçada (*Maker-Checker*).
* **HDWs Filhotes:** Rede federada de Data Warehouses soberanos dos clientes (ex: SUGOI S.A.).

---

## 2. Topologia de Concorrência & Homeostase
Para garantir tempo de resposta inferior a 200ms na portaria da DAI, o HDC implementa o padrão **Fire and Enqueue**:
1. **Idempotência no Redis:** Trava atômica `SET hdc:idemp:{tenant}:{ticket_id} PROCESSING NX EX 600` impedindo duplo processamento.
2. **Anti-Tampering HMAC SHA-256:** Verificação de integridade via header `X-Daisugi-Signature`.
3. **Isolamento de Tenants:** Header `X-Daisugi-Tenant-ID` segregando o tráfego e as consultas no Grafo Central.
4. **Despacho Assíncrono:** O endpoint devolve `HTTP 202 Accepted` imediatamente e joga a carga pesada para o Celery com Redis.

---

## 3. Matriz de Endpoints do HDC
* `POST /api/v1/eventos/notificar-anfitriao`: Notificação instantânea via Slack/Push ao anfitrião do departamento.
* `POST /api/v1/webhooks/quarentena-auditoria`: Encaminhamento de CCBs e medições PAM para a esteira KAN-SA.
* `POST /api/v1/alertas/emergencia`: Sirene P1 imediata + orientação jurídica preliminar do Dr. SaulLM.
* `GET /api/v1/grafo/consultar-entidade`: Busca semântica de perfis, cargos e riscos para recepção qualificada.
* `POST /api/webhooks/hudson-callback` (HDC ➔ DAI): Retorno automático da resposta do anfitrião ou conclusão pericial.
