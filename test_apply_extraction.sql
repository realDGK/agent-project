-- Apply extraction twice to test idempotency
SELECT apply_extraction('a3be6bb4-e972-40d9-9e60-0791daa934b4'::uuid, $J$
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
$J$::jsonb);

-- Apply same extraction again
SELECT apply_extraction('a3be6bb4-e972-40d9-9e60-0791daa934b4'::uuid, $J$
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
$J$::jsonb);
