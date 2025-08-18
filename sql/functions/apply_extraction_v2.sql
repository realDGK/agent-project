-- Revised apply_extraction (race-safe, drift-aware)
-- Uses INSERT … ON CONFLICT for true idempotency

CREATE OR REPLACE FUNCTION apply_extraction(p_doc_id uuid, p_payload jsonb, p_mark_superseded boolean DEFAULT true)
RETURNS void AS $$
DECLARE
  ob          jsonb;
  ev          jsonb;
  oid         uuid;
  due         date;
  status_in   text;
  status_enum obligation_status;
  ob_type     text;
  trig        text;
  party       text;
  descr       text;
  touched     uuid[] := '{}';
BEGIN
  -- 1) Save structured fields (idempotent)
  UPDATE documents
     SET extracted_fields = COALESCE(p_payload->'extracted_fields','{}'::jsonb)
   WHERE document_id = p_doc_id;

  -- 2) Upsert obligations
  FOR ob IN SELECT value FROM jsonb_array_elements(COALESCE(p_payload->'obligations','[]'::jsonb)) LOOP
    status_in := lower(coalesce(nullif(ob->>'status',''),'open'));
    status_enum := CASE status_in
      WHEN 'open'        THEN 'open'::obligation_status
      WHEN 'in_progress' THEN 'in_progress'::obligation_status
      WHEN 'satisfied'   THEN 'satisfied'::obligation_status
      WHEN 'waived'      THEN 'waived'::obligation_status
      WHEN 'past_due'    THEN 'past_due'::obligation_status
      ELSE 'open'::obligation_status
    END;

    ob_type := coalesce(nullif(ob->>'obligation_type',''),'unspecified');
    trig    := nullif(ob->>'trigger_event','');
    party   := nullif(ob->>'responsible_party','');
    descr   := nullif(ob->>'description','');

    -- normalize text (trim + collapse whitespace + lower) for storage consistency
    trig  := CASE WHEN trig  IS NULL THEN NULL ELSE regexp_replace(trim(trig),  '\s+', ' ', 'g') END;
    party := CASE WHEN party IS NULL THEN NULL ELSE regexp_replace(trim(party), '\s+', ' ', 'g') END;
    descr := CASE WHEN descr IS NULL THEN NULL ELSE regexp_replace(trim(descr), '\s+', ' ', 'g') END;

    due := NULL;
    IF ob ? 'due_date' AND (ob->>'due_date') ~ '^\d{4}-\d{2}-\d{2}$' THEN
      due := (ob->>'due_date')::date;
    END IF;

    -- upsert using the natural-hash unique index
    INSERT INTO obligations (document_id, obligation_type, status, trigger_event, due_date, party_name, description)
    VALUES (p_doc_id, ob_type, status_enum, trig, due, party, descr)
    ON CONFLICT (document_id, obligation_hash) DO UPDATE
      SET status        = EXCLUDED.status,
          trigger_event = COALESCE(EXCLUDED.trigger_event, obligations.trigger_event),
          due_date      = COALESCE(EXCLUDED.due_date, obligations.due_date),
          party_name    = COALESCE(EXCLUDED.party_name, obligations.party_name),
          description   = COALESCE(EXCLUDED.description, obligations.description)
    RETURNING obligation_id INTO oid;

    touched := touched || oid;

    -- 3) Evidence (idempotent via unique index without note)
    FOR ev IN SELECT value FROM jsonb_array_elements(COALESCE(ob->'evidence','[]'::jsonb)) LOOP
      INSERT INTO obligation_evidence_links (obligation_id, evidence_document_id, page_from, page_to, note)
      VALUES (
        oid,
        COALESCE(NULLIF(ev->>'document_id','')::uuid, p_doc_id),
        NULLIF(ev->>'page_from','')::int,
        COALESCE(NULLIF(ev->>'page_to','')::int, NULLIF(ev->>'page_from','')::int),
        NULLIF(ev->>'note','')
      )
      ON CONFLICT (obligation_id, evidence_document_id, page_from, page_to) DO NOTHING;
    END LOOP;
  END LOOP;

  -- 4) Optionally mark prior obligations (for this doc) that were not touched as superseded
  IF p_mark_superseded AND array_length(touched,1) IS NOT NULL THEN
    UPDATE obligations
       SET status = 'superseded'::obligation_status
     WHERE document_id = p_doc_id
       AND obligation_id <> ALL(touched)
       AND status IN ('open','in_progress');
  END IF;
END;
$$ LANGUAGE plpgsql;