# Sugestão de Interface Web Visual Corporativa para Operadores Humanos
## Ecossistema HUDSON Data Warehouse (HDW) — SUGOI S.A.

---

## 📄 Sumário Executivo

Este documento apresenta a proposta arquitetural e funcional detalhada para a construção da **Interface Web Visual Corporativa** do **HUDSON Data Warehouse (HDW)**, voltada para operadores humanos (engenheiros, auditores, advogados, gestores e equipes operacionais da SUGOI S.A.).

O **HDW** atua como a **Biblioteca Soberana e Cofre Digital Forense Local** da empresa. Por lidar com ativos críticos e probatórios — como contratos, plantas de engenharia (WBS), e-mails corporativos, laudos de ensaio de concreto (FCK/slump), FVS (Fichas de Verificação de Serviço) e auditorias fiscais —, a interface visual não pode ser um simples painel de BI comercial. Ela deve combinar alta usabilidade com rigor pericial, **controle de acesso granular (RBAC)**, **conformidade com a LGPD** e uma **LLM local com Harness de Segurança (Guardrails)** para buscas em linguagem natural.

---

## 🏛️ 1. Diagnóstico das Premissas e Restrições Técnicas do HDW Core (:8000)

A análise da documentação oficial de comandos e limites do HDW (`HUDSON-DW-guia-comandos.pdf` e `IDENTIDADE_HDW.md`) estabelece restrições fundamentais que impedem a conexão direta de um navegador web à API nativa do HDW:

1. **Ausência de Autenticação Individual na API Nativa (`:8000`)**: A API FastAPI do HDW é protegida por uma única chave mestre (`X-API-Key`) por serviço/agente. Ela não possui tabela de usuários humanos, logins ou gerenciamento de sessões JWT/OAuth2. Expor essa chave no código JavaScript do cliente exporia todo o cofre corporativo.
2. **Caminhos de Arquivo Locais sem Stream HTTP**: Os endpoints do HDW retornam o atributo `storage_path`, que corresponde ao caminho físico absoluto do arquivo no servidor Linux (ex: `/var/hudson/storage/document_text/...`). Não existe rota pública de download ou streaming direto para exibição no navegador.
3. **Foco em Ingestão via CLI e Agentes**: A API não expõe rotas públicas de upload para usuários finais. A ingestão é realizada via scripts em linha de comando (`import_cli_v2.py`) ou por esteiras automáticas registradas por lote (`ronda_id`).
4. **Isolamento e Imutabilidade**: A camada de banco PostgreSQL 18.6 (schema `hudson`) possui *triggers* estritos que proíbem `UPDATE` e `DELETE` no log de custódia (`custody_log`) e `DELETE` na tabela de itens.

---

## 🏗️ 2. Arquitetura em Três Camadas com BFF (Backend-For-Frontend)

Para superar essas restrições e garantir segurança, auditabilidade e performance, a solução adota uma **Arquitetura em Três Camadas (3-Tier Architecture)** ancorada em um padrão **BFF (Backend-For-Frontend)**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAMADA 1: FRONTEND REACT (CLIENTE)                       │
│  - Single Page Application (SPA) em React (TypeScript) + Material-UI (MUI) │
│  - Intérprete Genérico (Server-Driven UI / Declarative Report Definitions)  │
│  - Componentes de Chat, Visualizadores de Estantes e Certidão SHA-256       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS / REST + WebSockets (JWT)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CAMADA 2: INTERMEDIÁRIA (BFF & HARNESS)                 │
│  - Autenticação de Usuários (OAuth2 / OIDC / JWT) + Matriz RBAC / LGPD       │
│  - Proxy de Mídia: Converte storage_path em Stream HTTP Seguro               │
│  - Guardrails & Harness da LLM Local (Filtragem Pre-Retrieval)               │
│  - Gerenciador de Lockout no Redis (Regra das 3 Tentativas)                  │
│  - Agregação de APIs e Injeção Segura da X-API-Key para o HDW Core          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ OpenVPN / mTLS + X-API-Key
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CAMADA 3: HUDSON DW CORE (:8000)                       │
│  - FastAPI REST Server + PostgreSQL 18.6 (Schema hudson - Imutável)         │
│  - Busca Híbrida: tsvector (Full-Text) + RapidFuzz + ChromaDB (Embeddings)   │
│  - Armazenamento Físico Append-Only com Zero Exclusão de Binários           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 3. Módulo Conversacional: LLM Local com Harness de Segurança (Guardrails)

A interface web conta com um assistente conversacional inteligente que permite consultar o acervo por linguagem natural. A segurança e a soberania dos dados são mantidas através de uma **LLM Local (On-Premise)** e um **Harness de Segurança (Guardrail)** implementado na camada BFF.

### 3.1. Arquitetura do Chat e Busca Híbrida
1. O usuário autenticado envia uma mensagem no chat (ex: *"Localize o relatório de ensaio de rompimento de concreto da laje da Obra Residencial Sol"*).
2. O **Harness de Segurança** intercepta a requisição **antes** de enviar qualquer comando ao banco ou à LLM.

### 3.2. O Harness de Segurança e Filtragem *Pre-Retrieval*
* **Validação de Alçadas (RBAC)**: O Harness cruza a identidade do usuário (extraída do JWT) com a matriz de acessos às obras (`obra_wbs`) e estantes (`document_text`, `structured_data`, `communication`, etc.).
* **Injeção de Restrições**: Se o usuário for um Engenheiro de Campo autorizado apenas na `OBRA_SOL`, o Harness injeta automaticamente o filtro estrito: `WHERE obra_wbs = 'OBRA_SOL' AND nivel_permissao <= 'ENGENHARIA'`.
* **Detecção de Intenção Negada**: Caso o usuário solicite dados de um contrato confidencial ou obra fora de sua alçada, o Harness interrompe a execução e retorna:
  > *"Seu usuário não está habilitado para esta consulta na estante solicitada. Procure o administrador da biblioteca do HDW para solicitar acesso."*

### 3.3. Regra dos 3 Bloqueios (Account Lockout) e Trilha de Custódia
* **Contador Atômico no Redis**: O BFF registra cada tentativa não autorizada em uma chave temporária com janela de 24 horas (`failed_access:user_id`).
* **Regra do Bloqueio Automático**: Na **3ª tentativa consecutiva** não autorizada:
  1. O usuário é suspenso imediatamente no repositório de identidades (`status = 'SUSPENDED_SECURITY'`).
  2. Um alerta de prioridade alta é gerado para o time de Segurança e Compliance.
  3. A resposta do chat passa a ser: *"Sua conta foi temporariamente bloqueada devido a 3 tentativas de acesso a acervos restritos. Entre em contato com a equipe de Segurança da Informação."*
* **Registro Imutável em Banco**: Toda tentativa de acesso negado é gravada no `custody_log` do PostgreSQL como um evento de violação com IP, timestamp, máquina de origem e o prompt utilizado, protegido pelas *triggers* imutáveis *append-only*.

### 3.4. Motor da LLM Local (Soberania Absoluta)
* A LLM (ex: Llama 3 / Qwen / DeepSeek) roda **100% On-Premise / OCI Privado** via Ollama ou vLLM, sem qualquer envio de dados para APIs externas.
* A resposta no chat apresenta a síntese do documento e fornece a **Cota HUDSON** determinística com link direto para a emissão da certidão de autenticidade:
  > *"O ensaio de rompimento do corpo de prova de concreto (FCK 30 MPa) para a laje da Obra Residencial Sol atendeu à norma ABNT NBR 5739 com resistência média de 32,4 MPa.*
  >
  > 📄 **Documento de Origem**: `document_text-OBRA_SOL-2026-8f3a9b12`  
  > 🔍 [Clique aqui para verificar a certidão de autenticidade SHA-256 no HDW]"

---

## 💻 4. Modelos de Interface Recomendados

Para cobrir todas as frentes operacionais, estratégicas e de conformidade da SUGOI S.A., recomenda-se a combinação de **três modelos de interface**:

### 🏆 MODELO 1 (Principal): Portal Web React (MUI) + BFF + Chat LLM Local
* **Público**: Engenheiros de Obra, Gestores de Qualidade, Advogados, Auditores e Diretoria.
* **Função**: Operação diária, pesquisas no cofre, busca por Cota HUDSON, navegação na árvore de WBS das obras e chat com LLM.
* **Destaques Visuais**:
  * **Painel da Cota & Certidão Forense (`/authenticity`)**: Tela onde o operador consulta qualquer arquivo por cota ou executa o re-cálculo do hash SHA-256 sob demanda, gerando certidão pericial com validade jurídica.
  * **Visualizador Multiestantes**: Leitor integrado de plantas CAD/BIM (`.dwg`, `.ifc`), PDFs/imagens com OCR e e-mails corporativos (`.eml`, `.msg`).
  * **Virtual Scrolling**: Tabelas de alta performance (*MUI Data Grid*) para navegação em medições e planilhas com milhares de linhas.

### 📄 MODELO 2 (Complementar): Evidence.dev (Analytics as Code)
* **Público**: Auditores de Qualidade (ISO 9001 / PBQP-H / QSMS) e Relações com Financiadores (Caixa Econômica Federal).
* **Função**: Emissão de Dossiês e Relatórios Executivos de Fechamento de Obra.
* **Destaques**: Os relatórios são definidos em arquivos Markdown + SQL salvos e versionados no repositório GitHub (`Sugoi-SA/HUDSON`). Nenhuma métrica ou gráfico pode ser alterado manualmente em tela, garantindo auditabilidade do próprio relatório.

### 🏛️ MODELO 3 (Complementar): PortalJS + OpenMetadata
* **Público**: Equipes de TI, Governança de Dados e Compliance.
* **Função**: Catálogo de dados e visualização de linhagem corporativa.
* **Destaques**: Interface amigável para navegar pelo dicionário de termos da construção civil, rastrear o histórico de rodadas de ingestão (`ronda_id`) e verificar usuários de captura sem necessidade de comandos SQL.

---

## 📋 5. Quadro Comparativo das Opções de Interface

| Requisito / Funcionalidade | Conexão Direta (Inviável) | Modelo 1: Portal React + BFF + Chat LLM (Recomendado) | Modelo 2: Evidence.dev (Auditoria) |
| :--- | :--- | :--- | :--- |
| **Segurança e Autenticação** | ❌ Ruim (API Key exposta no browser) | ✅ Total (OAuth2/JWT + RBAC + Audit Log) | ✅ Alta (Páginas estáticas / SSR) |
| **Download / View de Arquivos**| ❌ Impossível (`storage_path` é local) | ✅ Sim (BFF realiza o Proxy em Stream) | ➖ Não aplicável |
| **Navegação por WBS de Obra** | ⚠️ Limitada | ✅ Árvore interativa por empreendimento | 📊 Agregada em indicadores |
| **Busca Conversacional com LLM**| ❌ Não suportada | ✅ Suportada com Harness e Guardrails | ❌ Não suportada |
| **Proteção contra Acessos Negados**| ❌ Nenhuma | ✅ Bloqueio na 3ª tentativa (Redis) | ➖ Não aplicável |
| **Prova Pericial SHA-256** | ⚠️ Requer chamadas cegas de API | ✅ Botão nativo para certidão `/authenticity` | 📄 Citação documental |

---

## 🚀 6. Conclusão e Plano de Implementação

A criação da interface web corporativa para o **HUDSON DW** viabiliza o uso humano seguro do acervo documental e probatório da SUGOI S.A.. 

Ao adotar o **Portal Web React + BFF (Modelo 1)** equipado com o **Harness de Segurança e LLM Local**, a empresa garante:
1. **Zero Vazamento de Dados**: Processamento 100% *on-premise* sem dependência de nuvens de IA de terceiros.
2. **Mitigação de Passivos em Obras**: Acesso instantâneo a FVS, laudos de FCK de concreto e projetos executivos atrelados à WBS, cumprindo requisitos da **ISO 9001, PBQP-H, QSMS e Caixa Econômica Federal**.
3. **Proteção Contra Invasões e Abusos**: Bloqueio automático de usuários após 3 tentativas de acesso a pastas não autorizadas, com registro imutável para auditoria.

---
*Documento preparado como proposta técnica de arquitetura de software e governança para o ecossistema HUDSON DW.*
