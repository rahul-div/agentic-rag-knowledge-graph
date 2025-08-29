-- Multi-Tenant PostgreSQL Schema with Row-Level Security (RLS)
-- Based on Neon's official multi-tenancy patterns
-- https://neon.tech/docs/guides/multi-tenancy

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core tenants table
CREATE TABLE tenants (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    max_documents INTEGER DEFAULT 1000,
    max_storage_mb INTEGER DEFAULT 500,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tenant-aware documents table with RLS
CREATE TABLE documents (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(id),
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on documents
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their tenant's documents
CREATE POLICY tenant_isolation_policy ON documents
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Chunks table with vector embeddings and RLS
CREATE TABLE chunks (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(id),
    document_id VARCHAR(50) NOT NULL REFERENCES documents(id),
    content TEXT NOT NULL,
    embedding VECTOR(768),
    chunk_index INTEGER NOT NULL,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on chunks
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their tenant's chunks
CREATE POLICY tenant_chunks_policy ON chunks
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Sessions table for conversation tracking
CREATE TABLE sessions (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(id),
    user_id VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_sessions_policy ON sessions
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Messages table for conversation history
CREATE TABLE messages (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(id),
    session_id VARCHAR(50) NOT NULL REFERENCES sessions(id),
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_messages_policy ON messages
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Tenant-aware vector search function (official Neon pattern)
CREATE OR REPLACE FUNCTION match_chunks_tenant(
    query_embedding VECTOR(768),
    filter_tenant_id VARCHAR(50),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    chunk_id VARCHAR(50),
    document_id VARCHAR(50),
    content TEXT,
    similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    tenant_id VARCHAR(50)
)
LANGUAGE sql STABLE
AS $$
    SELECT 
        c.id as chunk_id,
        c.document_id,
        c.content,
        1 - (c.embedding <=> query_embedding) as similarity,
        c.metadata,
        d.title as document_title,
        c.tenant_id
    FROM chunks c
    INNER JOIN documents d ON c.document_id = d.id 
    WHERE c.tenant_id = filter_tenant_id
    AND d.tenant_id = filter_tenant_id
    AND c.embedding IS NOT NULL
    AND 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Helper function to set tenant context for RLS
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_id_param VARCHAR(50))
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', tenant_id_param, true);
END;
$$ LANGUAGE plpgsql;

-- Helper function to get current tenant context
CREATE OR REPLACE FUNCTION get_tenant_context()
RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN current_setting('app.current_tenant_id', true);
END;
$$ LANGUAGE plpgsql;

-- Indexes for performance
CREATE INDEX idx_documents_tenant_id ON documents(tenant_id);
CREATE INDEX idx_documents_tenant_created ON documents(tenant_id, created_at);
CREATE INDEX idx_chunks_tenant_id ON chunks(tenant_id);
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_tenant_document ON chunks(tenant_id, document_id);
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_sessions_tenant_id ON sessions(tenant_id);
CREATE INDEX idx_sessions_tenant_activity ON sessions(tenant_id, last_activity);
CREATE INDEX idx_messages_tenant_id ON messages(tenant_id);
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_tenant_session ON messages(tenant_id, session_id);

-- Storage quotas trigger function
CREATE OR REPLACE FUNCTION check_tenant_storage_quota()
RETURNS TRIGGER AS $$
DECLARE
    tenant_max_docs INTEGER;
    current_doc_count INTEGER;
    tenant_max_storage INTEGER;
    current_storage_mb FLOAT;
BEGIN
    -- Get tenant limits
    SELECT max_documents, max_storage_mb 
    INTO tenant_max_docs, tenant_max_storage
    FROM tenants 
    WHERE id = NEW.tenant_id;
    
    -- Check document count limit
    SELECT COUNT(*) 
    INTO current_doc_count
    FROM documents 
    WHERE tenant_id = NEW.tenant_id;
    
    IF current_doc_count >= tenant_max_docs THEN
        RAISE EXCEPTION 'Tenant % has reached document limit of %', NEW.tenant_id, tenant_max_docs;
    END IF;
    
    -- Check storage limit (approximate based on content length)
    SELECT COALESCE(SUM(LENGTH(content))::FLOAT / (1024 * 1024), 0)
    INTO current_storage_mb
    FROM documents 
    WHERE tenant_id = NEW.tenant_id;
    
    IF current_storage_mb >= tenant_max_storage THEN
        RAISE EXCEPTION 'Tenant % has reached storage limit of % MB', NEW.tenant_id, tenant_max_storage;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply quota trigger to documents
CREATE TRIGGER tenant_storage_quota_trigger
    BEFORE INSERT ON documents
    FOR EACH ROW
    EXECUTE FUNCTION check_tenant_storage_quota();

-- Tenant statistics view
CREATE VIEW tenant_stats AS
SELECT 
    t.id as tenant_id,
    t.name as tenant_name,
    t.status,
    COUNT(DISTINCT d.id) as document_count,
    COUNT(DISTINCT c.id) as chunk_count,
    ROUND(COALESCE(SUM(LENGTH(d.content))::FLOAT / (1024 * 1024), 0), 2) as storage_mb_used,
    t.max_documents,
    t.max_storage_mb,
    ROUND((COUNT(DISTINCT d.id)::FLOAT / t.max_documents * 100), 2) as doc_usage_percent,
    ROUND((COALESCE(SUM(LENGTH(d.content))::FLOAT / (1024 * 1024), 0) / t.max_storage_mb * 100), 2) as storage_usage_percent,
    COUNT(DISTINCT s.id) as active_sessions,
    t.created_at as tenant_created_at
FROM tenants t
LEFT JOIN documents d ON t.id = d.tenant_id
LEFT JOIN chunks c ON d.id = c.document_id
LEFT JOIN sessions s ON t.id = s.tenant_id AND s.last_activity > NOW() - INTERVAL '24 hours'
GROUP BY t.id, t.name, t.status, t.max_documents, t.max_storage_mb, t.created_at
ORDER BY t.created_at DESC;

-- Sample data for testing (remove in production)
-- INSERT INTO tenants (id, name, email, max_documents, max_storage_mb) VALUES
-- ('tenant_demo', 'Demo Corporation', 'demo@example.com', 500, 250),
-- ('tenant_test', 'Test Company', 'test@example.com', 1000, 500);
