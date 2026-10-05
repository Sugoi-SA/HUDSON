-- ==============================================================================
-- 🌐 HUDSON DC (HDC) — Esquema de Banco de Dados Relacional Multi-Tenant
-- Ambiente: Oracle Cloud Infrastructure (OCI) / PostgreSQL 16
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Tabela de Tenants do Ecossistema Daisugi
CREATE TABLE IF NOT EXISTS hdc_tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    webhook_callback_url VARCHAR(512) NOT NULL,
    hmac_secret_hash VARCHAR(128) NOT NULL,
    quota_requisicoes_minuto INT NOT NULL DEFAULT 600,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Carga inicial de Tenants homologados
INSERT INTO hdc_tenants (tenant_id, nome, ativo, webhook_callback_url, hmac_secret_hash, quota_requisicoes_minuto)
VALUES 
('sugoi_sa', 'SUGOI S.A. Construtora e Incorporadora', true, 'http://dai:8001/api/webhooks/hudson-callback', crypt('daisugi_hudson_secret_sha256_shared_key', gen_salt('bf')), 1200),
('daisugi_alpha', 'Daisugi Tecnologias Alpha Core', true, 'http://dai:8001/api/webhooks/hudson-callback', crypt('daisugi_hudson_secret_sha256_shared_key', gen_salt('bf')), 2400)
ON CONFLICT (tenant_id) DO NOTHING;

-- 2. Tabela de Ingestão de Eventos (Event Sourcing & Tracking)
CREATE TABLE IF NOT EXISTS hdc_eventos_ingestao (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(64) NOT NULL REFERENCES hdc_tenants(tenant_id),
    ticket_id VARCHAR(128) NOT NULL,
    tipo_evento VARCHAR(64) NOT NULL,
    payload_hash_sha256 CHAR(64) NOT NULL,
    status_processamento VARCHAR(32) NOT NULL DEFAULT 'RECEBIDO', -- RECEBIDO, EM_FILA, PROCESSADO, ERRO
    latencia_ms NUMERIC(10,2),
    ip_origem VARCHAR(45),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tenant_ticket UNIQUE (tenant_id, ticket_id)
);

CREATE INDEX IF NOT EXISTS idx_eventos_tenant_ticket ON hdc_eventos_ingestao(tenant_id, ticket_id);
CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON hdc_eventos_ingestao(tipo_evento, criado_em);

-- 3. Tabela de Auditoria de Segregação de Funções (SoD & Quarentena)
CREATE TABLE IF NOT EXISTS hdc_auditoria_sod (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID REFERENCES hdc_eventos_ingestao(id),
    documento_hash CHAR(64) NOT NULL,
    tipo_documento VARCHAR(64) NOT NULL,
    maker VARCHAR(255) NOT NULL,
    checker VARCHAR(255) NOT NULL,
    sod_aprovado BOOLEAN NOT NULL,
    motivo_bloqueio TEXT,
    valor_declarado NUMERIC(15,2),
    data_validacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabela de Alertas de Emergência (Dr. SaulLM & Governança Jurídica)
CREATE TABLE IF NOT EXISTS hdc_alertas_emergencia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id VARCHAR(128) NOT NULL,
    prioridade VARCHAR(16) NOT NULL, -- P1_CRITICO, P2_ALTO, P3_MEDIO
    descricao TEXT NOT NULL,
    localizacao VARCHAR(255) NOT NULL,
    orientacao_juridica TEXT,
    canais_notificados JSONB NOT NULL,
    status_resolucao VARCHAR(32) DEFAULT 'ABERTO',
    acionado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabela de Federação HDC ➔ HDW (Pontes de Custódia)
CREATE TABLE IF NOT EXISTS hdc_federacao_hdw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(64) NOT NULL,
    ticket_id VARCHAR(128) NOT NULL,
    hash_sha256 CHAR(64) NOT NULL,
    cota_hudson VARCHAR(64),
    status_custodia VARCHAR(32) NOT NULL,
    resposta_hdw JSONB,
    sincronizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
