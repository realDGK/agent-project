SELECT lr.*, d.document_id, p.apn
FROM legal_recordings lr
JOIN documents d ON d.document_id = lr.document_id
JOIN document_parcels dp ON dp.document_id = d.document_id
JOIN parcels p ON p.parcel_id = dp.parcel_id
WHERE p.apn = $1
ORDER BY lr.recording_date;
