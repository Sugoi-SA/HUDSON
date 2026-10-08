# RELATÓRIO TÉCNICO DE INSTALAÇÃO, TESTES E ARQUITETURA DE REDE (VPN)
## HUDSON DATA WAREHOUSE (HDW) - AMBIENTE LINUX SUGOI

**Data do Relatório:** 08/10/2026  
**Responsável Técnico:** Equipe de Arquitetura & Automação HDW / PMO de TI  
**Destinatários:**  
1. Equipe de TI da SUGOI Construtora S.A.  
2. Agente Especialista Claude  
3. Dr. Taylor Code & Ronaldo Akagui  
**Servidor de Produção HDW:** Host Linux CentOS 7 (`192.168.1.122`)  
**Repositório Oficial HDW:** `https://github.com/Sugoi-SA/HUDSON.git`  
**Repositório de Ferramentas:** `https://github.com/MV-AKAGUI/FERRAMENTAS--FUZZY---HARNESS-`  

---

## 1. RESUMO EXECUTIVO

Em conformidade com as diretrizes do Dr. Taylor Code, do agente Claude e do comitê de tecnologia da SUGOI, foi realizada a implantação, configuração e bateria integral de testes de todas as ferramentas complementares forenses, extratores e motores de inteligência artificial no ambiente do **Hudson Data Warehouse (HDW)**.

### Resultados Consolidados:
- **Infraestrutura Pré-Existente:** Preservada em **100%**, com zero indisponibilidade (zero downtime). O banco de dados PostgreSQL 18.6, suas 9 tabelas do schema `hudson`, seu particionamento de custódia e seus volumes de armazenamento permaneceram totalmente operacionais e íntegros.
- **Isolamento do Hudson DC (HDC):** Nenhuma alteração foi realizada em relação ao HDC, respeitando o fato de que este roda de forma segregada no Oracle Cloud (OCI).
- **Novas Ferramentas Forenses e IA:** Instaladas, verificadas e homologadas com sucesso (Docling, RapidOCR, RapidFuzz, Desbloqueador de PDF/Word/Excel/RAR/ZIP, LibreOffice CLI, UnRAR nativo e Libmagic).
- **Persistência Docker:** A imagem live foi selada com `docker commit hudson-app hudson-app:base` e os arquivos `Dockerfile` e `requirements.txt` foram sincronizados para garantir persistência em qualquer ciclo de vida futuro.

---

## 2. ARQUITETURA DE SEGURANÇA E CONECTIVIDADE VIA OPENVPN (O VPN)

### 2.1. Cenário de Isolamento do Servidor Linux
O servidor físico/VM que hospeda o HDW no IP `192.168.1.122` é uma máquina **isolada na rede interna da SUGOI**. Por razões de cibersegurança, compliance e proteção de dados sigilosos e fiscais da construtora, **o servidor não possui portas expostas diretamente para a Internet pública**.

### 2.2. O Canal de Acesso Seguro: OpenVPN
Qualquer sistema, estação de trabalho remota ou robô de inteligência artificial externo (por exemplo: **Dai**, **Kan-sa**, robôs em nuvem ou o **HDC na Oracle Cloud**) que necessite consumir a API do HDW (`http://192.168.1.122:8000`) ou conectar-se diretamente ao PostgreSQL (`192.168.1.122:5432`) **deve obrigatoriamente trafegar pelo túnel seguro OpenVPN**.

### 2.3. Especificações Técnicas do Perfil / Cartão de Acesso OpenVPN
Conforme analisado nos arquivos de configuração disponibilizados pela TI da SUGOI (`C:\Users\Ronaldo Akagui.SUG00245\OneDrive - SUGOI CONSTRUTORA S.A\Documentos\VPN\hudson_vpn.ovpn`):

| Parâmetro Técnico | Especificação Homologada |
| :--- | :--- |
| **Protocolo de Rede** | OpenVPN Client (`proto udp`, `dev tun`) |
| **Gateway / IP Remoto** | `87.102.137.206` na porta `1194` (UDP) |
| **Criptografia de Canal** | `AES-256-CBC` com autenticação de integridade `SHA256` |
| **Autenticação de Segurança** | Certificados digitais X.509 PKI (`<ca>`, `<cert>`, `<key>`) e controle TLS |
| **Resolução de Rota** | Redirecionamento para a sub-rede privada `192.168.1.0/24` |
| **Perfis Existentes** | `hudson_vpn.ovpn` (perfil da aplicação) e `root_vpn.ovpn` (perfil administrativo) |

### 2.4. Como Aplicações Externas (Dai, Kan-sa, HDC na Nuvem) Devem Acessar o HDW
1. **Emissão do Cartão de Acesso:** A TI da SUGOI gera um arquivo de credencial `.ovpn` dedicado para o serviço cliente.
2. **Execução do Túnel:**
   - **Em Servidores Linux / Containers (Ex: Oracle Cloud):** O OpenVPN pode rodar como um serviço de sistema (`systemctl start openvpn-client@hudson`) ou como um container sidecar com permissões de rede `NET_ADMIN`.
   - **Em Estações Windows:** O OpenVPN Connect ou OpenVPN GUI importa o arquivo `.ovpn` e estabelece a conexão criptografada.
3. **Consumo dos Serviços HDW:**
   - **API REST do HDW:** `http://192.168.1.122:8000` (Endpoints `/health`, ingestão, consulta forense e extração).
   - **Banco de Dados PostgreSQL:** `192.168.1.122:5432`, Banco: `sugoi`, Schema: `hudson`.

---

## 3. RELATÓRIO DE TESTES E DIAGNÓSTICO DO SERVIDOR LINUX

Realizamos testes automatizados via SSH e execução interna no Docker em 08/10/2026. Abaixo estão os resultados obtidos:

### 3.1. Estado dos Containers Docker
```text
NAMES            STATUS                  PORTS
hudson-app       Up 46 hours             0.0.0.0:8000->8000/tcp, :::8000->8000/tcp
sugoi-postgres   Up 47 hours (healthy)   0.0.0.0:5432->5432/tcp, :::5432->5432/tcp
```
- Ambos os serviços operando continuamente sem falhas e com status *healthy*.

### 3.2. Integridade do Banco de Dados PostgreSQL (sugoi-postgres)
- **Instância:** PostgreSQL 18.6
- **Database:** `sugoi` (Encoding UTF8, Locale pt_BR.UTF-8)
- **Schema:** `hudson`
- **Tabelas Encontradas e Validadas (9 tabelas):**
  1. `hudson.custody_log` (Tabela mestre particionada)
  2. `hudson.custody_log_2025` (Partição do ano 2025)
  3. `hudson.custody_log_2026` (Partição do ano 2026)
  4. `hudson.custody_log_2027` (Partição do ano 2027)
  5. `hudson.declarations`
  6. `hudson.entities`
  7. `hudson.estant_types` (Contém os 6 tipos de estantes homologados)
  8. `hudson.items`
  9. `hudson.relationships`
- **Índices de Partição:** Todos os 17 índices e chaves primárias do `custody_log` permanecem ativos e indexados por `event_type` e `item_id`.
- **Volume Físico:** Volume Docker `sugoi-postgres-data` intacto.

### 3.3. Teste da API FastAPI HDW
```http
GET http://localhost:8000/health
HTTP/1.1 200 OK
date: Thu, 08 Oct 2026 18:12:02 GMT
server: uvicorn
content-length: 15
content-type: application/json

{"status":"ok"}
```

---

## 4. RELATÓRIO DAS NOVAS FERRAMENTAS INSTALADAS

Todos os pacotes foram validados em tempo de execução dentro do container `hudson-app` (Python 3.11.11):

| Ferramenta / Módulo | Versão | Status | Descrição e Função no HDW |
| :--- | :--- | :---: | :--- |
| **Docling (IBM Deep Search)** | `2.135.0` | ✅ Operacional | Leitura multimodal profunda de PDFs complexos, notas fiscais, relatórios contratuais e tabelas com reconstrução hierárquica. |
| **RapidOCR** | `1.4.4` (ONNX Runtime) | ✅ Operacional | OCR ultrarrápido com aceleração local ONNX para documentos escaneados e comprovantes ilegíveis. |
| **RapidFuzz** | `3.14.6` | ✅ Operacional | Motor de casamento difuso (fuzzy string matching) C++ de altíssimo desempenho para conciliação contábil, nomes de credores e títulos de dívida. |
| **DesbloqueadorPDF** | `pikepdf 10.16.0` + `pypdfium2 5.14.0` + `pdfplumber 0.11.10` | ✅ Operacional | Remoção de travas de cópia, impressão e senhas conhecidas; extração de texto forense sem perda de layout. |
| **DesbloqueadorWord** | `python-docx 1.2.0` + XML nativo + `LibreOffice` | ✅ Operacional | Remoção cirúrgica de travas de edição (`w:documentProtection`) em arquivos `.docx` e conversão headless de formatos legados. |
| **DesbloqueadorExcel** | `openpyxl 3.1.5` + XML nativo + `LibreOffice` | ✅ Operacional | Remoção instantânea de bloqueios de abas (`sheetProtection`) e pastas em arquivos `.xlsx` fiscais e contábeis. |
| **DesbloqueadorRARZIP** | `rarfile 4.5` + `py7zr 1.1.3` + `zipfile` | ✅ Operacional | Descompactação automatizada com motor oficial WinRAR Linux (`/usr/bin/unrar`) e 7-Zip (`/usr/bin/7z`). |
| **Python-Magic / Libmagic** | `0.4.27` / `libmagic1` | ✅ Operacional | Detecção de tipo real de arquivo via assinatura binária (Magic Bytes), neutralizando arquivos com extensão mascarada ou fraudada. |
| **Binários Linux C/C++** | `unrar`, `7z`, `soffice`, `file`, `pdfimages`, `tesseract` | ✅ Operacional | Todos os binários de sistema instalados em `/usr/bin` e testados quanto à execução. |

---

## 5. LOCALIZAÇÃO DOS ARQUIVOS E CÓDIGO FONTE

1. **Módulo Desbloqueador no Servidor HDW:**
   - Host: `/home/hudson/HUDSON/backend/app/services/hudson_desbloqueador.py`
   - Container: `/app/app/services/hudson_desbloqueador.py`
2. **Configuração de Dependências no Servidor HDW:**
   - Host: `/home/hudson/HUDSON/backend/requirements.txt`
   - Host: `/home/hudson/HUDSON/backend/Dockerfile`
3. **Repositório GitHub do HUDSON:**
   - Repositório: `https://github.com/Sugoi-SA/HUDSON.git`
   - Sincronizado com os mesmos arquivos de backend, dockerfile e documentação técnica em `docs/hdw/`.
4. **Repositório GitHub de Ferramentas Fuzzy-Harness:**
   - Repositório: `https://github.com/MV-AKAGUI/FERRAMENTAS--FUZZY---HARNESS-`
   - Código central em `ferramentas/hudson_desbloqueador.py`.

---

## 6. RECOMENDAÇÕES PARA A TI E PARA OS DESENVOLVEDORES (CLAUDE / DR. TAYLOR)

1. **Para a Equipe de TI da SUGOI:**
   - O ambiente do HDW está estabilizado e homologado. Nenhuma intervenção destrutiva no Docker ou no PostgreSQL é necessária.
   - Para integrar robôs como a **Dai** ou o **Kan-sa**, emitir perfis OpenVPN `.ovpn` dedicados com IPs fixos ou rotas configuradas para a sub-rede `192.168.1.0/24`.
2. **Para o Agente Claude e Dr. Taylor Code:**
   - Os pipelines de ingestão agora podem chamar diretamente `from app.services.hudson_desbloqueador import HudsonDesbloqueador` antes de enviar os arquivos para o pipeline de extração e OCR.
   - O Docling (`docling.document_converter.DocumentConverter`) e o RapidOCR (`rapidocr_onnxruntime.RapidOCR`) estão instalados e prontos para uso nativo no container `hudson-app` sem dependências externas adicionais.

---
*Relatório emitido e validado em 08/10/2026.*
