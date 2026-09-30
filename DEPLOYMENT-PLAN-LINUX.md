# 🚀 HUDSON v0 — Plano de Deployment no Linux

**Data**: 2026-09-30  
**Status Geral**: ✅ MVP v0 PRONTO PARA PRODUÇÃO (com lacunas conhecidas)  
**Próximas Fases**: Fase 1.1/1.2 (Frontend + RBAC + Canais Oficiais)

---

## 📋 FECHAMENTO DE STATUS v0

### ✅ Implementado e Validado

| Componente | Status | Teste | Última Validação |
|---|---|---|---|
| **Core Pipeline** | ✅ Completo | Pytest (22 testes) | 2026-09-24 |
| Backend (FastAPI) | ✅ Camadas | Unitário + Integração | 2026-09-24 |
| Hash SHA-256 | ✅ Streaming | Teste de integridade | 2026-09-24 |
| Deduplicação | ✅ Sem race condition | Teste de concorrência | 2026-09-24 |
| Roteamento por Estante | ✅ 6 estantes | Teste de routing | 2026-09-24 |
| Custody Log | ✅ Append-only | Trigger PG validado | 2026-09-24 |
| OCR (Tesseract) | ✅ Integrado | Teste de extração | 2026-09-24 |
| Full-text Index | ✅ tsvector PT-BR | Teste de busca | 2026-09-24 |
| Cota HUDSON | ✅ Determinística | Teste de geração | 2026-09-24 |
| API Key Auth | ✅ Implementada | Teste de 401/200 | 2026-09-24 |
| Integridade Pós-cópia | ✅ Com quarentena | Teste com arquivo corrompido | 2026-09-24 |
| Systemd Unit | ✅ Auto-restart | Kill -9 confirmado | 2026-09-24 |
| Backup (Postgres) | ✅ Ag. Cron | Struct. validada pg_restore --list | 2026-09-24 |
| Backup (Storage) | ✅ tar.gz | Struct. validada tar -tzf | 2026-09-24 |

### ⚠️ Lacuna Conhecida: Restore Completo

- **Situação**: Backup foi validado por integridade estrutural apenas
- **Falta**: Teste de `pg_restore` completo em banco de teste
- **Bloqueador**: Usuário `hudson` não tem privilégio `CREATEDB`
- **Solução**: Conceder `CREATEDB` ao usuário (ação root, uma única vez) OU rodar restore mensalmente com `postgres` user

---

## 🎯 PRÓXIMOS PASSOS (Ordem Executável)

### 1️⃣ **Validação Final de Dependências (Linux)**
**Onde**: Servidor CentOS 7 / Debian  
**Duração**: 5 min

```bash
# Verificar Python 3.8+ (exigido)
python3 --version

# Verificar PostgreSQL 15 (recomendado, 13+ OK)
psql --version

# Verificar Tesseract OCR (necessário)
tesseract --version

# Verificar Poppler (necessário para PDF)
pdfimages -v

# Verificar pip
pip3 --version
```

**Resultado esperado**: Python 3.8+, PostgreSQL 13+, Tesseract 4+, Poppler 0.84+

---

### 2️⃣ **Setup do Servidor Linux**

#### Passo A: Clonar repositório

```bash
cd /home
sudo git clone https://github.com/Sugoi-SA/HUDSON.git
sudo chown -R hudson:hudson /home/HUDSON
cd /home/HUDSON/backend
```

#### Passo B: Criar usuário `hudson` e diretórios (se não existir)

```bash
# Como root:
useradd -d /home/hudson -s /bin/bash -m hudson
mkdir -p /var/hudson/storage /home/hudson/backups/{postgres,storage}
chown -R hudson:hudson /var/hudson /home/hudson/backups

# Conceder SUDO (opcional) para futuras manutenções:
echo "hudson ALL=(ALL) NOPASSWD: /usr/bin/systemctl" >> /etc/sudoers.d/hudson
```

#### Passo C: Criar `.env` a partir do template

```bash
# Como hudson:
cp /home/HUDSON/backend/.env.example /home/HUDSON/backend/.env

# Editar com credenciais reais:
nano /home/HUDSON/backend/.env
```

**Valores esperados**:
```bash
DATABASE_URL=postgresql+psycopg://hudson:SEU_PASSWORD@localhost:5432/hudson
STORAGE_ROOT=/var/hudson/storage
API_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
TESSERACT_CMD=/usr/bin/tesseract  # Ou vazio se está em PATH
POPPLER_PATH=/usr/bin  # Ou vazio se está em PATH
```

#### Passo D: Setup do banco de dados

```bash
# Como postgres ou root:
createuser hudson
createdb -O hudson hudson

# (Opcional) Conceder CREATEDB ao hudson para restore futuro:
ALTER USER hudson CREATEDB;
```

#### Passo E: Criar venv e instalar dependências

```bash
# Como hudson:
cd /home/HUDSON/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Duração**: ~2-3 min (depende de internet)

#### Passo F: Inicializar banco com schema

```bash
# Como hudson:
cd /home/HUDSON/backend
source .venv/bin/activate

# Executar os DDLs de S2:
psql -d hudson -f ../specs/S2-schema.sql
```

**Validação**: Verificar tabelas criadas:
```bash
psql -d hudson -c "\dt"
# Esperado: items, custody_log, entities, relationships, declarations, estant_types
```

---

### 3️⃣ **Testar API Localmente (antes de Systemd)**

```bash
# Como hudson, no /home/HUDSON/backend:
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Em outro terminal:
curl -X GET http://localhost:8000/health
# Esperado: {"status": "ok", "timestamp": "2026-09-30T..."}
```

---

### 4️⃣ **Instalar Unidade Systemd**

```bash
# Como root:
cp /home/HUDSON/backend/deploy/hudson-api.service /etc/systemd/system/

# Editar se necessário (caminhos):
nano /etc/systemd/system/hudson-api.service

# Registrar e habilitar:
systemctl daemon-reload
systemctl enable hudson-api.service
systemctl start hudson-api.service

# Verificar status:
systemctl status hudson-api.service
# Esperado: "active (running)"

# Logs em tempo real:
journalctl -u hudson-api.service -f
```

---

### 5️⃣ **Agendar Backup Diário (Cron)**

```bash
# Como hudson:
crontab -e

# Adicionar linha (03h diário):
0 3 * * * /home/HUDSON/backend/deploy/backup.sh >> /tmp/hudson_backup.log 2>&1
```

**Validação**: Testar manualmente:
```bash
/home/HUDSON/backend/deploy/backup.sh

# Verificar saída:
ls -lah /home/hudson/backups/postgres/
ls -lah /home/hudson/backups/storage/
```

---

## ✅ CHECKLIST DE VALIDAÇÃO PÓS-DEPLOYMENT

### 1. API Respondendo

```bash
curl -X GET http://localhost:8000/health
# Esperado: {"status": "ok", "timestamp": "..."}
```

### 2. Autenticação

```bash
# Sem API key (deve falhar):
curl -X GET http://localhost:8000/search?query=test
# Esperado: 401 Unauthorized

# Com API key (deve passar):
curl -X GET http://localhost:8000/search?query=test \
  -H "Authorization: Bearer <API_KEY_DO_.ENV>"
# Esperado: {"results": [], "total": 0} ou 200 OK
```

### 3. Pipeline de Ingestão

```bash
# Como hudson:
cd /home/HUDSON/backend
source .venv/bin/activate

# Rodar CLI para testar:
python scripts/import_cli.py \
  --file /caminho/para/arquivo.pdf \
  --estante JURIDICO
```

**Esperado**:
- Arquivo copiado em `/var/hudson/storage/`
- Hash SHA-256 calculado
- Entrada em `custody_log`
- Cota HUDSON gerada
- Indexação full-text completada

### 4. Banco de Dados

```bash
# Verificar integridade:
psql -d hudson -c "SELECT COUNT(*) FROM items;"
psql -d hudson -c "SELECT COUNT(*) FROM custody_log;"
```

### 5. Backup Agendado

```bash
# Verificar se cron rodou:
ls -lah /home/hudson/backups/postgres/hudson_*.dump
ls -lah /home/hudson/backups/storage/hudson_storage_*.tar.gz

# Validar estrutura do dump:
pg_restore --list /home/hudson/backups/postgres/hudson_*.dump | head -20
```

### 6. Systemd Auto-restart

```bash
# Como root:
ps aux | grep uvicorn  # Anotar PID

# Matar o processo:
kill -9 <PID>

# Aguardar ~5s, verificar se reiniciou:
systemctl status hudson-api.service
# Esperado: "active (running)" com novo PID

curl -X GET http://localhost:8000/health
# Esperado: 200 OK (sem delay)
```

---

## 🔴 Decisão Pendente: SO e Python EOL

**Situação Atual**:
- CentOS 7: Fim de suporte em 2024 (EOL)
- Python 3.8: Fim de suporte em 2024 (EOL)

**Recomendações** (em ordem de risco):

### ✅ Opção 1: Migrar para CentOS Stream 9 + Python 3.11
- **Risco**: Baixo (distro compatível, versionamento suportado)
- **Benefício**: Suporte até 2032
- **Esforço**: ~2h (re-build ambiente)

### ⚠️ Opção 2: Ficar em CentOS 7 + Python 3.8 (Status Quo)
- **Risco**: Alto (sem segurança patches)
- **Benefício**: Sem esforço agora
- **Custo**: Risco crescente conforme o tempo passa

### 🟡 Opção 3: Containerizar com Docker
- **Risco**: Médio (introduce novo layer operacional)
- **Benefício**: Isolamento, portabilidade, upgrade fácil
- **Esforço**: ~4h (criar Dockerfile + docker-compose)

**Recomendação**: Opção 1 (Migração simples) ou Opção 3 (Containerização para futuro)

---

## 📊 Arquitetura de Deployment Atual

```
┌─────────────────────────────────────┐
│ Cliente HTTP                        │
├─────────────────────────────────────┤
│ Nginx ou Firewall (porta 127.0.0.1:8000 local)
├─────────────────────────────────────┤
│ Systemd Unit: hudson-api.service    │
├─────────────────────────────────────┤
│ Uvicorn (uvicorn app.main:app)      │
│ ├─ API Layer (routers/)              │
│ ├─ Business Logic (services/)        │
│ ├─ Database Access (repositories/)   │
│ └─ Security (API key auth)          │
├─────────────────────────────────────┤
│ PostgreSQL 15 (hudson db)            │
│ ├─ items (com triggers append-only)  │
│ ├─ custody_log                      │
│ ├─ entities                          │
│ └─ relationships                    │
├─────────────────────────────────────┤
│ Storage: /var/hudson/storage/        │
│ └─ Estrutura por estante + hash     │
├─────────────────────────────────────┤
│ Backup (Cron 03h)                   │
│ ├─ pg_dump → /home/hudson/backups/postgres
│ └─ tar -czf → /home/hudson/backups/storage
└─────────────────────────────────────┘
```

---

## 📞 Próximos Passos Imediatos

1. ✅ **Validar** este plano com arquitetura/DevOps do servidor alvo
2. ✅ **Confirmar** credenciais PostgreSQL + armazenamento (`STORAGE_ROOT`)
3. ✅ **Executar** seção "Setup do Servidor Linux" passo a passo
4. ✅ **Rodar** "Checklist de Validação" completo
5. ✅ **Documentar** qualquer desvio ou erro encontrado
6. ⏳ **Aguardar** decisão sobre SO/Python (Opção 1, 2 ou 3)

---

## 📚 Referências

- `docs/V0-STATUS.md` — Status técnico detalhado
- `specs/S2-schema.sql` — DDL do banco
- `specs/S1-openapi.yaml` — Contrato da API
- `backend/deploy/hudson-api.service` — Unidade systemd
- `backend/deploy/backup.sh` — Script de backup
- `backend/.env.example` — Variáveis de ambiente
- `backend/requirements.txt` — Dependências Python

---

**Documento preparado em**: 2026-09-30  
**Responsável**: Claude AI + MV-AKAGUI  
**Próxima revisão**: Após deployment bem-sucedido
