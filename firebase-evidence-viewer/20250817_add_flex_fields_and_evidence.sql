
-- Migration: add flexible per-type fields, field dictionary, multi-evidence links, and useful indexes
-- Generated: 20250817-131409
-- Safe, additive migration against your existing DDL

-- 1) Flexible per-type fields on documents
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS extracted_fields JSONB,
  ADD CONSTRAINT chk_documents_extracted_fields_json
    CHECK (extracted_fields IS NULL OR jsonb_typeof(extracted_fields) = 'object');

-- 2) Field dictionary for validation / UI hints
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'importance_t') THEN
        CREATE TYPE importance_t AS ENUM ('Low','Med','High');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS field_dictionary (
    doc_type              contract_type NOT NULL,
    field_key             TEXT NOT NULL,
    label                 TEXT,
    datatype              TEXT,   -- text, integer, decimal, currency, date, boolean, enum(...), party, text[]
    units                 TEXT,
    regex                 TEXT,
    required              BOOLEAN DEFAULT FALSE,
    importance            importance_t DEFAULT 'High',
    PRIMARY KEY (doc_type, field_key)
);

-- 3) Multi-evidence links with page ranges for obligations
CREATE TABLE IF NOT EXISTS obligation_evidence_links (
    evidence_link_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obligation_id         UUID NOT NULL REFERENCES obligations(obligation_id) ON DELETE CASCADE,
    evidence_document_id  UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    page_from             INT,
    page_to               INT,
    note                  TEXT
);
CREATE INDEX IF NOT EXISTS ix_obligation_evidence_obl ON obligation_evidence_links(obligation_id);
CREATE INDEX IF NOT EXISTS ix_obligation_evidence_doc ON obligation_evidence_links(evidence_document_id);

-- 4) Practical indexes
CREATE INDEX IF NOT EXISTS ix_documents_type ON documents(contract_type);
CREATE INDEX IF NOT EXISTS ix_documents_effective ON documents(effective_date);
CREATE INDEX IF NOT EXISTS ix_obligations_doc ON obligations(document_id);
CREATE INDEX IF NOT EXISTS ix_obligations_party ON obligations(party_id);
CREATE INDEX IF NOT EXISTS ix_permits_issue ON permits(issue_date);
CREATE INDEX IF NOT EXISTS ix_financial_terms_price ON financial_terms(purchase_price);

-- 5) Optional: unique constraint for recordings when present
CREATE UNIQUE INDEX IF NOT EXISTS ux_recordings_unique_instr
ON legal_recordings(county_fips, instrument_number)
WHERE county_fips IS NOT NULL AND instrument_number IS NOT NULL;

-- 6) View: time-aware "as_of_date" for simpler queries
CREATE OR REPLACE VIEW documents_as_of AS
SELECT
  d.*,
  COALESCE(lr.recording_date, d.effective_date, d.execution_date, d.created_at::date) AS as_of_date
FROM documents d
LEFT JOIN LATERAL (
  SELECT recording_date
  FROM legal_recordings lr
  WHERE lr.document_id = d.document_id
  ORDER BY recording_date DESC NULLS LAST
  LIMIT 1
) lr ON TRUE;
