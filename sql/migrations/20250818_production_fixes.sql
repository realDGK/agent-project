-- Production fixes for idempotency, race conditions, and data integrity
-- Based on GPT-5 recommendations

-- 0) Pre-reqs
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

-- 1) Evidence de-dupe: drop 'note' from uniqueness; add invariants + FKs
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE schemaname = 'public'
      AND indexname = 'ux_evidence_dedupe_idx'
  ) THEN
    EXECUTE 'DROP INDEX ux_evidence_dedupe_idx';
  END IF;
END$$;

-- Add proper constraints and foreign keys
ALTER TABLE obligation_evidence_links
  DROP CONSTRAINT IF EXISTS obligation_evidence_links_obligation_fk,
  DROP CONSTRAINT IF EXISTS obligation_evidence_links_document_fk,
  DROP CONSTRAINT IF EXISTS obligation_evidence_links_pages_ck;

ALTER TABLE obligation_evidence_links
  ADD CONSTRAINT obligation_evidence_links_obligation_fk
    FOREIGN KEY (obligation_id) REFERENCES obligations(obligation_id)
    ON DELETE CASCADE,
  ADD CONSTRAINT obligation_evidence_links_document_fk
    FOREIGN KEY (evidence_document_id) REFERENCES documents(document_id),
  ADD CONSTRAINT obligation_evidence_links_pages_ck
    CHECK (page_from IS NULL OR (page_from >= 1 AND (page_to IS NULL OR page_to >= page_from)));

-- New unique key without 'note'
CREATE UNIQUE INDEX IF NOT EXISTS ux_evidence_dedupe_idx
ON obligation_evidence_links (obligation_id, evidence_document_id, page_from, page_to);

CREATE INDEX IF NOT EXISTS ix_evidence_obligation_id
ON obligation_evidence_links (obligation_id);

-- 2) Obligations: normalized uniqueness via generated hash (robust & fast)
ALTER TABLE obligations
  ADD COLUMN IF NOT EXISTS obligation_hash text
  GENERATED ALWAYS AS (
    md5(
      coalesce(lower(obligation_type),'')        || '|' ||
      coalesce(lower(trigger_event),'')          || '|' ||
      coalesce(to_char(coalesce(due_date,'0001-01-01'::date),'YYYY-MM-DD'),'') || '|' ||
      coalesce(regexp_replace(lower(party_name), '\s+', ' ', 'g'),'') || '|' ||
      coalesce(regexp_replace(lower(description), '\s+', ' ', 'g'),'')
    )
  ) STORED;

-- Drop old natural key index and create new hash-based one
DROP INDEX IF EXISTS ux_obligations_natural_key;
CREATE UNIQUE INDEX IF NOT EXISTS ux_obligations_natural_hash
ON obligations (document_id, obligation_hash);

-- Optional: fast filtering
CREATE INDEX IF NOT EXISTS ix_obligations_status_due
ON obligations (status, due_date);

-- 3) JSONB indexes: ops + path_ops
DROP INDEX IF EXISTS ix_documents_extracted_fields;
CREATE INDEX IF NOT EXISTS ix_documents_extracted_fields_ops
ON documents USING GIN (extracted_fields jsonb_ops);
CREATE INDEX IF NOT EXISTS ix_documents_extracted_fields_path
ON documents USING GIN (extracted_fields jsonb_path_ops);

-- 4) View: due in next 60 days (uses new evidence index)
CREATE OR REPLACE VIEW obligations_due_60 AS
SELECT d.contract_name,
       o.document_id,
       o.obligation_id,
       o.obligation_type,
       o.trigger_event,
       o.due_date,
       o.status,
       (SELECT COUNT(*) FROM obligation_evidence_links e WHERE e.obligation_id = o.obligation_id) AS evidence_count
FROM obligations o
JOIN documents d USING (document_id)
WHERE o.status IN ('open','in_progress')
  AND o.due_date IS NOT NULL
  AND o.due_date <= (current_date + 60);