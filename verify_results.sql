-- Check obligations count
SELECT COUNT(*) AS obligations
FROM obligations
WHERE document_id = 'a3be6bb4-e972-40d9-9e60-0791daa934b4'::uuid;

-- Check evidence count
SELECT COUNT(*) AS evidence
FROM obligation_evidence_links e
JOIN obligations o USING (obligation_id)
WHERE o.document_id = 'a3be6bb4-e972-40d9-9e60-0791daa934b4'::uuid;

-- Show actual data
SELECT d.contract_name, d.extracted_fields,
       o.obligation_type, o.description, o.status, o.due_date
FROM documents d
LEFT JOIN obligations o ON d.document_id = o.document_id
WHERE d.document_id = 'a3be6bb4-e972-40d9-9e60-0791daa934b4'::uuid;
