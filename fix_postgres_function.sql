-- Fixed apply_extraction function with proper enum handling
-- Run this in your PostgreSQL container

CREATE OR REPLACE FUNCTION apply_extraction(p_doc_id uuid, p_payload jsonb)
RETURNS void AS $$
DECLARE
  ob  jsonb;
  ev  jsonb;
  oid uuid;
  due date;
  status_val obligation_status;
BEGIN
  -- 1) Write structured fields to the document
  UPDATE documents
  SET extracted_fields = COALESCE(p_payload->'extracted_fields','{}'::jsonb)
  WHERE document_id = p_doc_id;

  -- 2) Insert obligations + evidence
  FOR ob IN
    SELECT value FROM jsonb_array_elements(COALESCE(p_payload->'obligations','[]'::jsonb))
  LOOP
    -- Parse due date safely
    due := NULL;
    IF ob ? 'due_date' AND (ob->>'due_date') ~ '^\d{4}-\d{2}-\d{2}' THEN
      due := (ob->>'due_date')::date;
    END IF;

    -- Parse status safely with proper enum casting
    status_val := CASE LOWER(COALESCE(NULLIF(ob->>'status',''),'open'))
      WHEN 'open'        THEN 'open'::obligation_status
      WHEN 'in_progress' THEN 'in_progress'::obligation_status
      WHEN 'satisfied'   THEN 'satisfied'::obligation_status
      WHEN 'waived'      THEN 'waived'::obligation_status
      WHEN 'past_due'    THEN 'past_due'::obligation_status
      ELSE 'open'::obligation_status
    END;

    INSERT INTO obligations (
      document_id, obligation_type, status, trigger_event, due_date, party_name, description
    )
    VALUES (
      p_doc_id,
      COALESCE(NULLIF(ob->>'obligation_type',''),'unspecified'),
      status_val,
      NULLIF(ob->>'trigger_event',''),
      due,
      NULLIF(ob->>'responsible_party',''),
      NULLIF(ob->>'description','')
    )
    RETURNING obligation_id INTO oid;

    -- Insert evidence items if they exist
    FOR ev IN
      SELECT value FROM jsonb_array_elements(COALESCE(ob->'evidence','[]'::jsonb))
    LOOP
      INSERT INTO obligation_evidence_links (
        obligation_id, evidence_document_id, page_from, page_to, note
      )
      VALUES (
        oid,
        COALESCE(NULLIF(ev->>'document_id','')::uuid, p_doc_id),
        NULLIF(ev->>'page_from','')::int,
        COALESCE(NULLIF(ev->>'page_to','')::int, NULLIF(ev->>'page_from','')::int),
        NULLIF(ev->>'note','')
      );
    END LOOP;
  END LOOP;
END;
$$ LANGUAGE plpgsql;