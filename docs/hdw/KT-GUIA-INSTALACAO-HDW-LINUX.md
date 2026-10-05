# 📘 Guia de Instalação e KT (Knowledge Transfer): HUDSON DW no Linux
**Destinatário:** Time de Infraestrutura e TI da SUGOI S.A.  
**Emissor:** Dr. Tylor e Equipe de Arquitetura & Engenharia de Software  
**Sistema:** HUDSON DW (Data Warehouse Soberano — Biblioteca Digital Forense)  
**Servidor:** `vmsever.sugoisa.com.br` (CentOS Linux 7 / RHEL 7 / Rocky / Ubuntu)  
**Nível de Didática:** Passo a passo detalhado (mastigado do zero)

---

## 🧭 O que é o HUDSON DW e o que vamos instalar?

Imagine que o **HUDSON DW** é um **Cofre Forte Digital** onde nenhum arquivo é jogado fora, ninguém consegue alterar contratos antigos em segredo e todo documento ganha uma "impressão digital matemática" única (Hash SHA-256).

Para esse cofre funcionar no servidor Linux, precisamos de apenas **4 coisas trabalhando juntas**:
1. **O Porteiro (FastAPI / Python 3.11):** O programa que recebe os arquivos e atende pedidos.
2. **O Caderno Notarial (PostgreSQL 15):** O banco de dados onde anotamos quem guardou o que e geramos cotas imutáveis.
3. **A Sala do Cofre (`/financeiro/hudson/storage`):** O disco com 50 GB livres onde os arquivos reais ficam trancados.
4. **Os Olhos do Sistema (Tesseract OCR & Poppler):** Ferramentas que leem o texto de PDFs e imagens escaneadas.

---

## 🧰 Checklist de Ferramentas Pré-Requisito

Antes de começar, abra o terminal do servidor e verifique se as ferramentas já estão instaladas digitando estes comandos:

| Ferramenta | Comando para Checar | Saída Esperada | O que fazer se não tiver? |
| :--- | :--- | :--- | :--- |
| **Git** | `git --version` | `git version 1.8...` ou superior | `sudo yum install -y git` |
| **Python 3.11** | `python3.11 --version` | `Python 3.11.x` | `sudo yum install -y python311 python311-devel` |
| **PostgreSQL 15** | `psql --version` | `psql (PostgreSQL) 15.x` | `sudo yum install -y postgresql15-server postgresql15-contrib` |
| **Tesseract OCR** | `tesseract --version` | `tesseract 3.04...` ou superior | `sudo yum install -y tesseract` |
| **Poppler Utils** | `pdfimages -v` | `pdfimages version 0.26...` ou superior | `sudo yum install -y poppler-utils` |
| **Disco Livre** | `df -h /financeiro` | Mais de 30GB disponíveis | Verificar partição com `lsblk` |

---

## 🗺️ Workflow de Ingestão: Das Pastas da SUGOI até a Custódia Final

Este é o caminho exato que o documento percorre quando entra no HUDSON DW:

```mermaid
sequenceDiagram
    autonumber
    actor Operador as 📁 Pastas SUGOI (Rede / Obras / Financeiro)
    participant CLI as ⚙️ import_cli.py / Watcher Daemon
    participant HASH as 🧮 Hashing Service (SHA-256)
    participant PG as 🐘 PostgreSQL (Dedup & Transação)
    participant STORE as 🗄️ Storage Soberano (/financeiro/hudson)
    participant OCR as 👁️ Tesseract + Poppler (Extração)
    participant HDC as 🌐 HUDSON DC (Nuvem Daisugi)

    Operador->>CLI: Varrer diretório de origem (--source /dados/sugoi --wbs OBRA-01)
    loop Para cada arquivo encontrado
        CLI->>HASH: Ler arquivo em streaming (chunks de 64KB)
        HASH-->>CLI: Retorna hash SHA-256 (64 hex chars)
        
        CLI->>PG: SELECT id FROM items WHERE hash_sha256 = :hash
        alt Arquivo Já Existe (Duplicado)
            PG-->>CLI: Retorna item_id existente
            CLI->>PG: INSERT INTO custody_log (event_type='deduplicacao', reason='origem_repetida')
            Note over CLI,PG: Binário descartado. Evita duplicidade em disco.
        else Arquivo Novo
            CLI->>CLI: Classificar Estante via Regex (ex: "Contrato" -> JURIDICO)
            CLI->>PG: INSERT INTO items (status='recebido', estante, obra_wbs)
            CLI->>PG: INSERT INTO custody_log (event_type='recebimento')
            
            CLI->>STORE: Copiar para /financeiro/hudson/storage/{estante}/{hash[:2]}/{hash}.ext
            
            CLI->>HASH: Recomputar SHA-256 do arquivo recém-gravado no Storage
            alt Hash Não Bate (Corrupção de I/O)
                CLI->>STORE: Deletar cópia corrompida
                CLI->>PG: INSERT INTO custody_log (event_type='alerta_integridade')
            else Hash 100% Íntegro
                CLI->>PG: Gerar Cota HUDSON determinística ([ESTANTE]-[WBS]-[AAAA]-[hash8])
                CLI->>OCR: Extrair texto (Tesseract OCR / pdfplumber)
                OCR-->>CLI: Texto bruto do documento
                CLI->>PG: Atualizar item (content_text, status='indexado', tsv=to_tsvector)
                CLI->>PG: INSERT INTO custody_log (event_type='indexacao')
                
                Note over CLI,HDC: Sincronização Federada com o HUDSON PAI
                CLI->>HDC: POST /api/v1/sync/metadata (tenant='sugoi_sa', hash, cota, entidades)
                HDC-->>CLI: HTTP 200 OK (Grafo Central Atualizado)
            end
        end
    end
```

---

## 👣 Passo a Passo de Instalação (Mastigado)

### Passo 1: Criar o Usuário do Sistema e Pastas no Disco Grande
Não queremos lotar a partição do sistema operacional (`/` ou `/home`). Vamos usar a partição `/financeiro` que tem 50 GB livres:

```bash
# 1.1 Criar o usuário 'hudson' se ainda não existir
sudo useradd -m -s /bin/bash hudson

# 1.2 Criar os diretórios do cofre na partição /financeiro
sudo mkdir -p /financeiro/hudson/storage
sudo mkdir -p /financeiro/hudson/backups/postgres
sudo mkdir -p /financeiro/hudson/backups/storage

# 1.3 Dar a chave desse diretório para o usuário 'hudson'
sudo chown -R hudson:hudson /financeiro/hudson
sudo chmod 750 /financeiro/hudson/storage
sudo chmod 700 /financeiro/hudson/backups
```

---

### Passo 2: Baixar o Código Fonte do HUDSON
Faça login com o usuário `hudson` e baixe o repositório do GitHub:

```bash
# 2.1 Mudar para o usuário hudson
sudo su - hudson

# 2.2 Clonar o repositório oficial
cd /home/hudson
git clone https://github.com/Sugoi-SA/HUDSON.git

# 2.3 Entrar na pasta do backend
cd /home/hudson/HUDSON/backend
```

---

### Passo 3: Criar o Ambiente Virtual Python (Isolamento)
Nunca instalamos nada no Python global do sistema. Criamos uma "caixinha de areia" (venv):

```bash
# 3.1 Criar o ambiente virtual chamado .venv dentro de backend
python3.11 -m venv /home/hudson/HUDSON/backend/.venv

# 3.2 Ativar a caixinha
source /home/hudson/HUDSON/backend/.venv/bin/activate

# 3.3 Atualizar o instalador de pacotes pip
pip install --upgrade pip

# 3.4 Instalar as dependências do HUDSON
pip install -r requirements.txt
```
> **Como sei que deu certo?**  
> Digite `python -c "import fastapi, sqlalchemy, psycopg; print('TUDO OK!')"`  
> Se imprimir `TUDO OK!`, o Python está pronto.

---

### Passo 4: Preparar o Banco de Dados PostgreSQL 15
O banco precisa de um usuário, uma senha e o banco chamado `hudson`.

Como usuário `postgres` (administrador do banco):
```bash
sudo -u postgres psql
```
Dentro do prompt do PostgreSQL (`postgres=#`), digite estes comandos:
```sql
CREATE USER hudson WITH PASSWORD 'SugoiHudson#2026';
CREATE DATABASE hudson OWNER hudson;
GRANT ALL PRIVILEGES ON DATABASE hudson TO hudson;
ALTER USER hudson CREATEDB;
\q
```

Agora, aplique as tabelas e triggers de custódia imutável:
```bash
cd /home/hudson/HUDSON
psql -U hudson -h 127.0.0.1 -d hudson -f specs/S2-schema.sql
```
*(Digite a senha `SugoiHudson#2026` quando pedir).*

---

### Passo 5: Criar o Arquivo Secreto de Configuração (`.env`)
O HUDSON lê suas configurações de um arquivo chamado `.env`. Vamos criá-lo:

```bash
cat << 'EOF' > /home/hudson/HUDSON/backend/.env
# Configurações Oficiais HUDSON DW - SUGOI S.A.
DATABASE_URL=postgresql+psycopg://hudson:SugoiHudson#2026@127.0.0.1:5432/hudson
STORAGE_ROOT=/financeiro/hudson/storage
API_KEY=sugoi_master_hudson_dw_key_2026

# Caminhos dos utilitários do CentOS 7 (se necessário)
TESSERACT_CMD=/usr/bin/tesseract
POPPLER_PATH=/usr/bin
EOF

# Proteger o arquivo para ninguém de fora ler a senha
chmod 600 /home/hudson/HUDSON/backend/.env
```

---

### Passo 6: Configurar o Serviço no Linux (Systemd Auto-Start)
Queremos que o HUDSON inicialize sozinho se o servidor reiniciar:

Como `root` ou com `sudo`:
```bash
# 6.1 Copiar o arquivo de serviço para o sistema operacional
sudo cp /home/hudson/HUDSON/backend/deploy/hudson-api.service /etc/systemd/system/

# 6.2 Avisar o Linux que tem um serviço novo
sudo systemctl daemon-reload

# 6.3 Ligar o serviço e habilitar para iniciar no boot
sudo systemctl enable hudson-api
sudo systemctl start hudson-api

# 6.4 Olhar se está rodando feliz (deve estar verde: active (running))
sudo systemctl status hudson-api
```

---

### Passo 7: O Teste de Fogo (Smoke Test)
Vamos fazer uma chamada HTTP local para ver se a API está respondendo na porta 8000:

```bash
curl -i http://127.0.0.1:8000/health
```

**Resposta esperada na tela:**
```http
HTTP/1.1 200 OK
content-type: application/json

{"status":"ok"}
```

Se viu isso, **PARABÉNS! O HUDSON DW está oficialmente vivo e operando no servidor da SUGOI!** 🚀

---

### Passo 8: Como Alimentar o Cofre (Importando Pastas da SUGOI)
Para pegar uma pasta cheia de contratos ou notas da SUGOI e guardar no acervo:

```bash
# 1. Ativar o ambiente
source /home/hudson/HUDSON/backend/.venv/bin/activate
cd /home/hudson/HUDSON/backend

# 2. Rodar o importador informando a pasta e o código da obra/projeto
python scripts/import_cli.py --source /caminho/onde_estao_os_documentos --wbs OBRA-01
```

O script vai mostrar na tela:
* Quantos arquivos foram encontrados;
* Quantos são novos e foram catalogados;
* Quantos já existiam (e foram deduplicados sem ocupar espaço à toa);
* A cota gerada para cada um.

---

## 🐳 Opção Alternativa: Rodar com Docker & Docker Compose
Se a equipe de TI preferir rodar em contêineres Docker, o repositório já suporta a topologia isolada de redes:

```bash
cd /home/hudson/HUDSON
# Subir com docker-compose
docker compose up -d
```
* **Rede Interna:** `core` (PostgreSQL, ChromaDB e API).
* **Porta Exposta:** `8000` (API do HUDSON).

---

## 📋 Ações Finais Recomendadas pelo Dr. Tylor e Conselho

1. **Rotina de Backup Diário:** Agendar no cron do usuário `hudson` o script `/home/hudson/HUDSON/backend/deploy/backup.sh` para rodar às 02:00 da manhã.
2. **Permissão CREATEDB:** Manter o usuário `hudson` com a permissão `CREATEDB` no PostgreSQL para testes periódicos de restore de integridade forense.
3. **Monitoramento:** Configurar monitoramento simples checando a cada 5 minutos o endpoint `http://127.0.0.1:8000/health`.
