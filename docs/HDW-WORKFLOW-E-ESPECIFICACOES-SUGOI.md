# 🏛️ Especificação Técnica & Workflow Operacional: HUDSON DW Soberano (SUGOI S.A.)

**Data:** Outubro de 2026  
**Status:** 🚀 **HOMOLOGADO PARA IMPLANTAÇÃO IMEDIATA NO SERVIDOR LINUX**  
**Instância:** HUDSON DW Filhote (Data Warehouse Local do Cliente SUGOI S.A.)  
**Servidor Físico Alvo:** `vmsever.sugoisa.com.br`  
**Parecer e Curadoria:** Dr. Tylor, Arquiteto de Sistemas, Especialista em Processos e Especialista em Programação  

---

## 1. Identidade e Propósito do HDW

O **HUDSON DW** é a **Biblioteca Soberana Digital Forense** da SUGOI S.A. Ele opera sob o princípio da **Imutabilidade Estrita**, **Zero-Exclusion** (nenhum binário sob custódia é excluído) e **Rastreabilidade Probatória Criptográfica**.

O HDW tem como objetivo blindar a SUGOI S.A. em auditorias de fundos, securitizadoras (CRI / Opea), bancos financiadores, fiscalizações e contenciosos jurídicos, garantindo que contratos, laudos periciais, medições de obras (CCBs) e documentos contábeis possuam integridade matematicamente comprovável.

### Pilares Fundamentais do HDW
* **Streaming Hash SHA-256:** Leitura em blocos (*chunked*) no momento do recebimento, sem exaurir a memória RAM.
* **Deduplicação Determinística:** Rejeição de duplicatas físicas em disco com registro de nova ocorrência no log de auditoria.
* **Classificação por 6 Estantes:** Separação estrita dos documentos nos contextos: `JURIDICO`, `FINANCEIRO`, `RH`, `OPERACIONAL`, `CONTABIL` e `ADMINISTRATIVO`.
* **Cota HUDSON (MARC):** Identificador padronizado, determinístico e reversível no formato `[ESTANTE]-[WBS_OBRA]-[ANO]-[hash8]`.
* **Custody Log Append-Only:** Registro inalterável com triggers no PostgreSQL 15 que bloqueiam comandos `UPDATE` e `DELETE`.
* **Certidão de Autenticidade Sob Demanda (`/authenticity`):** Recálculo de hash em tempo real para emissão de certidão de prova pericial.

---

## 2. Serviços Prestados à SUGOI e seu Time

```mermaid
flowchart LR
    subgraph TIME_SUGOI["👥 Time Interno SUGOI S.A."]
        FIN["💰 Financeiro & Contábil<br/>(Notas, DREs, Conciliações)"]
        ENG["🏗️ Engenharia & Obras<br/>(Medições, CCBs, Diários)"]
        JUR["⚖️ Jurídico & Compliance<br/>(Contratos, Ações, Laudos)"]
        RH["👔 Recursos Humanos<br/>(Prontuários, Rescisões)"]
    end

    subgraph HDW_LOCAL["📦 HUDSON DW Soberano (:8000)"]
        ACERVO["🗄️ Acervo Blindado (/financeiro/hudson)"]
        BUSCA["🔍 Busca Full-Text (tsvector PT-BR)"]
        LAUDO["📜 Certidão de Autenticidade Forense"]
        CUSTODIA["🛡️ Custody Log Append-Only"]
    end

    subgraph DC_DAI["🌐 HUDSON DC (:9000) & DAI (:8001)"]
        LOBBY["🌸 DAI Smart Reception (Portaria/Lobby)"]
        KANSA["🛡️ KAN-SA (Esteira de Perícia PAM)"]
        ALERT["🚨 Sirene Emergência P1 (Dr. SaulLM)"]
    end

    TIME_SUGOI <-->|Busca Cláusulas / Localiza Docs / Emite Laudos| HDW_LOCAL
    TIME_SUGOI -->|Input de Pastas Locais / Scans / Zeev| HDW_LOCAL
    
    HDW_LOCAL <-->|Metadados Leves & Hashes (Sem binário)| DC_DAI
    DC_DAI <-->|Triagem no Totem & Quarentena PAM| TIME_SUGOI
```

1. **Blindagem Contra Extravio e Fraude:** Centraliza os documentos da empresa em armazenamento local blindado com verificação cruzada de integridade pós-cópia.
2. **Localização Instantânea de Cláusulas e Dados:** Motor de busca full-text no PostgreSQL 15 (`tsvector` em português) para consultar termos, nomes de sócios, valores e CNPJs em milissegundos.
3. **Ponte com o HUDSON DC (Data Center) e DAI:**
   - **Portaria Inteligente (DAI):** Validação de entidades e confirmação de documentos recebidos no balcão sem tráfego de arquivos pesados.
   - **Quarentena PAM:** Validação de medições de engenharia com dupla alçada (*Maker-Checker*) articulada com o KAN-SA.

---

## 3. Workflow de Ingestão: Das Pastas da SUGOI ao Acervo Blindado

O processo de captura de documentos a partir de diretórios de rede, compartilhamentos SMB/NFS ou pastas locais da SUGOI segue o fluxo operacional abaixo:

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

### Detalhamento das Etapas de Ingestão:
1. **Intake & Streaming:** O arquivo é lido diretamente da origem em blocos de 64 KB, calculando o hash SHA-256 sem impacto na memória.
2. **Deduplicação Atômica:** Consulta no banco pelo hash SHA-256. Se já existir, a duplicata é rejeitada e o evento registrado no log de custódia.
3. **Roteamento de Estante:** O nome do arquivo e metadados são inspecionados contra as regras de negócio para determinar a estante de destino.
4. **Armazenamento com Sharding e Double-Check:** O arquivo é gravado no caminho `/financeiro/hudson/storage/{estante}/{hash[:2]}/{hash}.{ext}`. Imediatamente após a gravação, o hash do arquivo no disco final é recomputado. Se houver divergência, a cópia é removida e um alerta gravado.
5. **Cota HUDSON:** Geração determinística baseada na estante, código WBS do empreendimento, ano e prefixo do hash.
6. **Extração de Texto & Indexação:** Aplicação de OCR (Tesseract) e parser Poppler para gerar o texto indexado no `tsvector` do PostgreSQL.
7. **Federação Segura com o HUDSON DC:** Notificação assíncrona enviada ao HUDSON PAI com o hash e cota (sem envio do binário), mantendo a soberania do cliente.

---

## 4. Especificações do Servidor Linux (`vmsever.sugoisa.com.br`)

O diagnóstico físico do servidor confirma alta capacidade computacional:

| Componente | Especificação Real | Diretriz de Engenharia |
| :--- | :--- | :--- |
| **CPU** | 2x Intel Xeon E5-2630 v3 (**32 vCPUs lógicas**) | Capacidade para paralelismo massivo em OCR e hashing. |
| **Memória RAM** | **31 GB Total** (25 GB Livres) | Suporte amplo para buffers de banco e filas de importação. |
| **Sistema Operacional** | **CentOS Linux 7 (Kernel 3.10.0-1127)** | Execução direta via Python 3.11 nativo e Systemd. |
| **Storage Alvo** | **`/financeiro` (50 GB Livres e Dedicados)** | **Obrigatório:** O acervo (`STORAGE_ROOT`) deve residir em `/financeiro/hudson/storage` para evitar saturação da raiz. |

### Ferramentas Instaladas e Validadas
* **Python 3.11.11:** Ambiente virtual isolado em `/home/hudson/hudson-env`.
* **PostgreSQL 15.19:** Porta 5432, banco `hudson`, usuário `hudson`.
* **Tesseract OCR 3.04.00:** Extração de texto em imagens e PDFs escaneados.
* **Poppler Utils:** Utilitários `pdfimages` e `pdftotext`.
* **Systemd:** Gerenciamento do serviço `hudson-api.service` na porta 8000.

---

## 5. Roteiro Prático de Implantação no Servidor Linux

### Passo 1: Configuração das Variáveis de Ambiente (`.env`)
No diretório da aplicação (`/home/hudson/app` ou caminho equivalente no `vmsever`):

```bash
# Configuração do HUDSON DW Local (Sugoi)
DATABASE_URL=postgresql://hudson:SENHA_AQUI@localhost:5432/hudson
STORAGE_ROOT=/financeiro/hudson/storage
BACKUP_ROOT=/financeiro/hudson/backups
PORT=8000
HUDSON_API_KEY=CHAVE_MESTRA_LOCAL_SUGOI
HUDSON_DC_URL=https://hudson.daisugi.com.br
HUDSON_DC_TOKEN=TOKEN_JWT_FEDERACAO
TENANT_ID=sugoi_sa
```

### Passo 2: Inicialização da Estrutura de Diretórios
```bash
sudo mkdir -p /financeiro/hudson/storage /financeiro/hudson/backups/{postgres,storage}
sudo chown -R hudson:hudson /financeiro/hudson
sudo chmod 700 /financeiro/hudson/backups
```

### Passo 3: Criação das Tabelas e Triggers no PostgreSQL
```bash
psql -U hudson -d hudson -f specs/S2-schema.sql
```

### Passo 4: Habilitação e Inicialização do Serviço Systemd
```bash
sudo cp backend/deploy/hudson-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hudson-api
sudo systemctl start hudson-api
sudo systemctl status hudson-api
```

### Passo 5: Execução do Teste de Importação em Lote
```bash
source /home/hudson/hudson-env/bin/activate
python backend/scripts/import_cli.py --source /caminho/pasta_sugoi --wbs OBRA_PILOTO
```
