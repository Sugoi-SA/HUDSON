# 🚀 HUDSON v0 — Deployment em vmsever.sugoisa.com.br

**Data**: 2026-09-30  
**Servidor**: vmsever.sugoisa.com.br  
**SO**: CentOS 7 (Core)  
**Status**: ✅ **PRONTO PARA DEPLOYMENT**

---

## 📊 Especificações do Servidor (Realidade)

| Aspecto | Valor | Status |
|---|---|---|
| **Hostname** | vmsever.sugoisa.com.br | ✅ Resolvível |
| **SO** | CentOS 7 (Kernel 3.10.0-1127) | ⚠️ EOL mas OK |
| **CPU** | Intel Xeon E5-2630 v3 x2 (32 vCPUs) | ✅ Excelente |
| **RAM** | 31GB (25GB livre) | ✅ Abundante |
| **Storage (/) ** | 10GB (LVM vg4-var01) | ⚠️ Ver abaixo |
| **Storage (/home/hudson)** | 10GB (LVM vg6-lv_hudson) | ⚠️ Ver abaixo |
| **Storage (/financeiro)** | 50GB disponível | ✅ Usar este |
| **Python** | 3.11 instalado! | ✅ Excelente |
| **PostgreSQL** | ❓ Precisa verificar | 🔍 Próximo passo |
| **Tesseract** | ❓ Precisa verificar | 🔍 Próximo passo |
| **Poppler** | ❓ Precisa verificar | 🔍 Próximo passo |
| **Docker** | Não instalado | ℹ️ OK (não precisa) |

---

## ⚠️ ATENÇÃO: Problema de Storage

**Situação Atual**:
```
/home/hudson     → 10GB LVM vg6-lv_hudson (CHEIO para HUDSON!)
/financeiro      → 50GB (disponível, vazio)
/var             → 7,5GB (pequeno, não usar)
```

**Recomendação**:
- ✅ Usar `/financeiro/hudson` para storage de arquivos
- ✅ Manter `/home/hudson` apenas para código + venv + logs
- 📝 Atualizar `.env` com `STORAGE_ROOT=/financeiro/hudson`

---

## ✅ PASSO 0: Verificações Preliminares

Execute **no servidor** como usuário `hudson`:

```bash
# Verificar PostgreSQL
psql --version
psql -l  # Listar bancos

# Verificar Tesseract
tesseract --version

# Verificar Poppler
pdfimages -v

# Verificar espaço em disco
df -h /financeiro
df -h /home/hudson

# Verificar usuário hudson
whoami
id

# Verificar Python 3.11
python3.11 --version
which python3.11
```

**Se algo faltar**, execute como root:

```bash
# Instalar PostgreSQL 15 (recomendado) ou 13+
yum install -y postgresql-server postgresql-contrib

# Instalar Tesseract
yum install -y tesseract

# Instalar Poppler
yum install -y poppler-utils

# Iniciar PostgreSQL
systemctl start postgresql
systemctl enable postgresql
```

---

## 🔧 PASSO 1: Setup de Diretórios

Execute como **root**:

```bash
# Criar estrutura de storage
mkdir -p /financeiro/hudson/storage /financeiro/hudson/backups/{postgres,storage}
chown -R hudson:hudson /financeiro/hudson
chmod 700 /financeiro/hudson/backups

# Verificar permissões
ls -lah /financeiro/hudson/

# Criar link simbólico para facilitar (opcional)
ln -s /financeiro/hudson /var/hudson 2>/dev/null || echo "Link já existe"
```

---

## 🔄 PASSO 2: Clonar e Configurar Repositório

Execute como **hudson**:

```bash
# Se ainda não clonado:
cd /home
git clone https://github.com/Sugoi-SA/HUDSON.git

# Se já clonado, atualizar:
cd /home/HUDSON
git pull origin main

cd /home/HUDSON/backend

# Criar .env a partir do template
cp .env.example .env

# Editar com as configurações específicas:
nano .env
```

**Valores corretos para .env**:

```bash
# ✅ Usar Python 3.11 (já instalado)
DATABASE_URL=postgresql+psycopg://hudson:SENHA_REAL@localhost:5432/hudson

# ✅ Usar /financeiro (50GB disponíveis)
STORAGE_ROOT=/financeiro/hudson/storage

# ✅ Gerar API key segura
API_KEY=$(python3.11 -c "import secrets; print(secrets.token_hex(32))")

# ✅ Caminhos de sistema (geralmente já em PATH)
TESSERACT_CMD=/usr/bin/tesseract
POPPLER_PATH=/usr/bin
```

---

## 📦 PASSO 3: Setup do Banco de Dados

Execute como **root**:

```bash
# Inicializar cluster PostgreSQL (primeira vez)
sudo -u postgres /usr/lib/postgresql/15/bin/initdb -D /var/lib/postgresql/15/main 2>/dev/null || echo "Já inicializado"

# Iniciar PostgreSQL
systemctl start postgresql
systemctl status postgresql  # Deve estar "active (running)"

# Criar usuário hudson no PostgreSQL
sudo -u postgres createuser hudson 2>/dev/null || echo "Usuário já existe"

# Criar banco hudson
sudo -u postgres createdb -O hudson hudson 2>/dev/null || echo "Banco já existe"

# Conceder privilégios essenciais
sudo -u postgres psql -c "ALTER USER hudson CREATEDB;" 2>/dev/null || true

# Verificar criação
sudo -u postgres psql -l | grep hudson
```

**Esperado**:
```
hudson  | hudson | UTF8     | C       | C       | 
```

---

## 🐍 PASSO 4: Setup Python e Dependências

Execute como **hudson**:

```bash
cd /home/HUDSON/backend

# Criar virtualenv com Python 3.11
python3.11 -m venv .venv

# Ativar
source .venv/bin/activate

# Atualizar pip
pip install --upgrade pip wheel setuptools

# Instalar dependências (vai demorar ~2-3 min)
pip install -r requirements.txt

# Verificar instalação
python -c "import fastapi, sqlalchemy, psycopg; print('✅ Dependências OK')"
```

---

## 📊 PASSO 5: Inicializar Schema PostgreSQL

Execute como **hudson**:

```bash
cd /home/HUDSON

# Ativar venv
source backend/.venv/bin/activate

# Executar DDL
psql -d hudson -f specs/S2-schema.sql

# Verificar tabelas criadas
psql -d hudson -c "\dt"
```

**Esperado** (5 tabelas):
```
             List of relations
 Schema |     Name      | Type  | Owner
--------+---------------+-------+--------
 public | custody_log   | table | hudson
 public | declarations  | table | hudson
 public | entities      | table | hudson
 public | estant_types  | table | hudson
 public | items         | table | hudson
 public | relationships | table | hudson
```

---

## 🧪 PASSO 6: Testar Localmente (Antes de Systemd)

Execute como **hudson**:

```bash
cd /home/HUDSON/backend
source .venv/bin/activate

# Rodar servidor de teste
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Em outro terminal SSH:
curl -X GET http://localhost:8000/health

# Esperado:
# {"status": "ok", "timestamp": "2026-09-30T..."}
```

**Parar o servidor**: Ctrl+C no terminal

---

## 🔄 PASSO 7: Instalar Systemd Unit

Execute como **root**:

```bash
# Copiar arquivo
cp /home/HUDSON/backend/deploy/hudson-api.service /etc/systemd/system/

# Editar se necessário (verificar caminhos)
nano /etc/systemd/system/hudson-api.service

# Registrar
systemctl daemon-reload
systemctl enable hudson-api.service

# Iniciar
systemctl start hudson-api.service

# Verificar status
systemctl status hudson-api.service

# Ver logs em tempo real
journalctl -u hudson-api.service -f
```

---

## ⏰ PASSO 8: Agendar Backup via Cron

Execute como **hudson**:

```bash
# Editar crontab
crontab -e

# Adicionar linha (backup às 03h diariamente):
0 3 * * * /home/HUDSON/backend/deploy/backup.sh >> /tmp/hudson_backup.log 2>&1

# Salvar (Ctrl+X → Y → Enter)

# Verificar
crontab -l | grep hudson_backup
```

**Testar manualmente**:

```bash
/home/HUDSON/backend/deploy/backup.sh

# Verificar saída
ls -lah /financeiro/hudson/backups/postgres/
ls -lah /financeiro/hudson/backups/storage/
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

### 1. PostgreSQL

```bash
# ✅ Banco respondendo?
psql -d hudson -c "SELECT COUNT(*) FROM items;"
# Esperado: count = 0 (vazio)

# ✅ Trigger de append-only ativo?
psql -d hudson -c "\d items"
# Esperado: ver "BEFORE DELETE OR UPDATE"
```

### 2. API Health

```bash
curl -X GET http://localhost:8000/health
# Esperado: {"status": "ok", "timestamp": "..."}
```

### 3. API com Auth

```bash
# Sem API key (deve falhar)
curl -X GET http://localhost:8000/search?query=test
# Esperado: 401 Unauthorized

# Com API key
API_KEY=$(grep "^API_KEY=" /home/HUDSON/backend/.env | cut -d= -f2)
curl -X GET "http://localhost:8000/search?query=test" \
  -H "Authorization: Bearer $API_KEY"
# Esperado: {"results": [], "total": 0} (busca vazia, banco vazio)
```

### 4. Storage

```bash
# ✅ Diretório criado?
ls -lah /financeiro/hudson/storage/

# ✅ Permissões corretas?
stat /financeiro/hudson/storage/ | grep -i uid
# Esperado: Owner hudson
```

### 5. Backup

```bash
# ✅ Estrutura OK?
pg_restore --list /financeiro/hudson/backups/postgres/*.dump | head -5

# ✅ Storage OK?
tar -tzf /financeiro/hudson/backups/storage/*.tar.gz | head -5
```

### 6. Systemd Auto-restart

```bash
# ✅ Processo rodando?
ps aux | grep uvicorn | grep -v grep

# ✅ Matar e testar restart:
sudo systemctl kill -9 hudson-api.service
sleep 5
curl -X GET http://localhost:8000/health
# Esperado: 200 OK (processo reiniciado automaticamente)
```

---

## 🧪 PASSO 9: Teste de Ingestão Completo (Opcional)

Execute como **hudson** com um arquivo PDF/Word de teste:

```bash
cd /home/HUDSON/backend
source .venv/bin/activate

# Rodar CLI de ingestão
python scripts/import_cli.py \
  --file /caminho/para/arquivo_teste.pdf \
  --estante JURIDICO

# Verificar resultado
psql -d hudson -c "SELECT cota, hash_sha256, status FROM items ORDER BY criado DESC LIMIT 1;"
```

**Esperado**:
```
        cota         |                hash_sha256                 | status
---------------------|--------------------------------------------|---------
JURIDICO-????-????-?? | a1b2c3d4e5f6g7h8... (64 hex chars)        | indexado
```

---

## 🎯 Próximos Passos Após Validação

1. ✅ **Documentar** qualquer desvio ou erro encontrado
2. ✅ **Configurar Nginx** (se for expor para internet)
   ```bash
   # Exemplo: proxy reverso para localhost:8000
   # (deixar para próximo passo)
   ```
3. ✅ **Monitorar** logs por 24h
   ```bash
   journalctl -u hudson-api.service -f
   ```
4. ✅ **Testes de Carga** (preparar para Fase 1.1)
5. ✅ **Integração Zeev** (Fase 1.1)

---

## 🆘 Troubleshooting Comum

### Erro: "Connection refused" ao conectar PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
systemctl status postgresql

# Se não estiver, iniciar
sudo systemctl start postgresql

# Verificar socket Unix
ls -la /var/run/postgresql/
```

### Erro: "permission denied" em /financeiro/hudson

```bash
# Verificar permissões
ls -lad /financeiro/hudson

# Corrigir se necessário
sudo chown -R hudson:hudson /financeiro/hudson
```

### Erro: "ModuleNotFoundError: No module named 'tesseract'"

```bash
# pytesseract requer tesseract binário do sistema
# Verificar instalação
which tesseract
tesseract --version

# Se não estiver, instalar
sudo yum install -y tesseract
```

### API não reinicia após kill

```bash
# Verificar arquivo de serviço
cat /etc/systemd/system/hudson-api.service

# Verificar logs
journalctl -u hudson-api.service -n 50

# Se necessário, recarregar
sudo systemctl daemon-reload
sudo systemctl restart hudson-api.service
```

---

## 📞 Suporte

Se algo der errado:

1. **Coletar logs**:
   ```bash
   journalctl -u hudson-api.service -n 100 > /tmp/hudson_logs.txt
   psql -d hudson -c "SELECT COUNT(*) FROM items;" > /tmp/db_status.txt
   ```

2. **Me enviar output dos comandos acima**

3. **Eu vou ajudar a diagnosticar**

---

## 📋 Versão Adaptada Para

- **Servidor**: vmsever.sugoisa.com.br
- **SO**: CentOS 7
- **Python**: 3.11 (já instalado)
- **Storage**: /financeiro/hudson (50GB)
- **Backup**: /financeiro/hudson/backups
- **Prepared by**: Claude AI
- **Date**: 2026-09-30

---

**Status**: 🟢 **Pronto para executar**  
**Duração estimada**: 45-60 minutos (incluindo Postgres)  
**Risco**: 🟢 Baixo (servidor bem especificado)
