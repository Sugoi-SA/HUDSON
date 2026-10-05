# 🌐 HUDSON DC (HDC) — Hub Orquestrador Central Multi-Tenant

**Porta de Operação:** `9000` (FastAPI)  
**Domínio em Produção:** `https://hudson.daisugi.com.br`  
**Rede Interna Docker:** `daisugi-net` (Oracle Cloud Infrastructure — OCI)  
**Coordenação:** Dr. Tylor Code & Especialista em Sistemas de Alta Concorrência  

---

## 🎯 Visão Geral
O **HUDSON DC (HDC)** é o cérebro orquestrador da Daisugi Tecnologias. Ele atua como:
1. **Event Hub & Webhook Broker** para a **DAI (Smart Reception)**;
2. **Gateway Multi-Tenant** roteando eventos para os respectivos DWs Soberanos dos Clientes (como `sugoi_sa`);
3. **Ponte de Perícia Forense** com o **KAN-SA**;
4. **Acionador de Emergência P1** com o **Dr. SaulLM**;
5. **Grafo Central de Relacionamentos e Entidades** para recepção qualificada.

---

## 🛡️ Pilares de Segurança & Homeostase
* **Idempotência no Redis:** Trava atômica `SET idemp:{tenant}:{ticket_id} PROCESSING NX EX 600`. Duplicatas são descartadas sem custo computacional.
* **Validação Anti-Tampering:** Header `X-Daisugi-Signature` verificado com HMAC SHA-256.
* **Isolamento de Tenants:** Toda requisição isola o contexto via `X-Daisugi-Tenant-ID`.
* **Zero-Egress de Binários:** O HDC não armazena arquivos pesados; apenas hashes SHA-256 e metadados leves.

---

## 🚀 Como Subir o HDC

### Opção 1: Via Docker Compose (Produção OCI)
```bash
cd hdc_hub
docker compose -f docker-compose.hdc.yml up -d --build
```

### Opção 2: Localmente para Desenvolvimento
```bash
cd hdc_hub
python3 -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\Activate.ps1 no Windows
pip install -r requirements.txt

# Iniciar API na porta 9000
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```
