# HUDSON S1 — Arquitetura do Sistema

Custodiante forense e data warehouse do ecossistema (HUDSON S1, WATSON S2, HOLMES S3, MYCROFT S4). Hash SHA-256 em streaming e `custody_log` append-only garantem a cadeia de custódia de tudo que entra no acervo.

Este repositório reúne os três diagramas de arquitetura do desenho inicial do fluxo do sistema, em Mermaid.

## ⚠️ Nota técnica sobre o Bloco 1 (C4)

O suporte a `C4Context` no Mermaid é experimental e varia entre versões de renderizador. Testado neste ambiente (mermaid-cli 11.14.0): a diretiva `SHOW_LEGEND()` no fim do bloco quebra o parser com "Lexical error" — o restante do diagrama renderiza normalmente sem essa linha. O arquivo abaixo mantém `SHOW_LEGEND()` porque pode funcionar em outros renderizadores (ex.: mermaid.live com versão mais nova, ou o preview nativo do GitHub); se o C4 não renderizar no seu visualizador, remova essa linha ou use o Bloco 3 (Flowchart), validado e 100% estável.

## Diagramas

### 1. C4 Model — Contexto (Nível 1)

`01-c4-contexto.mmd`

```mermaid
C4Context
  title C4 Nivel 1 - Contexto do Sistema HUDSON S1

  Person(corporativo, "Consumidor Corporativo", "Advogado, gestor, auditor, due diligence e setores")
  Person(analista, "Analista de Quarentena", "Revisa itens retidos - nunca apaga")
  Person(gov, "Gestor de Governanca S4", "Aprova versoes do System Prompt")

  System(hudson, "HUDSON S1", "Custodiante forense e data warehouse - hash SHA-256 e custody_log append-only")
  System(watson, "WATSON S2", "Auditoria do acervo")
  System(holmes, "HOLMES S3", "Sindicancia - somente leitura")
  System(mycroft, "MYCROFT S4", "Governanca de IA - telemetria e prompt_registry")

  System_Ext(zeev, "Zeev BPMS", "Orquestra tarefas e mantem travas de ingestao")
  System_Ext(sienge, "SIENGE", "ERP - NFs, ordens e medicoes")
  System_Ext(autodoc, "AutoDoc", "Pranchas de projeto e ARTs")
  System_Ext(bancaria, "Conciliacao Bancaria", "Comprovantes e extratos")
  System_Ext(m365, "Microsoft 365", "SharePoint, Outlook e Teams")
  System_Ext(legados, "Legados", "SMB/NFS e caixas pst e msg")

  Rel(sienge, hudson, "Envia PDFs e XMLs por evento de negocio", "Webhook POST /items")
  Rel(autodoc, hudson, "Envia pranchas e ARTs", "Webhook POST /items")
  Rel(bancaria, hudson, "Envia comprovantes apos liquidacao", "Webhook POST /items")
  Rel(zeev, hudson, "Envia arquivos e formulario declarativo - espera recibo", "POST /items - HTTP 201")
  Rel(m365, hudson, "Documentos, e-mails e mensagens", "Graph API - conector unico")
  Rel(legados, hudson, "Varredura passiva agendada", "Celery Workers read-only")
  Rel(corporativo, hudson, "Consulta o acervo", "Chat Tradutor e endpoints de leitura")
  Rel(analista, hudson, "Revisa itens retidos", "Fila de revisao humana")
  Rel(holmes, hudson, "Consome o banco para sindicancia", "APIs de leitura auditada")
  Rel(watson, hudson, "Reporta falha de indexacao ou entidade omitida", "s1_audit_findings")
  Rel(hudson, mycroft, "Registra tokens e latencia de LLM", "llmops_telemetry")
  Rel(gov, mycroft, "Aprova ou bloqueia versoes de prompt", "prompt_registry")

  SHOW_LEGEND()
```

### 2. Sequência — Ingestão e Processamento

`02-sequencia-ingestao.mmd` — validado (renderiza sem erros).

```mermaid
sequenceDiagram
    autonumber
    participant Z as Zeev BPMS
    participant E as Emissores (SIENGE, AutoDoc, M365)
    participant API as API HUDSON
    participant Q as Quarentena
    participant N as Nucleo HUDSON
    participant IA as Agente IA (LLM + Harness)
    participant DB as PostgreSQL hudson
    participant VDB as ChromaDB
    participant S4 as MYCROFT S4

    E->>API: POST /items (JSON + binario)
    API->>API: Hash SHA-256 em streaming
    API->>DB: 1o registro no custody_log
    API-->>Z: HTTP 201 Created + recibo hash

    alt Chamada falhou
        API--xZ: Erro - Zeev BLOQUEIA etapa de negocio
    end

    rect rgb(240, 245, 255)
        note over Q: Ante-sala - triagem leve
        API->>Q: Item em quarentena
        Q->>Q: ClamAV + magic bytes + schema + remetente
        alt Aprovado
            Q->>N: Segue para o nucleo
        else Retido
            Q->>DB: status retido + motivo no custody_log
            note over Q: Revisao humana - nunca apagado
            Q->>N: Liberado pelo analista (se aprovado)
        end
    end

    rect rgb(243, 236, 255)
        note over N,IA: Nucleo - tratamento pelo Agente IA
        N->>N: Deduplicacao exata (is_duplicate_of)
        N->>N: Roteamento pelas 6 Estantes
        N->>N: OCR Tesseract camada dupla
        N->>IA: Texto extraido para NER
        IA->>DB: Consulta catalogo de entidades
        IA->>DB: NER - PF, PJ, valores, datas, WBS
        IA->>DB: Resolucao de entidades (criar no ou merge)
        IA->>DB: Povoamento da tabela relationships
        IA->>S4: Telemetria (tokens, latencia)
    end

    N->>DB: Indexacao tsvector
    N->>VDB: Embeddings vetoriais
    N->>DB: Lock de Custodia - status processed + log imutavel

    opt Auditoria transversal
        S4-->>IA: prompt_registry travado por versao
    end
```

### 3. Flowchart — Arquitetura Completa (alternativa estável ao C4)

`03-flowchart-completo.mmd` — validado (renderiza sem erros).

```mermaid
flowchart TD
    subgraph FONTES["Fontes - geram arquivos e informacao"]
        ZEEV["Zeev BPMS<br/>+ formulario declarativo"]
        SIENGE["SIENGE<br/>NFs e medicoes"]
        M365["SharePoint, Outlook, Teams"]
        OUTROS["AutoDoc, Conciliacao, CV, OT, legados"]
    end

    subgraph API["API REST POST /items"]
        A1{"Chamada OK?"}
    end

    subgraph HUDSON["HUDSON - Recepcao"]
        H1["Hash SHA-256 em streaming"]
        H2["1o registro no custody_log"]
        H3["Formulario declarativo<br/>etiqueta - nunca filtro"]
    end

    subgraph QUAREN["Quarentena - ante-sala"]
        Q1["ClamAV, magic bytes,<br/>schema, remetente"]
        Q2{"Aprovado?"}
        Q3["Status RETIDO<br/>revisao humana"]
        Q4{"Liberado pelo analista?"}
    end

    subgraph NUCLEO["Nucleo - Agente IA"]
        N1{"Duplicata?"}
        N2["Marca is_duplicate_of<br/>origem preservada"]
        N3["Roteamento 6 Estantes"]
        N4["OCR Tesseract"]
        N5["NER pela LLM"]
        N6["Resolucao de entidades<br/>tabela relationships"]
        N7["Indexacao tsvector + ChromaDB"]
        N8{"Processamento OK?"}
        N9["Flag de reprocessamento<br/>telemetria S4"]
    end

    subgraph LOCK["Lock de Custodia"]
        L1["status processed<br/>log imutavel"]
    end

    subgraph CONSUMO["Biblioteca Soberana"]
        C1["Chat Tradutor + endpoints<br/>search, authenticity, custody-log,<br/>timeline, communication-map"]
        C2{"Consulta auditada?"}
        C3["Registro no custody_log"]
        C4["WATSON S2 - HOLMES S3 -<br/>MYCROFT S4 - corporativos"]
    end

    ZEEV --> A1
    SIENGE --> A1
    M365 --> A1
    OUTROS --> A1

    A1 -- "NAO" --> ZBLOCK["Zeev BLOQUEIA a etapa de negocio"]
    A1 -- "SIM" --> H1
    H1 --> H2 --> H3 --> Q1 --> Q2

    Q2 -- "NAO" --> Q3 --> Q4
    Q4 -- "NAO" --> Q3
    Q4 -- "SIM" --> N1
    Q2 -- "SIM" --> N1

    N1 -- "SIM" --> N2
    N1 -- "NAO" --> N3
    N3 --> N4 --> N5 --> N6 --> N7 --> N8

    N8 -- "NAO" --> N9 --> N3
    N8 -- "SIM" --> L1 --> C1

    C1 --> C2
    C2 -- "SIM - toda consulta" --> C3 --> C4
    C2 -- "NAO - acesso negado" --> X1["RBAC bloqueia<br/>e registra tentativa"]
```

## Princípios evidenciados no desenho

- **Cadeia de custódia desde a entrada**: hash SHA-256 em streaming e primeiro registro no `custody_log` acontecem antes de qualquer outra etapa.
- **Zeev como trava de negócio**: se a chamada à API HUDSON falhar, o Zeev bloqueia a etapa de negócio — não há caminho de contorno.
- **Quarentena nunca apaga**: itens retidos ficam para revisão humana; a liberação é decisão do analista, não automática.
- **Deduplicação preserva origem**: duplicatas exatas são marcadas (`is_duplicate_of`), nunca descartadas.
- **Toda consulta é auditada**: leitura pela Biblioteca Soberana passa por RBAC e gera registro no `custody_log`, com bloqueio e registro de tentativa em caso de acesso negado.
