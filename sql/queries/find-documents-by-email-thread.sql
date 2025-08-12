SELECT e.message_id, f.filename, f.storage_uri, d.document_id, d.contract_type
FROM emails e
LEFT JOIN email_attachments ea ON ea.email_id = e.email_id
LEFT JOIN files f ON f.file_id = ea.file_id
LEFT JOIN documents d ON d.email_id = e.email_id OR d.document_id = f.document_id
WHERE e.thread_id = $1
ORDER BY e.received_date;
