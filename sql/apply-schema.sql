-- Apply Real Estate Schema Step by Step
\echo 'Creating pgcrypto extension...'
CREATE EXTENSION IF NOT EXISTS pgcrypto;

\echo 'Creating enums...'
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contract_type') THEN
        CREATE TYPE contract_type AS ENUM (
            'Lease Agreement', 'NDA', 'Contractor Agreement', 'Purchase Agreement', 'Development Agreement',
            'Letter of Intent', 'Amendment', 'Escrow Instructions', 'Resolution', 'Budget', 'Settlement Statement',
            'Email', 'Building Permit', 'CEQA'
        );
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_state') THEN
        CREATE TYPE document_state AS ENUM ('active', 'amended', 'void', 'draft');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'confidentiality') THEN
        CREATE TYPE confidentiality AS ENUM ('public', 'internal', 'privileged');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'obligation_status') THEN
        CREATE TYPE obligation_status AS ENUM ('open', 'in_progress', 'satisfied', 'waived', 'past_due');
    END IF;
END$$;

\echo 'Creating core documents table...'
CREATE TABLE IF NOT EXISTS documents (
    document_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_type       contract_type NOT NULL,
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

\echo 'Creating supporting tables...'
CREATE TABLE IF NOT EXISTS parties (
    party_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    address     TEXT,
    phone       TEXT,
    email       TEXT
);

CREATE TABLE IF NOT EXISTS parcels (
    parcel_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    apn             TEXT NOT NULL,
    county_fips     TEXT,
    state           TEXT,
    legal_description TEXT,
    acres           NUMERIC,
    lat             DOUBLE PRECISION,
    lon             DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS financial_terms (
    document_id         UUID PRIMARY KEY REFERENCES documents(document_id) ON DELETE CASCADE,
    rent_amount         NUMERIC,
    purchase_price      NUMERIC,
    security_deposit    NUMERIC,
    payment_terms       TEXT,
    total_contract_value NUMERIC,
    currency            CHAR(3) DEFAULT 'USD'
);

CREATE TABLE IF NOT EXISTS obligations (
    obligation_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id          UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    party_name           TEXT,
    obligation_type      TEXT NOT NULL,
    trigger_event        TEXT,
    due_date             DATE,
    status               obligation_status NOT NULL,
    penalty              TEXT
);

\echo 'Schema application complete!'
SELECT count(*) as tables_created FROM information_schema.tables WHERE table_schema = 'public';