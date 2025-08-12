SELECT o.*, d.contract_name, d.contract_type
FROM obligations o
JOIN documents d USING (document_id)
WHERE o.status IN ('open','in_progress')
    AND o.due_date <= CURRENT_DATE + INTERVAL '6 months'
ORDER BY o.due_date;