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
