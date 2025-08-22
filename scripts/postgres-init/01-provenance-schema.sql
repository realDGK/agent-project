-- Provenance Tracking Schema
-- Based on GPT-5 improvements for contract-level provenance

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Document storage with versioning and immutability
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sha256 VARCHAR(64) NOT NULL UNIQUE,
    filename VARCHAR(255) NOT NULL,
    content TEXT,
    content_type VARCHAR(100),
    file_size INTEGER,
    version INTEGER DEFAULT 1,
    parent_sha256 VARCHAR(64) REFERENCES documents(sha256),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending',
    CONSTRAINT check_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'review_required'))
);

CREATE INDEX idx_documents_sha256 ON documents(sha256);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);

-- Extraction provenance tracking
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id VARCHAR(100) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    value JSONB NOT NULL,
    doc_id UUID NOT NULL REFERENCES documents(id),
    doc_sha256 VARCHAR(64) NOT NULL,
    doc_version INTEGER NOT NULL,
    page INTEGER,
    bbox JSONB, -- [x1, y1, x2, y2]
    char_offset_start INTEGER,
    char_offset_end INTEGER,
    snippet TEXT NOT NULL,
    extractor VARCHAR(50) NOT NULL,
    extractor_version VARCHAR(20),
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    derived_from UUID[], -- Array of other extraction IDs
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    agent_id VARCHAR(100),
    metadata JSONB,
    CONSTRAINT check_extractor CHECK (extractor IN ('rule', 'model', 'human', 'computed'))
);

CREATE INDEX idx_extractions_doc_id ON extractions(doc_id);
CREATE INDEX idx_extractions_field_name ON extractions(field_name);
CREATE INDEX idx_extractions_timestamp ON extractions(timestamp DESC);
CREATE INDEX idx_extractions_confidence ON extractions(confidence);

-- Conflict tracking for amendments and superseded values
CREATE TABLE conflicts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_name VARCHAR(100) NOT NULL,
    doc_id UUID NOT NULL REFERENCES documents(id),
    chosen_extraction_id UUID REFERENCES extractions(id),
    chosen_value JSONB,
    conflict_rule_id VARCHAR(100),
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Conflict candidates (losing values)
CREATE TABLE conflict_candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conflict_id UUID NOT NULL REFERENCES conflicts(id) ON DELETE CASCADE,
    extraction_id UUID NOT NULL REFERENCES extractions(id),
    value JSONB NOT NULL,
    superseded_by UUID REFERENCES extractions(id),
    conflict_rule_applied VARCHAR(100),
    reason VARCHAR(255),
    priority INTEGER
);

CREATE INDEX idx_conflict_candidates_conflict_id ON conflict_candidates(conflict_id);

-- Table cell anchoring for financial data
CREATE TABLE table_cells (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cell_id VARCHAR(100) UNIQUE NOT NULL,
    doc_id UUID NOT NULL REFERENCES documents(id),
    doc_sha256 VARCHAR(64) NOT NULL,
    page INTEGER NOT NULL,
    table_index INTEGER,
    row_index INTEGER NOT NULL,
    col_index INTEGER NOT NULL,
    bbox JSONB NOT NULL,
    header_row TEXT[],
    header_col TEXT[],
    cell_type VARCHAR(50),
    raw_value TEXT,
    normalized_value JSONB,
    currency VARCHAR(3),
    is_percentage BOOLEAN DEFAULT FALSE,
    validation_status VARCHAR(50),
    CONSTRAINT check_cell_type CHECK (cell_type IN ('header', 'data', 'total', 'subtotal', 'label'))
);

CREATE INDEX idx_table_cells_doc_id ON table_cells(doc_id);
CREATE INDEX idx_table_cells_cell_id ON table_cells(cell_id);
CREATE INDEX idx_table_cells_location ON table_cells(page, table_index, row_index, col_index);

-- Human-in-the-Loop review queue
CREATE TABLE review_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_type VARCHAR(50) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    doc_id UUID REFERENCES documents(id),
    doc_sha256 VARCHAR(64),
    page INTEGER,
    bbox JSONB,
    field_name VARCHAR(100),
    extraction_id UUID REFERENCES extractions(id),
    priority DECIMAL(5,2) NOT NULL,
    criticality DECIMAL(3,2),
    confidence DECIMAL(3,2),
    impact DECIMAL(3,2),
    status VARCHAR(50) DEFAULT 'pending',
    assigned_to VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    resolution JSONB,
    batch_id UUID,
    auto_closed BOOLEAN DEFAULT FALSE,
    auto_close_reason TEXT,
    CONSTRAINT check_task_type CHECK (task_type IN ('transcribe', 'verify', 'resolve_conflict', 'validate_table', 'review_low_confidence')),
    CONSTRAINT check_status CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped', 'auto_closed'))
);

CREATE INDEX idx_review_tasks_status ON review_tasks(status);
CREATE INDEX idx_review_tasks_priority ON review_tasks(priority DESC);
CREATE INDEX idx_review_tasks_batch_id ON review_tasks(batch_id);
CREATE INDEX idx_review_tasks_created_at ON review_tasks(created_at);

-- Conflict resolution rules
CREATE TABLE conflict_rules (
    id VARCHAR(100) PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL,
    precedence_order INTEGER,
    conditions JSONB,
    actions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_rule_type CHECK (rule_type IN ('amendment', 'date_based', 'source_based', 'field_specific', 'custom'))
);

-- Audit log for all changes
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    old_values JSONB,
    new_values JSONB,
    metadata JSONB
);

CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_log_changed_at ON audit_log(changed_at DESC);

-- Create views for common queries
CREATE OR REPLACE VIEW latest_extractions AS
SELECT DISTINCT ON (field_name, doc_id) 
    e.*,
    d.filename,
    d.status as doc_status
FROM extractions e
JOIN documents d ON e.doc_id = d.id
ORDER BY field_name, doc_id, timestamp DESC;

CREATE OR REPLACE VIEW pending_reviews AS
SELECT 
    rt.*,
    d.filename,
    e.field_name as extraction_field,
    e.value as extraction_value,
    e.confidence as extraction_confidence
FROM review_tasks rt
LEFT JOIN documents d ON rt.doc_id = d.id
LEFT JOIN extractions e ON rt.extraction_id = e.id
WHERE rt.status = 'pending'
ORDER BY rt.priority DESC;

-- Functions for priority calculation
CREATE OR REPLACE FUNCTION calculate_review_priority(
    p_criticality DECIMAL,
    p_confidence DECIMAL,
    p_impact DECIMAL
) RETURNS DECIMAL AS $$
BEGIN
    -- Priority = criticality * (1 - confidence) * impact
    RETURN p_criticality * (1 - COALESCE(p_confidence, 0)) * COALESCE(p_impact, 1);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger for updating document status
CREATE OR REPLACE FUNCTION update_document_status() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' THEN
        NEW.processed_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_document_status
    BEFORE UPDATE ON documents
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION update_document_status();

-- Trigger for audit logging
CREATE OR REPLACE FUNCTION audit_trigger() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES (
        TG_TABLE_NAME,
        CASE 
            WHEN TG_OP = 'DELETE' THEN OLD.id
            ELSE NEW.id
        END,
        TG_OP,
        current_setting('app.current_user', true),
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to main tables
CREATE TRIGGER audit_documents AFTER INSERT OR UPDATE OR DELETE ON documents
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();

CREATE TRIGGER audit_extractions AFTER INSERT OR UPDATE OR DELETE ON extractions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();

CREATE TRIGGER audit_conflicts AFTER INSERT OR UPDATE OR DELETE ON conflicts
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();