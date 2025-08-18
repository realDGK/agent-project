# Claude Code – One‑File Setup Spec for Real‑Estate Doc DB

This is a **single file** you can paste into Claude Code (or a Notion page) and say: *“Create these files exactly as specified and run the run‑commands.”* It consolidates the migration, helper scripts, prompt contract, and sanity commands.

---

## How to use this spec

1. **Create files** below exactly as shown (paths + contents).
2. **Run the commands** under **Run‑commands**.
3. (Optional) Use the **Sanity checks**.

Assumes you already have a Docker container named `agent-postgres` with env `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` and the project root is `~/agent-project`.

---

## Files to create (exact paths + contents)

> Create each file verbatim. Use LF line endings. Make the three `scripts/*` files executable.

### 1) Migration – idempotent function, indexes, and view

**File: **``

```sql
-- Evidence de-dupe (no duplicate page links for the same obligation)
CREATE UNIQUE INDEX IF NOT EXISTS ux_evidence_dedupe_idx
ON obligation_evidence_links (obligation_id, evidence_document_id, page_from, page_to, note);

-- Natural key to prevent duplicate obligations (same doc/type/trigger/date/party/desc)
CREATE UNIQUE INDEX IF NOT EXISTS ux_obligations_natural_key
ON obligations (
  document_id,
  obligation_type,
  COALESCE(trigger_event,''),
  COALESCE(due_date, '0001-01-01'::date),
  COALESCE(party_name,''),
  COALESCE(description,'')
);

-- Fast JSON queries on extracted_fields
CREATE INDEX IF NOT EXISTS ix_documents_extracted_fields
ON documents USING GIN (extracted_fields jsonb_path_ops);

-- Quick reporting view
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
  AND o.due_date <= CURRENT_DATE + 60;

-- Idempotent apply_extraction
CREATE OR REPLACE FUNCTION apply_extraction(p_doc_id uuid, p_payload jsonb)
RETURNS void AS $$
DECLARE
  ob  jsonb;
  ev  jsonb;
  oid uuid;
  due date;
  status_in text;
  status_enum obligation_status;
  ob_type text;
  trig   text;
  party  text;
  descr  text;
BEGIN
  -- Save structured fields
  UPDATE documents
  SET extracted_fields = COALESCE(p_payload->'extracted_fields','{}'::jsonb)
  WHERE document_id = p_doc_id;

  -- Obligations (find-or-insert by natural key)
  FOR ob IN SELECT value FROM jsonb_array_elements(COALESCE(p_payload->'obligations','[]'::jsonb)) LOOP
    status_in := LOWER(COALESCE(NULLIF(ob->>'status',''),'open'));
    status_enum := CASE status_in
      WHEN 'open'        THEN 'open'::obligation_status
      WHEN 'in_progress' THEN 'in_progress'::obligation_status
      WHEN 'satisfied'   THEN 'satisfied'::obligation_status
      WHEN 'waived'      THEN 'waived'::obligation_status
      WHEN 'past_due'    THEN 'past_due'::obligation_status
      ELSE 'open'::obligation_status
    END;

    ob_type := COALESCE(NULLIF(ob->>'obligation_type',''),'unspecified');
    trig    := NULLIF(ob->>'trigger_event','');
    party   := NULLIF(ob->>'responsible_party','');
    descr   := NULLIF(ob->>'description','');

    due := NULL;
    IF ob ? 'due_date' AND (ob->>'due_date') ~ '^\d{4}-\d{2}-\d{2}$' THEN
      due := (ob->>'due_date')::date;
    END IF;

    SELECT o.obligation_id INTO oid
    FROM obligations o
    WHERE o.document_id = p_doc_id
      AND lower(o.obligation_type) = lower(ob_type)
      AND COALESCE(o.trigger_event,'') = COALESCE(trig,'')
      AND COALESCE(o.due_date, '0001-01-01'::date) = COALESCE(due, '0001-01-01'::date)
      AND COALESCE(lower(o.party_name),'') = COALESCE(lower(party),'')
      AND COALESCE(lower(o.description),'') = COALESCE(lower(descr),'')
    LIMIT 1;

    IF oid IS NULL THEN
      INSERT INTO obligations (document_id, obligation_type, status, trigger_event, due_date, party_name, description)
      VALUES (p_doc_id, ob_type, status_enum, trig, due, party, descr)
      RETURNING obligation_id INTO oid;
    ELSE
      UPDATE obligations
      SET status        = status_enum,
          trigger_event = COALESCE(trig, trigger_event),
          due_date      = COALESCE(due, due_date),
          party_name    = COALESCE(party, party_name),
          description   = COALESCE(descr, description)
      WHERE obligation_id = oid;
    END IF;

    -- Evidence (idempotent via unique index)
    FOR ev IN SELECT value FROM jsonb_array_elements(COALESCE(ob->'evidence','[]'::jsonb)) LOOP
      INSERT INTO obligation_evidence_links (obligation_id, evidence_document_id, page_from, page_to, note)
      VALUES (
        oid,
        COALESCE(NULLIF(ev->>'document_id','')::uuid, p_doc_id),
        NULLIF(ev->>'page_from','')::int,
        COALESCE(NULLIF(ev->>'page_to','')::int, NULLIF(ev->>'page_from','')::int),
        NULLIF(ev->>'note','')
      )
      ON CONFLICT (obligation_id, evidence_document_id, page_from, page_to, note) DO NOTHING;
    END LOOP;
  END LOOP;
END;
$$ LANGUAGE plpgsql;
```

---

### 2) Helper: open psql REPL inside the container

**File: **``

```bash
#!/usr/bin/env bash
set -euo pipefail
docker exec -it agent-postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

### 3) Helper: run a one‑liner SQL command

**File: **``

```bash
#!/usr/bin/env bash
set -euo pipefail
docker exec -i agent-postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -A -t -q -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '"$*"''
```

### 4) Helper: run a SQL file (or heredoc via stdin)

**File: **``

```bash
#!/usr/bin/env bash
set -euo pipefail
if [ -n "${1-}" ]; then
  docker exec -i agent-postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /dev/stdin' < "$1"
else
  docker exec -i agent-postgres sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /dev/stdin'
fi
```

> After creating these 3 scripts, mark them executable:
>
> ```bash
> chmod +x scripts/opsql scripts/sqlc scripts/sqlf
> ```

---

### 5) Canonical extraction prompt for LLMs

**File: **``

````md
# Extraction Contract (Doc → JSON)

Return **only** this JSON shape (no extra keys):

```json
{
  "doc_type": "Purchase Agreement",
  "extracted_fields": {
    "purchase_price": 3100000,
    "inspection_period_days": 25
  },
  "obligations": [
    {
      "obligation_type": "fee_payment",
      "description": "Pay traffic impact fees",
      "responsible_party": "Developer",
      "trigger_event": "Prior to first building permit",
      "due_date": "YYYY-MM-DD",
      "status": "open",
      "evidence": [
        { "document_id": "", "page_from": 8, "page_to": 8, "note": "COA #12" }
      ]
    }
  ]
}
````

Allowed statuses: `open`, `in_progress`, `satisfied`, `waived`, `past_due`. Omit fields you cannot verify. Numbers are raw (no symbols/commas).

````

---

## Run‑commands (execute from project root)

1) **Apply migration**
```bash
./scripts/sqlf sql/migrations/20250818_idempotent_apply_extraction.sql
````

2. **Quick verifies**

```bash
./scripts/sqlc "SELECT viewname FROM pg_views WHERE viewname='obligations_due_60';"
./scripts/sqlc "SELECT proname FROM pg_proc WHERE proname='apply_extraction';"
```

3. **Create a doc + apply sample JSON twice (idempotency demo)**

```bash
# Create doc
DOC_ID=$(./scripts/sqlc "INSERT INTO documents (contract_type,effective_date,contract_name,extracted_fields) VALUES ('Purchase Agreement', CURRENT_DATE, 'PSA - Idempotency Test', '{}'::jsonb) RETURNING document_id;"); echo "$DOC_ID"

# Apply same JSON twice
./scripts/sqlf <<SQL
SELECT apply_extraction('${DOC_ID}'::uuid, \$J$
{
  "doc_type": "Purchase Agreement",
  "extracted_fields": { "purchase_price": 999999, "inspection_period_days": 30 },
  "obligations": [
    {
      "obligation_type": "fee_payment",
      "description": "Traffic impact fees",
      "responsible_party": "Developer",
      "trigger_event": "Prior to first building permit",
      "due_date": "2025-10-01",
      "status": "open",
      "evidence": [ { "page_from": 8, "page_to": 8, "note": "COA #12" } ]
    }
  ]
}
\$J$::jsonb);

SELECT apply_extraction('${DOC_ID}'::uuid, \$J$
{
  "doc_type": "Purchase Agreement",
  "extracted_fields": { "purchase_price": 999999, "inspection_period_days": 30 },
  "obligations": [
    {
      "obligation_type": "fee_payment",
      "description": "Traffic impact fees",
      "responsible_party": "Developer",
      "trigger_event": "Prior to first building permit",
      "due_date": "2025-10-01",
      "status": "open",
      "evidence": [ { "page_from": 8, "page_to": 8, "note": "COA #12" } ]
    }
  ]
}
\$J$::jsonb);
SQL

# Should show 1 obligation + 1 evidence
./scripts/sqlf <<SQL
SELECT COUNT(*) AS obligations
FROM obligations
WHERE document_id = '${DOC_ID}'::uuid;

SELECT COUNT(*) AS evidence
FROM obligation_evidence_links e
JOIN obligations o USING (obligation_id)
WHERE o.document_id = '${DOC_ID}'::uuid;
SQL
```

4. **Use the due‑soon dashboard**

```bash
./scripts/sqlc "TABLE obligations_due_60 ORDER BY due_date, contract_name;"
```

---

## Sanity queries (copy/paste into psql via `./scripts/opsql`)

```sql
-- Latest doc and its fields
WITH latest AS (SELECT document_id FROM documents ORDER BY created_at DESC LIMIT 1)
SELECT d.document_id, d.contract_name, d.extracted_fields
FROM documents d JOIN latest l ON d.document_id = l.document_id;

-- Obligations for that doc
WITH latest AS (SELECT document_id FROM documents ORDER BY created_at DESC LIMIT 1)
SELECT o.obligation_type, o.trigger_event, o.due_date, o.status
FROM obligations o JOIN latest l ON o.document_id = l.document_id
ORDER BY o.due_date NULLS LAST, o.obligation_id DESC;

-- Evidence for that doc
WITH latest AS (SELECT document_id FROM documents ORDER BY created_at DESC LIMIT 1)
SELECT e.page_from, e.page_to, e.note
FROM obligation_evidence_links e
JOIN obligations o USING (obligation_id)
JOIN latest l ON o.document_id = l.document_id
ORDER BY e.evidence_link_id DESC;
```

---

## Notes

- Scripts are **Bash**; on Linux/macOS no extension needed. Ensure `chmod +x`.
- All SQL runs **inside** the `agent-postgres` container via env vars. No local psql setup required.
- The function is **idempotent**: same payload can be re‑applied without duplicates (thanks to the natural key + `ON CONFLICT`).
- Prompt contract is the **source of truth** for extractors (`config/prompts/extraction_contract.md`).

