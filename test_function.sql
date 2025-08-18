-- Test the fixed function
-- Run this after the function fix

-- First, let's make sure we have the required tables
DO $$
BEGIN
    -- Add extracted_fields column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'documents' AND column_name = 'extracted_fields'
    ) THEN
        ALTER TABLE documents ADD COLUMN extracted_fields JSONB;
    END IF;
    
    -- Create obligation_evidence_links table if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'obligation_evidence_links') THEN
        CREATE TABLE obligation_evidence_links (
            evidence_link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            obligation_id UUID NOT NULL REFERENCES obligations(obligation_id) ON DELETE CASCADE,
            evidence_document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
            page_from INT,
            page_to INT,
            note TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX ix_obligation_evidence_obl ON obligation_evidence_links(obligation_id);
        CREATE INDEX ix_obligation_evidence_doc ON obligation_evidence_links(evidence_document_id);
    END IF;
END $$;

-- Now test the function
WITH ins AS (
  INSERT INTO documents (contract_type, effective_date, contract_name, extracted_fields)
  VALUES ('Purchase Agreement', CURRENT_DATE, 'PSA - Claude Test Fixed', '{}'::jsonb)
  RETURNING document_id
)
SELECT apply_extraction(
  (SELECT document_id FROM ins),
  jsonb_build_object(
    'doc_type', 'Purchase Agreement',
    'extracted_fields', jsonb_build_object(
      'purchase_price', 3100000,
      'inspection_period_days', 25
    ),
    'obligations', jsonb_build_array(
      jsonb_build_object(
        'obligation_type', 'fee_payment',
        'description', 'Pay traffic impact fees',
        'responsible_party', 'Developer',
        'trigger_event', 'Prior to first building permit',
        'due_date', '2025-10-01',
        'status', 'open',
        'evidence', jsonb_build_array(
          jsonb_build_object(
            'page_from', 8,
            'page_to', 8,
            'note', 'COA #12'
          )
        )
      )
    )
  )
);

-- Verify what was created
SELECT 'DOCUMENTS' as table_name, contract_name, extracted_fields
FROM documents
WHERE contract_name LIKE '%Claude Test%'
ORDER BY created_at DESC
LIMIT 3

UNION ALL

SELECT 'OBLIGATIONS' as table_name, 
       CONCAT(obligation_type, ': ', description) as contract_name,
       jsonb_build_object('status', status, 'due_date', due_date) as extracted_fields
FROM obligations o
JOIN documents d ON o.document_id = d.document_id
WHERE d.contract_name LIKE '%Claude Test%'
ORDER BY o.created_at DESC
LIMIT 3

UNION ALL

SELECT 'EVIDENCE' as table_name,
       CONCAT('Pages ', page_from, '-', page_to, ': ', note) as contract_name,
       NULL as extracted_fields
FROM obligation_evidence_links oel
JOIN obligations o ON oel.obligation_id = o.obligation_id
JOIN documents d ON o.document_id = d.document_id
WHERE d.contract_name LIKE '%Claude Test%'
ORDER BY oel.created_at DESC
LIMIT 3;