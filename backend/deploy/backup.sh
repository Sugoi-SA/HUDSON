#!/bin/bash
# Backup diario do banco 'hudson' (pg_dump formato custom) e do hudson_storage
# (tar.gz). Le credenciais do .env em runtime - nunca hardcoded aqui.
set -euo pipefail

BACKEND_DIR="/home/hudson/HUDSON/backend"
BACKUP_ROOT="/home/hudson/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_DIR="$BACKUP_ROOT/postgres"
STORAGE_BACKUP_DIR="$BACKUP_ROOT/storage"
RETENTION_DAYS=14

mkdir -p "$DB_BACKUP_DIR" "$STORAGE_BACKUP_DIR"

set -a
source "$BACKEND_DIR/.env"
set +a

eval "$("$BACKEND_DIR/.venv/bin/python3" -c "
import os
from urllib.parse import urlparse
u = urlparse(os.environ['DATABASE_URL'].replace('postgresql+psycopg://', 'postgresql://'))
print(f'export PGUSER={u.username}')
print(f'export PGPASSWORD={u.password}')
print(f'export PGHOST={u.hostname}')
print(f'export PGPORT={u.port}')
print(f'export PGDATABASE={u.path.lstrip(chr(47))}')
")"

echo "[$(date)] Backup do banco '$PGDATABASE'..."
pg_dump -Fc -f "$DB_BACKUP_DIR/hudson_${DATE}.dump"

echo "[$(date)] Backup do hudson_storage ($STORAGE_ROOT)..."
tar -czf "$STORAGE_BACKUP_DIR/hudson_storage_${DATE}.tar.gz" -C "$(dirname "$STORAGE_ROOT")" "$(basename "$STORAGE_ROOT")"

echo "[$(date)] Removendo backups com mais de ${RETENTION_DAYS} dias..."
find "$DB_BACKUP_DIR" -name 'hudson_*.dump' -mtime +${RETENTION_DAYS} -delete
find "$STORAGE_BACKUP_DIR" -name 'hudson_storage_*.tar.gz' -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Backup concluido: $DB_BACKUP_DIR/hudson_${DATE}.dump"
