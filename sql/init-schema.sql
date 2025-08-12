-- ============================================
-- Extensions
-- ============================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- gen_random_uuid()
-- Optional: if you want ANN search in Postgres
-- CREATE EXTENSION IF NOT EXISTS vector;    -- pgvector

-- ============================================
-- Enums
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contract_type') THEN
        CREATE TYPE contract_type AS ENUM (
            'Lease Agreement','NDA','Contractor Agreement','Purchase Agreement','Development Agreement',
            'Letter of Intent','Amendment','Escrow Instructions','Resolution','Budget','Settlement Statement',
            'Trustee''s Deed Upon Sale','Disbursement of Proceeds','Substitution of Trustee and Deed of Reconveyance',
            'Email','Conditional Use Permit','Site Plan Review','Deed of Trust','Grant Deed','Quitclaim','Easement',
            'CC&Rs','SNDA','Estoppel','Guaranty','Indemnity','Option Agreement','Assignment & Assumption',
            'Notice of Default','Notice of Sale','Lis Pendens','Preliminary Title Report','Title Policy','ALTA Survey',
            'Performance/Payment Bond','Change Order','Pay App','Mechanics Lien','Lien Release','Will-Serve Letter',
            'Building Permit','Grading Permit','Encroachment Permit','Certificate of Occupancy','CEQA'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ceqa_doc_type') THEN
        CREATE TYPE ceqa_doc_type AS ENUM ('EIR','MND','NOD','NOE','Initial Study','Addendum','Other');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_state') THEN
        CREATE TYPE document_state AS ENUM ('active','amended','void','draft');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'confidentiality') THEN
        CREATE TYPE confidentiality AS ENUM ('public','internal','privileged');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'permission') THEN
        CREATE TYPE permission AS ENUM ('read','write','admin');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'relation_type') THEN
        CREATE TYPE relation_type AS ENUM ('amends','replaces','exhibit','attachment','references','recorded_against','implements','evidence_of');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'obligation_status') THEN
        CREATE TYPE obligation_status AS ENUM ('open','in_progress','satisfied','waived','past_due');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'capacity_action') THEN
        CREATE TYPE capacity_action AS ENUM ('debit','credit');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'capacity_unit') THEN
        CREATE TYPE capacity_unit AS ENUM ('GPD','AFY');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'recipient_type') THEN
        CREATE TYPE recipient_type AS ENUM ('to','cc','bcc');
    END IF;
END$$;

-- ============================================
-- Core: documents, provenance, security/ACLs
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    document_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_type       contract_type NOT NULL,
    ceqa_document_type  ceqa_doc_type,
    document_state      document_state DEFAULT 'active',
    contract_name       TEXT,
    execution_date      DATE,
    effective_date      DATE NOT NULL,
    expiration_date     DATE,
    closing_date        DATE,
    currency            CHAR(3) DEFAULT 'USD',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_provenance (
    document_id         UUID PRIMARY KEY REFERENCES documents(document_id) ON DELETE CASCADE,
    source_uri          TEXT NOT NULL,
    source_system       TEXT,
    ingestion_time      TIMESTAMPTZ NOT NULL,
    ingested_by         TEXT,
    sha256_hash         TEXT NOT NULL,
    file_size_bytes     BIGINT,
    mime_type           TEXT,
    page_count          INT,
    text_extraction_method TEXT,
    ocr_confidence      NUMERIC(5,2),
    parser_version      TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_document_provenance_hash ON document_provenance(sha256_hash);

CREATE TABLE IF NOT EXISTS document_versions (
    document_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    version_no          INT NOT NULL,
    sha256_hash         TEXT NOT NULL,
    parser_version      TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          TEXT
);

ALTER TABLE documents
ADD COLUMN IF NOT EXISTS supersedes_document_id UUID,
ADD COLUMN IF NOT EXISTS superseded_by_document_id UUID;

ALTER TABLE documents
    ADD CONSTRAINT fk_docs_supersedes FOREIGN KEY (supersedes_document_id) REFERENCES documents(document_id) ON DELETE SET NULL,
    ADD CONSTRAINT fk_docs_superseded_by FOREIGN KEY (superseded_by_document_id) REFERENCES documents(document_id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS document_security (
    document_id     UUID PRIMARY KEY REFERENCES documents(document_id) ON DELETE CASCADE,
    confidentiality confidentiality,
    legal_hold      BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS document_privacy_flags (
    document_id     UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    flag            TEXT NOT NULL,
    PRIMARY KEY (document_id, flag)
);

CREATE TABLE IF NOT EXISTS document_acl (
    acl_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    subject         TEXT NOT NULL,
    permission      permission NOT NULL
);

-- ============================================
-- Projects linkage
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    project_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    code        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_projects (
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    project_id  UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, project_id)
);

-- ============================================
-- Parties and roles
-- ============================================
CREATE TABLE IF NOT EXISTS parties (
    party_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    address     TEXT,
    phone       TEXT,
    email       TEXT
);

CREATE TABLE IF NOT EXISTS document_party_roles (
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    party_id    UUID NOT NULL REFERENCES parties(party_id) ON DELETE RESTRICT,
    role        TEXT NOT NULL,
    title       TEXT,
    PRIMARY KEY (document_id, party_id, role)
);

-- ============================================
-- Related documents
-- ============================================
CREATE TABLE IF NOT EXISTS related_documents (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id          UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    related_document_id  UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    relation_type        relation_type NOT NULL,
    description          TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_related_doc_pair ON related_documents(document_id, related_document_id, relation_type);

-- ============================================
-- Parcels & linkage
-- ============================================
CREATE TABLE IF NOT EXISTS parcels (
    parcel_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    apn             TEXT NOT NULL,
    county_fips     TEXT,
    state           TEXT,
    legal_description TEXT,
    acres           NUMERIC,
    lot_number      TEXT,
    lat             DOUBLE PRECISION,
    lon             DOUBLE PRECISION
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_parcel_apn_fips ON parcels(apn, county_fips);

CREATE TABLE IF NOT EXISTS document_parcels (
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    parcel_id   UUID NOT NULL REFERENCES parcels(parcel_id) ON DELETE RESTRICT,
    relation    TEXT,
    PRIMARY KEY (document_id, parcel_id)
);

-- ============================================
-- Files (for canonical docs & normalized attachments)
-- ============================================
CREATE TABLE IF NOT EXISTS files (
    file_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    filename     TEXT NOT NULL,
    mime_type    TEXT,
    size_bytes   BIGINT,
    sha256       TEXT NOT NULL,
    storage_uri  TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_files_document_id ON files(document_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_files_sha256 ON files(sha256);

-- ============================================
-- Emails (PST lineage) + recipients + attachments
-- ============================================
CREATE TABLE IF NOT EXISTS emails (
    email_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      TEXT UNIQUE,
    thread_id       TEXT,
    in_reply_to     TEXT,
    received_date   TIMESTAMPTZ NOT NULL,
    mailbox         TEXT,
    pst_file_path   TEXT,
    pst_entry_id    TEXT,
    delivery_headers_sha256 TEXT,
    from_addr       TEXT
);

CREATE TABLE IF NOT EXISTS email_recipients (
    email_id    UUID NOT NULL REFERENCES emails(email_id) ON DELETE CASCADE,
    rtype       recipient_type NOT NULL,
    address     TEXT NOT NULL,
    PRIMARY KEY (email_id, rtype, address)
);

-- Link email attachments to normalized files
CREATE TABLE IF NOT EXISTS email_attachments (
    email_id    UUID NOT NULL REFERENCES emails(email_id) ON DELETE CASCADE,
    file_id     UUID NOT NULL REFERENCES files(file_id) ON DELETE CASCADE,
    PRIMARY KEY (email_id, file_id)
);

-- Optional: map a Document record to its source email (for "contract_type = Email")
ALTER TABLE documents ADD COLUMN IF NOT EXISTS email_id UUID REFERENCES emails(email_id) ON DELETE SET NULL;

-- ============================================
-- Legal recording details
-- ============================================
CREATE TABLE IF NOT EXISTS legal_recordings (
    recording_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id        UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    instrument_type    TEXT,
    instrument_number  TEXT,
    book               TEXT,
    page               TEXT,
    recording_date     DATE,
    execution_date     DATE,
    county             TEXT,
    county_fips        TEXT,
    grantor            TEXT[],   -- keep simple; normalize later if needed
    grantee            TEXT[],
    notary_name        TEXT,
    notary_commission_no TEXT,
    notary_expires     DATE,
    cross_reference_instruments TEXT[]
);
CREATE INDEX IF NOT EXISTS ix_recordings_doc ON legal_recordings(document_id);
CREATE INDEX IF NOT EXISTS ix_recordings_instr ON legal_recordings(county_fips, instrument_number);

-- ============================================
-- Permits & approvals
-- ============================================
CREATE TABLE IF NOT EXISTS permits (
    permit_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    issuing_agency  TEXT,
    status          TEXT,
    issue_date      DATE,
    expiry_date     DATE,
    bond_number     TEXT,
    bond_amount     NUMERIC,
    permit_numbers  TEXT[],
    resolution_numbers TEXT[],
    conditions_of_approval TEXT[],
    inspection_history   TEXT[]
);
CREATE INDEX IF NOT EXISTS ix_permits_doc ON permits(document_id);
CREATE INDEX IF NOT EXISTS ix_permits_numbers ON permits USING GIN (permit_numbers);

-- ============================================
-- Financial terms, costs, draws, loans
-- ============================================
CREATE TABLE IF NOT EXISTS financial_terms (
    document_id         UUID PRIMARY KEY REFERENCES documents(document_id) ON DELETE CASCADE,
    rent_amount         NUMERIC,
    purchase_price      NUMERIC,
    security_deposit    NUMERIC,
    payment_terms       TEXT,
    interest_reserve    NUMERIC,
    total_contract_value NUMERIC,
    currency            CHAR(3) DEFAULT 'USD'
);

CREATE TABLE IF NOT EXISTS financial_loans (
    loan_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    loan_amount NUMERIC,
    loan_type   TEXT,
    lender      TEXT
);

CREATE TABLE IF NOT EXISTS financial_itemized_costs (
    cost_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    item            TEXT,
    amount          NUMERIC,
    unit            TEXT,
    unit_price      NUMERIC,
    cost_code       TEXT,
    committed_vendor TEXT,
    retention_pct   NUMERIC
);

CREATE TABLE IF NOT EXISTS financial_draw_requests (
    draw_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    draw_no         TEXT,
    period_start    DATE,
    period_end      DATE,
    amount_requested NUMERIC,
    amount_approved NUMERIC,
    lien_releases   TEXT[]
);

-- ============================================
-- Clauses & obligations
-- ============================================
CREATE TABLE IF NOT EXISTS key_clauses (
    clause_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    clause_name  TEXT NOT NULL,
    clause_text  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS obligations (
    obligation_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id          UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    party_id             UUID REFERENCES parties(party_id) ON DELETE SET NULL,
    party_name           TEXT,
    obligation_type      TEXT NOT NULL,
    trigger_event        TEXT,
    due_date             DATE,
    status               obligation_status NOT NULL,
    evidence_document_id UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    penalty              TEXT
);
CREATE INDEX IF NOT EXISTS ix_obligations_due ON obligations(status, due_date);

-- ============================================
-- Water & sewer details + capacity ledger
-- ============================================
CREATE TABLE IF NOT EXISTS water_sewer_details (
    document_id             UUID PRIMARY KEY REFERENCES documents(document_id) ON DELETE CASCADE,
    sewer_capacity_gpd      NUMERIC,
    reimbursement_amount    NUMERIC,
    pond_release_payment    NUMERIC,
    water_well_capacity     TEXT,
    allocation_source       TEXT,
    transferable            BOOLEAN,
    meter_id                TEXT
);

CREATE TABLE IF NOT EXISTS capacity_bank_ledger (
    entry_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    action              capacity_action NOT NULL,
    amount              NUMERIC NOT NULL,
    unit                capacity_unit NOT NULL,
    as_of_date          DATE NOT NULL,
    reason              TEXT,
    source_document_id  UUID REFERENCES documents(document_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_capacity_ledger_doc ON capacity_bank_ledger(document_id, as_of_date);

-- ============================================
-- Fees ledger
-- ============================================
CREATE TABLE IF NOT EXISTS fees_ledger (
    entry_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    project_id          UUID REFERENCES projects(project_id) ON DELETE SET NULL,
    parcel_id           UUID REFERENCES parcels(parcel_id) ON DELETE SET NULL,
    scope               TEXT CHECK (scope IN ('project','parcel','document')),
    apn                 TEXT,
    fee_type            TEXT NOT NULL,
    assessed_amount     NUMERIC,
    paid_amount         NUMERIC,
    credit_applied      NUMERIC,
    balance             NUMERIC,
    currency            CHAR(3) DEFAULT 'USD',
    as_of_date          DATE NOT NULL,
    evidence_document_id UUID REFERENCES documents(document_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_fees_scope_date ON fees_ledger(scope, as_of_date);

-- ============================================
-- Lease & Development details (optional modules)
-- ============================================
CREATE TABLE IF NOT EXISTS lease_terms (
    document_id       UUID PRIMARY KEY REFERENCES documents(document_id) ON DELETE CASCADE,
    lease_term_years  NUMERIC,
    base_year         INT,
    cpi_cap_pct       NUMERIC,
    ti_allowance      NUMERIC,
    permitted_uses    TEXT[],
    maintenance_responsibilities TEXT
);

CREATE TABLE IF NOT EXISTS lease_base_rent_schedule (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id   UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    start_date    DATE NOT NULL,
    end_date      DATE NOT NULL,
    amount        NUMERIC NOT NULL,
    currency      CHAR(3) DEFAULT 'USD'
);

CREATE TABLE IF NOT EXISTS lease_option_windows (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id    UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    notice_open    DATE,
    notice_close   DATE,
    term_years     NUMERIC
);

CREATE TABLE IF NOT EXISTS development_details (
    document_id                 UUID PRIMARY KEY REFERENCES documents(document_id) ON DELETE CASCADE,
    development_plan            TEXT,
    approved_uses               TEXT[],
    infrastructure_obligations  TEXT,
    entitlements                TEXT,
    density                     TEXT
);

-- ============================================
-- Embeddings (doc optional + chunked preferred)
-- ============================================
-- Option A: pgvector (recommended)
-- CREATE TABLE IF NOT EXISTS embedding_chunks (
--     chunk_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     document_id      UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
--     chunk_index      INT NOT NULL,
--     text_offset_start INT,
--     text_offset_end   INT,
--     embedding        vector(1536) NOT NULL, -- adjust dim
--     embedding_model  TEXT,
--     embedding_dim    INT,
--     created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
-- );
-- CREATE INDEX IF NOT EXISTS ix_embed_doc ON embedding_chunks(document_id);
-- CREATE INDEX IF NOT EXISTS ivfflat_embedding ON embedding_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);

-- Option B: float array (if not using pgvector yet)
CREATE TABLE IF NOT EXISTS embedding_chunks (
    chunk_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id      UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_index      INT NOT NULL,
    text_offset_start INT,
    text_offset_end   INT,
    embedding        DOUBLE PRECISION[] NOT NULL,
    embedding_model  TEXT,
    embedding_dim    INT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_embed_doc ON embedding_chunks(document_id, chunk_index);

-- Optional doc-level embedding metadata
CREATE TABLE IF NOT EXISTS embedding_documents (
    document_id      UUID PRIMARY KEY REFERENCES documents(document_id) ON DELETE CASCADE,
    embedding        DOUBLE PRECISION[],
    embedding_model  TEXT,
    embedding_dim    INT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- Housekeeping trigger: touch updated_at
-- ============================================
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_documents_updated ON documents;
CREATE TRIGGER trg_documents_updated
BEFORE UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
