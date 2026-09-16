-- HUDSON S1 - schema hudson - PostgreSQL 15
-- Deriva do diagrama ER (diagrams/P3-schema-hudson.mmd). Base agnostica de
-- hipotese (P8 do contexto unico): novas hipoteses geram consultas com
-- filtros, nunca novas tabelas.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS hudson;
SET search_path TO hudson;

-- Estant_types - enum das 6 Estantes (roteamento deterministico do nucleo)
CREATE TABLE estant_types (
    codigo TEXT PRIMARY KEY,
    descricao TEXT NOT NULL
);
COMMENT ON TABLE estant_types IS 'Enum das 6 Estantes - roteamento deterministico do nucleo';

INSERT INTO estant_types (codigo, descricao) VALUES
    ('document_text', 'Documentos textuais'),
    ('communication', 'Comunicacoes - e-mail, chat, mensagens'),
    ('engineering_drawings', 'Pranchas e desenhos de engenharia'),
    ('structured_data', 'Dados estruturados - notas fiscais, planilhas'),
    ('image', 'Imagens'),
    ('audio_video', 'Audio e video');

-- Items - registro forense de cada binario recebido
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hash_sha256 TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL,
    estante TEXT REFERENCES estant_types (codigo),
    cota TEXT,
    obra_wbs TEXT,
    duplicate_of_item_id UUID REFERENCES items (id),
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    search_vector TSVECTOR,
    CONSTRAINT items_hash_sha256_key UNIQUE (hash_sha256),
    CONSTRAINT items_cota_key UNIQUE (cota)
);

COMMENT ON COLUMN items.hash_sha256 IS 'Hash forense - calculado em streaming na recepcao, antes de qualquer outra etapa (P1 hash primeiro)';
COMMENT ON COLUMN items.duplicate_of_item_id IS 'Auto-relacionamento - preenchido somente quando o item e duplicata exata; origem sempre preservada, nunca excluida';
COMMENT ON COLUMN items.cota IS 'Cota HUDSON - endereco unico e deterministico - ver docs/S8-cota-hudson.md';
COMMENT ON COLUMN items.status IS 'Espelha o stateDiagram de diagrams/P1-estados-item.mmd - nunca reflete um estado de exclusao';

CREATE INDEX items_search_vector_idx ON items USING GIN (search_vector);
CREATE INDEX items_estante_idx ON items (estante);
CREATE INDEX items_status_idx ON items (status);
CREATE INDEX items_duplicate_of_idx ON items (duplicate_of_item_id);
CREATE INDEX items_obra_wbs_idx ON items (obra_wbs);

-- Entities - catalogo de PF, PJ, valores, datas, clausulas, WBS identificados pela LLM (funcao NER)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}'
);

CREATE INDEX entities_canonical_name_idx ON entities (canonical_name);
CREATE INDEX entities_aliases_idx ON entities USING GIN (aliases);

-- Relationships - vinculos entre entidades, povoados pela funcao Resolucao de Entidades
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_a_id UUID NOT NULL REFERENCES entities (id),
    entity_b_id UUID NOT NULL REFERENCES entities (id),
    relation_type TEXT NOT NULL,
    source_item_id UUID NOT NULL REFERENCES items (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT relationships_no_self_loop CHECK (entity_a_id <> entity_b_id)
);

CREATE INDEX relationships_entity_a_idx ON relationships (entity_a_id);
CREATE INDEX relationships_entity_b_idx ON relationships (entity_b_id);
CREATE INDEX relationships_source_item_idx ON relationships (source_item_id);

-- Declarations - formulario declarativo humano ou metadados automaticos equivalentes
CREATE TABLE declarations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL UNIQUE REFERENCES items (id),
    origem_setor TEXT NOT NULL,
    tipo_material TEXT NOT NULL,
    vinculo_obra_wbs TEXT,
    observacao_livre TEXT,
    fonte TEXT NOT NULL CHECK (fonte IN ('formulario_humano', 'metadados_automaticos')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE declarations IS 'Etiqueta declarativa - nunca filtro; divergencia com o conteudo do binario e dado forense, nao motivo de reprovacao';

-- Custody_log - append-only, particionado por ano, retencao de 10 anos (ver S5)
CREATE TABLE custody_log (
    id BIGSERIAL,
    item_id UUID REFERENCES items (id),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'recebimento', 'retencao', 'liberacao', 'deduplicacao',
        'roteamento', 'processamento', 'falha_llm', 'reprocessamento',
        'indexacao', 'lock_custodia', 'consulta', 'alerta_integridade'
    )),
    actor TEXT NOT NULL,
    reason TEXT,
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload_hash TEXT NOT NULL,
    PRIMARY KEY (id, "timestamp")
) PARTITION BY RANGE ("timestamp");

COMMENT ON TABLE custody_log IS 'Append-only - base legal Arts. 158-A a 158-F do CPP; item_id nulo apenas em evento de consulta ampla sem item unico associado';
COMMENT ON COLUMN custody_log.reason IS 'Obrigatorio na aplicacao quando event_type = retencao';

CREATE TABLE custody_log_2025 PARTITION OF custody_log
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE custody_log_2026 PARTITION OF custody_log
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE custody_log_2027 PARTITION OF custody_log
    FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');
-- nova particao anual criada por rotina de manutencao antes do virar do ano

CREATE INDEX custody_log_item_id_idx ON custody_log (item_id);
CREATE INDEX custody_log_event_type_idx ON custody_log (event_type);

-- Protecao contra UPDATE/DELETE em custody_log - reforca a custodia append-only (P2)
CREATE OR REPLACE FUNCTION hudson.bloquear_update_delete_custody_log()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'custody_log e append-only - % nao e permitido', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER custody_log_bloqueia_update_delete
    BEFORE UPDATE OR DELETE ON custody_log
    FOR EACH ROW EXECUTE FUNCTION hudson.bloquear_update_delete_custody_log();

-- Protecao contra DELETE em items - reforca Zero Exclusao (P3); UPDATE continua liberado
-- para o pipeline avancar status, estante, processed_at etc.
CREATE OR REPLACE FUNCTION hudson.bloquear_delete_items()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Zero Exclusao (P3) - DELETE nao e permitido em items';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER items_bloqueia_delete
    BEFORE DELETE ON items
    FOR EACH ROW EXECUTE FUNCTION hudson.bloquear_delete_items();
