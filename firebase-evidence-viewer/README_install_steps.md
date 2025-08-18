
# Real Estate Schema Integration — Fast Path

## What you’re adding
- Flexible `documents.extracted_fields` (JSONB) + `field_dictionary` to validate per-type fields.
- `obligation_evidence_links` so each obligation can point to multiple proof pages/docs.
- Indexes you actually need, and a `documents_as_of` view for time-aware queries.

## Files in this folder
- `migrations/20250817_add_flex_fields_and_evidence.sql` — run this against your DB.
- `prompts/claude_extraction_prompt.md` — give this to your LLM for extraction.
- Use the CSVs we already generated earlier:
  - `real_estate_doc_types_*.csv`
  - `critical_fields_by_doctype_*.csv`

## 5 steps (copy/paste friendly)

### 1) Backup (always)
```bash
pg_dump -Fc -h <host> -U <user> <db> > backup_$(date +%F).dump
```

### 2) Apply the migration
```bash
psql -h <host> -U <user> -d <db> -f migrations/20250817_add_flex_fields_and_evidence.sql
```

### 3) Load the field dictionary (from the Critical Fields CSV)
```bash
-- in psql
\copy field_dictionary (doc_type, field_key, label, datatype, units, regex, required, importance) FROM '<ABSOLUTE_PATH>/critical_fields_by_doctype_*.csv' CSV HEADER
```

> If a row fails on `doc_type` casting, the enum label doesn't match. Either adjust the CSV or add the missing enum to `contract_type`.

### 4) (Optional) Loosen `effective_date` if it causes ingest errors
```sql
ALTER TABLE documents ALTER COLUMN effective_date DROP NOT NULL;
```

### 5) Test it quick
```sql
-- add a dummy PSA with one extracted field
INSERT INTO documents (contract_type, effective_date, contract_name, extracted_fields)
VALUES ('Purchase Agreement', CURRENT_DATE, 'PSA – Test',
        '{"purchase_price": 2500000, "inspection_period_days": 30}'::jsonb)
RETURNING document_id;

-- add an obligation
INSERT INTO obligations (document_id, obligation_type, status, description, due_date)
VALUES ('<returned_uuid>', 'fee_payment', 'open', 'Pay traffic impact fees before BP', CURRENT_DATE + 30)
RETURNING obligation_id;

-- add proof
INSERT INTO obligation_evidence_links (obligation_id, evidence_document_id, page_from, page_to, note)
VALUES ('<obl_uuid>', '<doc_uuid>', 12, 12, 'COA #14');

-- sanity queries
SELECT doc_type, contract_name, extracted_fields FROM documents LIMIT 5;
SELECT * FROM documents_as_of LIMIT 5;
SELECT o.description, e.page_from, e.note
FROM obligations o LEFT JOIN obligation_evidence_links e USING (obligation_id)
ORDER BY o.created_at DESC;
```

## What to hand to your LLM (Claude)
- The prompt: `prompts/claude_extraction_prompt.md`
- The `field_dictionary` rows for the target `doc_type` (pull them and paste into the chat or pass via tool-call).
- The raw text (or per-page text) of the document + minimal `doc_metadata`.

Aim the model’s output at:
```sql
UPDATE documents
SET extracted_fields = :json_output->'extracted_fields'
WHERE document_id = :id;
-- then insert obligations + evidence rows with the IDs and page anchors from the output
```

That’s it. If you want me to run a dry run migration script customized to your environment (Docker, Compose, or direct psql), tell me your connection method and I’ll tailor the commands.
