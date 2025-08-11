-- PostgreSQL initialization script for agent orchestration system
-- Optimized for high-concurrency document processing

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector"; -- For embedding vectors (if using pgvector)

-- Create schemas
CREATE SCHEMA IF NOT EXISTS documents;
CREATE SCHEMA IF NOT EXISTS analysis;
CREATE SCHEMA IF NOT EXISTS agents;

-- Documents table - stores original document content
CREATE TABLE documents.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 hash for deduplication
    size_bytes INTEGER NOT NULL,
    mime_type VARCHAR(100),
    upload_timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    
    -- Indexes for performance
    CONSTRAINT documents_content_hash_unique UNIQUE(content_hash)
);

-- Document chunks for embedding (if using vector search)
CREATE TABLE documents.document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents.documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- Adjust dimension based on embedding model
    metadata JSONB,
    
    CONSTRAINT document_chunks_unique UNIQUE(document_id, chunk_index)
);

-- Analysis results from agent orchestration
CREATE TABLE analysis.document_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents.documents(id) ON DELETE CASCADE,
    task_id VARCHAR(255) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL, -- 'orchestrated', 'single_agent', etc.
    
    -- Analysis results
    extracted_metadata JSONB NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    requires_human_review BOOLEAN DEFAULT FALSE,
    
    -- Processing information
    processing_start_time TIMESTAMPTZ NOT NULL,
    processing_end_time TIMESTAMPTZ NOT NULL,
    processing_duration_ms INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (processing_end_time - processing_start_time)) * 1000
    ) STORED,
    
    -- Agent information
    agents_used JSONB, -- Array of agent names that participated
    successful_agents INTEGER NOT NULL DEFAULT 0,
    total_agents INTEGER NOT NULL DEFAULT 0,
    
    -- Business metadata
    document_type VARCHAR(50),
    contract_value DECIMAL(15,2),
    parties JSONB,
    key_dates JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Individual agent results for detailed tracking
CREATE TABLE agents.agent_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analysis.document_analysis(id) ON DELETE CASCADE,
    task_id VARCHAR(255) NOT NULL,
    
    -- Agent information
    agent_name VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL, -- 'extraction', 'validation', 'supervision'
    specialization VARCHAR(50), -- 'classification', 'parties', 'financial', etc.
    
    -- Result data
    status VARCHAR(20) NOT NULL, -- 'completed', 'failed', 'timeout'
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    data JSONB,
    error_message TEXT,
    warnings JSONB,
    
    -- Performance metrics
    processing_time_ms INTEGER NOT NULL,
    memory_usage_mb INTEGER,
    
    -- Metadata
    agent_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Human review queue for documents requiring attention
CREATE TABLE analysis.review_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents.documents(id),
    analysis_id UUID NOT NULL REFERENCES analysis.document_analysis(id),
    
    -- Review information
    priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'critical'
    reason VARCHAR(100) NOT NULL, -- Why review is needed
    assigned_to VARCHAR(100), -- User or team assigned
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'rejected'
    review_notes TEXT,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance monitoring table
CREATE TABLE agents.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Time period
    metric_date DATE NOT NULL,
    hour_of_day INTEGER CHECK (hour_of_day >= 0 AND hour_of_day <= 23),
    
    -- Metrics
    total_documents_processed INTEGER DEFAULT 0,
    total_processing_time_ms BIGINT DEFAULT 0,
    average_processing_time_ms INTEGER DEFAULT 0,
    
    -- Success rates
    successful_analyses INTEGER DEFAULT 0,
    failed_analyses INTEGER DEFAULT 0,
    timeout_analyses INTEGER DEFAULT 0,
    
    -- Agent performance
    agent_success_rates JSONB, -- Per-agent success rates
    average_confidence DECIMAL(3,2),
    
    -- Review statistics
    documents_requiring_review INTEGER DEFAULT 0,
    high_value_contracts INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT performance_metrics_unique UNIQUE(metric_date, hour_of_day)
);

-- Create indexes for optimal performance
CREATE INDEX idx_documents_upload_timestamp ON documents.documents(upload_timestamp);
CREATE INDEX idx_documents_content_hash ON documents.documents(content_hash);
CREATE INDEX idx_documents_metadata ON documents.documents USING GIN(metadata);

CREATE INDEX idx_document_chunks_document_id ON documents.document_chunks(document_id);
CREATE INDEX idx_document_chunks_embedding ON documents.document_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX idx_analysis_document_id ON analysis.document_analysis(document_id);
CREATE INDEX idx_analysis_task_id ON analysis.document_analysis(task_id);
CREATE INDEX idx_analysis_confidence_score ON analysis.document_analysis(confidence_score);
CREATE INDEX idx_analysis_requires_review ON analysis.document_analysis(requires_human_review);
CREATE INDEX idx_analysis_document_type ON analysis.document_analysis(document_type);
CREATE INDEX idx_analysis_created_at ON analysis.document_analysis(created_at);
CREATE INDEX idx_analysis_metadata ON analysis.document_analysis USING GIN(extracted_metadata);

CREATE INDEX idx_agent_results_analysis_id ON agents.agent_results(analysis_id);
CREATE INDEX idx_agent_results_agent_name ON agents.agent_results(agent_name);
CREATE INDEX idx_agent_results_status ON agents.agent_results(status);
CREATE INDEX idx_agent_results_processing_time ON agents.agent_results(processing_time_ms);

CREATE INDEX idx_review_queue_status ON analysis.review_queue(status);
CREATE INDEX idx_review_queue_priority ON analysis.review_queue(priority);
CREATE INDEX idx_review_queue_assigned_to ON analysis.review_queue(assigned_to);
CREATE INDEX idx_review_queue_created_at ON analysis.review_queue(created_at);

CREATE INDEX idx_performance_metrics_date ON agents.performance_metrics(metric_date);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_document_analysis_updated_at 
    BEFORE UPDATE ON analysis.document_analysis 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_review_queue_updated_at 
    BEFORE UPDATE ON analysis.review_queue 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE VIEW analysis.document_analysis_summary AS
SELECT 
    da.id,
    da.document_id,
    d.filename,
    da.confidence_score,
    da.requires_human_review,
    da.document_type,
    da.contract_value,
    da.processing_duration_ms,
    da.successful_agents,
    da.total_agents,
    CASE 
        WHEN da.successful_agents = da.total_agents THEN 'excellent'
        WHEN da.successful_agents >= da.total_agents * 0.75 THEN 'good'
        WHEN da.successful_agents >= da.total_agents * 0.5 THEN 'partial'
        ELSE 'poor'
    END as analysis_quality,
    da.created_at
FROM analysis.document_analysis da
JOIN documents.documents d ON da.document_id = d.id;

CREATE VIEW agents.agent_performance_summary AS
SELECT 
    agent_name,
    COUNT(*) as total_executions,
    AVG(confidence) as avg_confidence,
    AVG(processing_time_ms) as avg_processing_time_ms,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
    COUNT(CASE WHEN status = 'timeout' THEN 1 END) as timeout_executions,
    ROUND(
        COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as success_rate_percent
FROM agents.agent_results
GROUP BY agent_name;

-- Insert initial performance tracking record
INSERT INTO agents.performance_metrics (metric_date, hour_of_day) 
VALUES (CURRENT_DATE, EXTRACT(HOUR FROM NOW()));

-- Grant permissions (adjust as needed for your security requirements)
GRANT USAGE ON SCHEMA documents TO cognee_user;
GRANT USAGE ON SCHEMA analysis TO cognee_user;
GRANT USAGE ON SCHEMA agents TO cognee_user;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA documents TO cognee_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analysis TO cognee_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA agents TO cognee_user;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA documents TO cognee_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analysis TO cognee_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA agents TO cognee_user;

-- Analysis complete message
SELECT 'PostgreSQL agent orchestration database initialized successfully!' as status;