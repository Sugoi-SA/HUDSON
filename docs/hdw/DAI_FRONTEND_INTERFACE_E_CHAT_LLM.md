# ESPECIFICAÇÃO DE INTERFACE & EXPERIÊNCIA DO USUÁRIO: DAI FRONT-END
## PORTAL WEB CORPORATIVO, NAVEGAÇÃO POR WBS E CHAT CONVERSACIONAL COM LLM OPEN SOURCE (OCI)

**Organização:** SUGOI S.A. & Daisugi Tecnologias  
**Sistema:** DAI — Smart Reception Framework & Portal Corporativo  
**Módulo:** Front-end SPA (Single Page Application)  
**Coordenação:** PMO de Processos, TI, Programação & Infraestrutura  
**Liderança Técnica:** Especialista em Front-end (React/TypeScript) & Designer de Produto  
**Tecnologias:** React 18, TypeScript, Material-UI (MUI v5), vLLM / Ollama (API LLM Open Source)  
**Data de Emissão:** 09 de Outubro de 2026  
**Status do Documento:** 🟢 **HOMOLOGADO PARA DESENVOLVIMENTO (SPRINT FASE 1.1)**  

---

## 🎯 1. VISÃO GERAL E PROPÓSITO DO PRODUTO

A **DAI (Smart Reception Framework & Portal Corporativo)** é a porta de entrada visual unificada para todos os operadores humanos da SUGOI S.A. (engenheiros de obra, gestores de contratos, fiscais de campo, advogados, peritos, auditores e diretoria executiva).

Historicamente, o **HUDSON DW (HDW)** operava como um cofre cego em linha de comando (CLI) acessível apenas por scripts. O objetivo desta especificação é dotar a organização de um portal moderno, responsivo, seguro e intuitivo, combinando:
1. **Navegação Estruturada:** Exploração visual da árvore de empreendimentos via código WBS (`obra_wbs`) e classificação em 6 estantes temáticas;
2. **Chat Inteligente Soberano:** Assistente conversacional impulsionado por uma **LLM de Código Aberto (100% Free - Llama 3.1 / Qwen 2.5 / DeepSeek)** hospedada em instância privada na **Oracle Cloud Infrastructure (OCI)**;
3. **Comprovação Forense em 1 Clique:** Emissão e visualização de certidões periciais de autenticidade criptográfica (SHA-256) atreladas à Cota HUDSON determinística.

---

## 🏗️ 2. ARQUITETURA DE FRONT-END & STACK TECNOLÓGICA

```
                            ARQUITETURA DA SPA (DAI FRONT-END)
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                        CAMADA DE APRESENTAÇÃO (UI/UX)                       │
   │  • React 18 (TypeScript) + Material-UI (MUI v5) + Emotion CSS              │
   │  • Layout Responsivo: Modo Escuro / Claro (Tema Corporativo SUGOI)          │
   │  • Ícones e Tipografia: Inter / Roboto + Lucide React                       │
   └──────────────────────────────────────┬──────────────────────────────────────┘
                                          │
         ┌────────────────────────────────┴────────────────────────────────┐
         ▼                                                                 ▼
   ┌───────────────────────────┐                     ┌───────────────────────────┐
   │     MÓDULO DE TELAS       │                     │    MÓDULO DE CHAT IA      │
   │ • Árvore WBS Interativa   │                     │ • Chatbot Conversacional  │
   │ • Visualizador Multiestant│                     │ • Conexão vLLM / Ollama   │
   │ • Tabela MUI DataGrid     │                     │ • Render Markdown + Cota  │
   │ • Certidão SHA-256        │                     │ • Guardrail Feedback      │
   └─────────────┬─────────────┘                     └─────────────┬─────────────┘
                 │                                                 │
                 └────────────────────────┬────────────────────────┘
                                          │
                                          ▼
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                   CAMADA DE ESTADO & COMUNICAÇÃO DE REDE                    │
   │  • TanStack Query (React Query v5): Cache de requisições e auto-refetch    │
   │  • Zustand: Gerenciamento de estado global (Usuário, Obra Ativa, Tema)     │
   │  • Axios Interceptor: Injeção de Bearer Token JWT e renovação de sessão     │
   └─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1. Dependências e Bibliotecas Homologadas
* **Core:** `react: ^18.3.0`, `react-dom: ^18.3.0`, `typescript: ^5.4.0`
* **Interface Visual:** `@mui/material: ^5.15.0`, `@mui/icons-material: ^5.15.0`, `@mui/x-data-grid: ^6.19.0`
* **Estado e Requisições:** `zustand: ^4.5.0`, `@tanstack/react-query: ^5.28.0`, `axios: ^1.6.8`
* **Visualizadores de Arquivos:** `react-pdf: ^7.7.0`, `papaparse: ^5.4.1`, `lucide-react: ^0.359.0`
* **Markdown do Chat:** `react-markdown: ^9.0.0`, `remark-gfm: ^4.0.0`

---

## 🖥️ 3. TELAS DO SISTEMA E COMPONENTES VISUAIS

### 3.1. Tela 1: Dashboard de Obras e Árvore WBS (`/obras`)
* **Propósito:** Permitir que o engenheiro selecione seu empreendimento e navegue visualmente pela Estrutura Analítica do Projeto (WBS).
* **Componentes:**
  * **Seletor de Empreendimento:** Dropdown com busca rápida de obras (ex: `OBRA-FLORES-2026 - Residencial Flores de Maio`).
  * **Árvore WBS Hierárquica (`MUI SimpleTreeView`):**
    ```text
    📁 OBRA-FLORES-2026
       ├── 📁 01. FUNDAÇÕES & ESTRUTURA
       │      ├── 📄 Laudos de Sondagem (SPT)
       │      └── 📄 Ensaios de Concreto FCK / Slump (32 itens)
       ├── 📁 02. ALVENARIA & VEDAÇÕES
       │      ├── 📄 FVS - Fichas de Verificação de Serviço
       │      └── 📄 Contrato Empreiteira Alvenaria V02.pdf
       └── 📁 03. INSTALAÇÕES ELÉTRICAS E HIDRÁULICAS
    ```
  * **Indicador de Saúde de Custódia:** Gráfico visual mostrando quantos documentos daquela obra já possuem Cota HUDSON e estão imutáveis no HDW.

---

### 3.2. Tela 2: Visualizador Multiestantes de Documentos (`/documentos/{cota}`)
* **Propósito:** Abrir qualquer arquivo custodiado sem necessidade de download para o computador pessoal do usuário.
* **Componentes por Estante:**
  * `document_text`: Visualizador PDF embutido com paginação, zoom e busca de palavras com marca-texto amarelo sobre o texto extraído por OCR.
  * `engineering_drawings`: Pré-visualizador de plantas técnicas (`.dwg`, `.dxf`, `.rvt`, `.ifc`) via canvas WebGL ou conversão em imagem vetorial SVG em alta resolução.
  * `structured_data`: Grid de dados dinâmico (`MUI DataGrid`) com ordenação, filtros por coluna e paginação virtual (*virtual scrolling*) para planilhas de medição com até 50.000 linhas.
  * `communication`: Leitor de e-mails corporativos (`.eml`, `.msg`), exibindo remetente, destinatário, assunto, corpo em HTML e anexos.

---

### 3.3. Tela 3: Painel de Prova Pericial e Certidão Forense (`/certidao/{cota}`)
* **Propósito:** Oferecer a qualquer advogado ou engenheiro a emissão instantânea da **Certidão de Autenticidade Probatória**.
* **Comportamento Visual:**
  * Um card com bordas douradas e selo de autenticidade contendo:
    * **Cota Determinística:** `document_text-OBRA-FLORES-2026-2026-464468e2`
    * **Hash SHA-256 do Arquivo:** `464468e27158f894987e82c35dcdda08fe0b3fb647cb9ab8d4ccceebc6067a59`
    * **Data e Hora UTC do Recebimento Original:** `2026-10-08 22:01:13 UTC`
    * **Operador da Ronda / Máquina de Origem:** `operador_ronda_01 / srv-harness-win11`
    * **Botão de Ação "Verificar Integridade em Tempo Real":** Dispara a rota `/authenticity` no HDW. O sistema recalcula o hash físico do arquivo no disco Linux e exibe:  
      🟢 **"HASH 100% ÍNTEGRO: O binário no disco confere perfeitamente com a cadeia de custódia."**
    * **Botão "Exportar Certidão em PDF Assinada":** Gera documento oficial formatado para juntada em processos judiciais ou apresentação à Caixa Econômica Federal.

---

## 🤖 4. MÓDULO CONVERSACIONAL: CHAT COM LLM OPEN SOURCE NA NUVEM OCI

```
                          INTEGRAÇÃO DO CHAT CONVERSACIONAL
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                          DAI FRONT-END (CHAT UI)                            │
   │  "DAI, localize o laudo de FCK da laje da Torre B da Obra Flores."          │
   └──────────────────────────────────────┬──────────────────────────────────────┘
                                          │ POST /v1/chat/completions (OpenAI Compatible)
                                          ▼
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                LLM OPEN SOURCE PRIVADA (ORACLE CLOUD OCI)                   │
   │  • Servidor vLLM / Ollama em Instância Dedicada (Porta :8080)               │
   │  • Modelo Free: Llama 3.1 8B Instruct / Qwen 2.5 7B Coder                   │
   │  • Custo Recorrente de Tokens: R$ 0,00 (Software Livre)                     │
   └──────────────────────────────────────┬──────────────────────────────────────┘
                                          │ Tool Calling: get_hudson_document(obra, termo)
                                          ▼
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                           HUDSON DC GATEWAY (:9000)                         │
   │  Valida alçadas de acesso (RBAC), consulta Cache e despacha via OpenVPN     │
   └─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1. Configuração do Endpoint da LLM
A DAI conecta-se à API da LLM rodando na nuvem privada OCI através do padrão de mercado compatível com OpenAI:
* **Base URL da LLM:** `https://llm.daisugi.com.br/v1` (ou interno `http://10.0.1.50:8080/v1`)
* **Modelo Padrão:** `meta-llama/Llama-3.1-8B-Instruct-Q4_K_M`
* **Temperatura:** `0.1` (Precisão factual determinística, eliminando alucinações)
* **System Prompt Especialista:**
  ```text
  Você é a DAI, assistente de inteligência e custódia documental da SUGOI S.A.
  Seu objetivo é auxiliar engenheiros, advogados e auditores a encontrar registros no HUDSON DW.
  Ao citar qualquer documento, forneça sempre:
  1. A síntese objetiva dos dados técnicos;
  2. A COTA HUDSON exata encontrada;
  3. O link de verificação de autenticidade probatória.
  Nunca invente dados que não constem nos metadados retornados pelo sistema.
  ```

### 4.2. Renderização da Resposta no Chat
Quando a LLM localiza um documento, a interface renderiza um card interativo com destaque:

```markdown
Localizei o relatório de ensaio técnico para a laje solicitada!

* **Tipo:** Ensaio de Rompimento de Corpos de Prova (FCK aos 28 dias)
* **Resultado:** Resistência média de 32,4 MPa (Conforme norma NBR 5739)
* **Data da Concretagem:** 15/09/2026
* **Cota HUDSON:** `document_text-OBRA-FLORES-2026-464468e2`

[📄 Visualizar Documento Completo]    [🔍 Verificar Certidão SHA-256]
```

---

## 🔒 5. AUTENTICAÇÃO, CONTROLE RBAC E LGPD NA INTERFACE

1. **Autenticação Segura via JWT / OAuth2:**
   * O usuário faz login no portal da DAI e recebe um token de sessão seguro com expiração de 8 horas.
   * A chave mestra do HDW (`X-API-Key`) **NUNCA** chega ao navegador do usuário; ela permanece isolada no backend do HDC.
2. **Controle de Visualização por Perfil (RBAC):**
   * *Engenheiro de Campo:* Visualiza apenas as obras às quais está formalmente alocado no WBS.
   * *Auditor da Caixa / PBQP-H:* Acesso somente-leitura restrito às estantes de qualidade e medições.
   * *Advogado / Jurídico:* Acesso total às estantes contratuais e societárias com emissão de certidão forense.
3. **Tratamento de Acesso Negado e Feedback Amigável:**
   * Se um operador tentar clicar em uma obra ou contrato fora de sua permissão, a tela não quebra nem emite erro técnico. Ela exibe uma notificação suave de governança:
     > ℹ️ *"Seu perfil não possui alçada para visualizar documentos societários deste empreendimento. Solicite autorização formal ao administrador da biblioteca no PMO."*

---

## 🚀 6. PLANO DE ENTREGAS & ROADMAP DO FRONT-END (SPRINT FASE 1.1)

| Etapa | Escopo de Desenvolvimento | Entregáveis Técnicos |
| :--- | :--- | :--- |
| **Semana 1** | Estruturação da SPA e Design System | Configuração do Vite + React + MUI com tema SUGOI, autenticação OIDC e layout base. |
| **Semana 2** | Árvore WBS e Integração com HDC | Tela de navegação por obras, seleção de estantes e tabelas dinâmicas de medição. |
| **Semana 3** | Visualizador de Documentos & Certidão | Componente de PDF/Imagens com streaming seguro e tela de certidão forense SHA-256. |
| **Semana 4** | Chat com LLM Open Source (OCI) | Integração do chat na porta `:8080`, formatação de Cotas HUDSON e homologação final. |
