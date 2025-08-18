
-- Real Estate Development Docs - Minimal SQL Skeleton
-- Generated: 20250817-125826

-- ENUMs
DO $$ BEGIN
    CREATE TYPE importance_t AS ENUM ('Low','Med','High');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Core reference tables
CREATE TABLE IF NOT EXISTS jurisdictions (
    jurisdiction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    county TEXT,
    state TEXT NOT NULL,
    agency_type TEXT, -- City, County, District, State, Federal
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    jurisdiction_id UUID REFERENCES jurisdictions(jurisdiction_id),
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS parcels (
    parcel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    apn TEXT NOT NULL,
    jurisdiction_id UUID REFERENCES jurisdictions(jurisdiction_id),
    site_name TEXT,
    -- geometry GEOGRAPHY/GEOMETRY optional
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS parties (
    party_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT, -- individual, llc, corp, agency, lender, tenant, etc.
    fein TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_type TEXT NOT NULL,
    title TEXT,
    lifecycle_stage TEXT, -- acquisition, entitlement, financing, etc.
    jurisdiction_id UUID REFERENCES jurisdictions(jurisdiction_id),
    project_id UUID REFERENCES projects(project_id),
    source_uri TEXT,
    hash_sha256 TEXT,
    page_count INTEGER,
    execution_date DATE,
    effective_date DATE,
    recording_date DATE,
    instrument_number TEXT,
    ocr_status TEXT,
    extraction_confidence NUMERIC(5,2),
    extracted_fields JSONB, -- flexible per-type data
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_recording ON documents(recording_date);
CREATE INDEX IF NOT EXISTS idx_documents_instrument ON documents(instrument_number);
CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON documents(jurisdiction_id);

-- Many-to-many: documents ↔ parcels
CREATE TABLE IF NOT EXISTS document_parcels (
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    parcel_id UUID REFERENCES parcels(parcel_id) ON DELETE CASCADE,
    role TEXT, -- benefited, burdened, subject, etc.
    PRIMARY KEY (document_id, parcel_id, role)
);

-- Many-to-many: documents ↔ parties (with role)
CREATE TABLE IF NOT EXISTS document_parties (
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    party_id UUID REFERENCES parties(party_id) ON DELETE CASCADE,
    role TEXT, -- buyer, seller, grantor, grantee, lender, borrower, trustee, landlord, tenant, agency, etc.
    PRIMARY KEY (document_id, party_id, role)
);

-- Permits (optional but useful)
CREATE TABLE IF NOT EXISTS permits (
    permit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    permit_type TEXT NOT NULL, -- CUP, Variance, Building, Encroachment, etc.
    number TEXT,
    agency TEXT,
    status TEXT,
    issue_date DATE,
    expiration_date DATE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_permits (
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    permit_id UUID REFERENCES permits(permit_id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, permit_id)
);

-- Obligations registry
CREATE TABLE IF NOT EXISTS obligations (
    obligation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    clause_reference TEXT, -- page/section/caption
    description TEXT NOT NULL,
    responsible_party_id UUID REFERENCES parties(party_id),
    trigger_event TEXT,
    due_date DATE,
    amount NUMERIC(18,2),
    units TEXT,
    status TEXT, -- open, in_progress, satisfied, waived, defaulted
    priority importance_t DEFAULT 'High',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Evidence links to prove satisfaction
CREATE TABLE IF NOT EXISTS obligation_evidence_links (
    evidence_link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obligation_id UUID REFERENCES obligations(obligation_id) ON DELETE CASCADE,
    evidence_document_id UUID REFERENCES documents(document_id),
    page_from INTEGER,
    page_to INTEGER,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Field dictionary to validate JSONB extracted_fields
CREATE TABLE IF NOT EXISTS field_dictionary (
    doc_type TEXT NOT NULL,
    field_key TEXT NOT NULL,
    label TEXT,
    datatype TEXT, -- text, integer, decimal, currency, date, boolean, enum(...), party, text[], etc.
    units TEXT,
    regex TEXT,
    required BOOLEAN DEFAULT false,
    importance importance_t DEFAULT 'High',
    PRIMARY KEY (doc_type, field_key)
);

CREATE INDEX IF NOT EXISTS idx_field_dict_doctype ON field_dictionary(doc_type);

-- Suggested import: load your critical_fields_by_doctype CSV into field_dictionary.
-- Suggested practice: promote frequently queried JSONB fields into materialized views or columns.
