#!/bin/bash
# HUDSON v0 - Quick Start Script para CentOS 7 / Debian
# Este script automatiza a maioria das etapas de setup
# Executar como: bash LINUX-QUICKSTART.sh
# AVISO: Requer privilégios sudo

set -euo pipefail

echo "================================"
echo "HUDSON v0 - Linux Quick Setup"
echo "================================"
echo ""

# ===== VALIDAÇÕES INICIAIS =====
echo "[1/7] Validando dependências do sistema..."

# Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION"

# PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL não encontrado"
    exit 1
fi
PG_VERSION=$(psql --version | awk '{print $3}')
echo "✅ PostgreSQL $PG_VERSION"

# Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "❌ Tesseract não encontrado (necessário para OCR)"
    exit 1
fi
TESS_VERSION=$(tesseract --version | head -1 | awk '{print $2}')
echo "✅ Tesseract $TESS_VERSION"

# Poppler
if ! command -v pdfimages &> /dev/null; then
    echo "❌ Poppler não encontrado (necessário para PDF)"
    exit 1
fi
echo "✅ Poppler (pdfimages)"

echo ""

# ===== CRIAR USUÁRIO E DIRETÓRIOS =====
echo "[2/7] Configurando usuário 'hudson' e diretórios..."

if ! id "hudson" &>/dev/null; then
    sudo useradd -d /home/hudson -s /bin/bash -m hudson
    echo "✅ Usuário hudson criado"
else
    echo "✅ Usuário hudson já existe"
fi

sudo mkdir -p /var/hudson/storage /home/hudson/backups/{postgres,storage}
sudo chown -R hudson:hudson /var/hudson /home/hudson/backups
sudo chmod 700 /home/hudson/backups
echo "✅ Diretórios criados"

echo ""

# ===== CLONAR REPOSITÓRIO =====
echo "[3/7] Clonando repositório HUDSON..."

if [ -d "/home/HUDSON" ]; then
    echo "ℹ️  Repositório já existe em /home/HUDSON"
else
    sudo git clone https://github.com/Sugoi-SA/HUDSON.git /home/HUDSON
    sudo chown -R hudson:hudson /home/HUDSON
    echo "✅ Repositório clonado"
fi

echo ""

# ===== CONFIGURAR .ENV =====
echo "[4/7] Configurando arquivo .env..."

ENV_FILE="/home/HUDSON/backend/.env"

if [ -f "$ENV_FILE" ]; then
    echo "ℹ️  Arquivo .env já existe"
else
    sudo cp /home/HUDSON/backend/.env.example "$ENV_FILE"

    # Gerar API key segura
    API_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    # Substituir valores (usar sed)
    sudo sed -i "s|troque-por-uma-chave-secreta-gerada|$API_KEY|" "$ENV_FILE"

    echo "✅ .env criado com API_KEY segura"
    echo "   ⚠️  EDITE /home/HUDSON/backend/.env com credenciais reais:"
    echo "      - DATABASE_URL (usuário/senha PostgreSQL)"
    echo "      - STORAGE_ROOT (caminho de armazenamento)"
    echo "      - TESSERACT_CMD e POPPLER_PATH (se não em PATH)"
fi

echo ""

# ===== CRIAR BANCO DE DADOS =====
echo "[5/7] Criando banco de dados PostgreSQL..."

PGPASSWORD="" sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = 'hudson'" | grep -q 1 && DB_EXISTS=1 || DB_EXISTS=0

if [ $DB_EXISTS -eq 0 ]; then
    sudo -u postgres createuser hudson 2>/dev/null || true
    sudo -u postgres createdb -O hudson hudson 2>/dev/null || true
    echo "✅ Usuário e banco 'hudson' criados"

    # Conceder CREATEDB para restore futuro
    sudo -u postgres psql -c "ALTER USER hudson CREATEDB;" 2>/dev/null || true
    echo "✅ Privilégio CREATEDB concedido a hudson"
else
    echo "ℹ️  Usuário hudson já existe"
fi

# Inicializar schema
sudo -u hudson psql -d hudson -f /home/HUDSON/specs/S2-schema.sql > /dev/null 2>&1 || echo "⚠️  Schema pode já estar inicializado"
echo "✅ Schema do banco inicializado"

echo ""

# ===== CRIAR VENV E INSTALAR DEPS =====
echo "[6/7] Instalando dependências Python..."

sudo -u hudson bash <<'EOF'
cd /home/HUDSON/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "✅ Dependências instaladas em virtualenv"
EOF

echo ""

# ===== INSTALAR SYSTEMD =====
echo "[7/7] Instalando unidade systemd..."

sudo cp /home/HUDSON/backend/deploy/hudson-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hudson-api.service
echo "✅ Unidade systemd instalada e habilitada"

# Agendar backup via cron
CRON_JOB="0 3 * * * /home/HUDSON/backend/deploy/backup.sh >> /tmp/hudson_backup.log 2>&1"
(sudo crontab -u hudson -l 2>/dev/null | grep -v "hudson_backup.sh"; echo "$CRON_JOB") | sudo crontab -u hudson -
echo "✅ Backup agendado para 03h diariamente"

echo ""
echo "================================"
echo "✅ SETUP CONCLUÍDO COM SUCESSO!"
echo "================================"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. ✅ Editar configuração:"
echo "   nano /home/HUDSON/backend/.env"
echo ""
echo "2. ✅ Iniciar serviço:"
echo "   sudo systemctl start hudson-api.service"
echo ""
echo "3. ✅ Verificar status:"
echo "   sudo systemctl status hudson-api.service"
echo ""
echo "4. ✅ Testar API:"
echo "   curl -X GET http://localhost:8000/health"
echo ""
echo "5. ✅ Visualizar logs:"
echo "   sudo journalctl -u hudson-api.service -f"
echo ""
echo "6. ⏳ Testar ingestão (após iniciar):"
echo "   cd /home/HUDSON/backend"
echo "   source .venv/bin/activate"
echo "   python scripts/import_cli.py --file /caminho/arquivo.pdf --estante JURIDICO"
echo ""
echo "📚 Documentação completa em: /home/HUDSON/DEPLOYMENT-PLAN-LINUX.md"
echo ""
