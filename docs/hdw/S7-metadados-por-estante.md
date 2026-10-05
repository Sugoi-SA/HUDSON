# S7 — Metadados por Estante (o "MARC do HUDSON")

Referência de catalogação análoga ao MARC da Library of Congress: cada Estante
(`estant_types` em [specs/S2-schema.sql](../specs/S2-schema.sql)) define campos
específicos além dos campos comuns de `items` (`hash_sha256`, `cota`, `estante`,
`obra_wbs`, `received_at`, `processed_at`). "Indexável" indica se o campo entra no
`tsvector` do PostgreSQL, nos embeddings do ChromaDB, em ambos, ou em nenhum
(campo apenas estrutural/forense).

## document_text — documentos textuais (contratos, memorandos, laudos, atas)

| Campo | Descrição | Indexável |
|---|---|---|
| tipo_documento | contrato, memorando, laudo, ata | tsvector |
| titulo_documento | título extraído ou declarado | tsvector |
| numero_paginas | contagem de páginas do OCR | não |
| texto_ocr | texto completo da camada dupla do Tesseract | tsvector + ChromaDB |
| clausulas_identificadas | referência às `entities` do tipo clausula | via `relationships` |
| assinantes | referência às `entities` do tipo PF/PJ | via `relationships` |

## communication — e-mail, chat, mensagens (Outlook, Teams, SharePoint, legado)

| Campo | Descrição | Indexável |
|---|---|---|
| remetente | referência à `entity` do tipo PF | via `relationships` |
| destinatarios | lista de referências a `entities` do tipo PF | via `relationships` |
| assunto | assunto da mensagem | tsvector |
| corpo_mensagem | corpo integral da mensagem | tsvector + ChromaDB |
| data_envio | timestamp original da mensagem | não |
| thread_id | identificador de conversa, quando disponível | não |
| anexos | lista de `item_id` de itens filhos vinculados | não |

## engineering_drawings — pranchas e desenhos de engenharia

| Campo | Descrição | Indexável |
|---|---|---|
| numero_prancha | identificador da prancha | tsvector |
| disciplina | estrutural, hidráulico, elétrico, arquitetônico | tsvector |
| revisao | código de revisão da prancha | não |
| art_crea | ART/CREA do responsável técnico | via `relationships` (entity PF/PJ) |
| escala | escala do desenho | não |
| legenda_ocr | texto da legenda extraído por OCR | tsvector |

## structured_data — dados estruturados (notas fiscais, ordens, medições, planilhas)

| Campo | Descrição | Indexável |
|---|---|---|
| numero_documento | número da NF, OC ou medição | tsvector |
| cnpj_emissor | referência à `entity` do tipo PJ_CNPJ | via `relationships` |
| cnpj_destinatario | referência à `entity` do tipo PJ_CNPJ | via `relationships` |
| valor_total | valor monetário total do documento | não (consulta por faixa, não por texto) |
| data_emissao | data de emissão do documento | não |
| itens_planilha | conteúdo tabular estruturado, quando aplicável | não |

## image — imagens (fotos de obra, plantas escaneadas sem OCR viável)

| Campo | Descrição | Indexável |
|---|---|---|
| descricao_legenda | legenda declarada ou extraída | tsvector |
| data_captura | data/hora da captura, quando disponível em EXIF | não |
| geolocalizacao | coordenadas EXIF, quando disponíveis | não |
| formato_imagem | JPEG, PNG, TIFF etc. | não |

## audio_video — áudio e vídeo (reuniões gravadas, ligações)

| Campo | Descrição | Indexável |
|---|---|---|
| duracao_segundos | duração da mídia | não |
| transcricao_texto | transcrição via reconhecimento de fala | tsvector + ChromaDB |
| participantes | referência a `entities` do tipo PF identificadas na transcrição | via `relationships` |
| data_gravacao | data/hora da gravação | não |
