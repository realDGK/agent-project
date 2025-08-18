-- Create test document
INSERT INTO documents (contract_type, effective_date, contract_name, extracted_fields)
VALUES ('Purchase Agreement', CURRENT_DATE, 'PSA - Idempotency Test', '{}'::jsonb)
RETURNING document_id AS doc_id;
