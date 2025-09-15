# Multi-Tenant RAG System: Complete Implementation Plan

## Executive Summary

This plan builds a **simplified multi-tenant RAG prototype** focused on core functionality: isolated data ingestion and search per tenant. We prioritize rapid deployment and testing over complex authentication systems.

## Critical Design Decisions

### Simplified Authentication Strategy (Prototype)
- **No authentication initially** - tenant identification via simple tenant_id parameter
- **Focus on data isolation** rather than security
- **Quick API testing** with tenant-specific endpoints

### Data Isolation Strategy
- **Neon project-per-tenant** for vector data (pgvector databases)
- **Neo4j namespace isolation** for knowledge graphs (group_id based)
- **Simple tenant registry** (in-memory or basic database)
- **Complete tenant data isolation** through proper query filtering

## Phase 1: Core Infrastructure (Week 1)

### 1.1 Database Architecture

#### Simplified Tenant Registry (PostgreSQL)
```sql
-- Minimal tenant management for prototype
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    neon_project_id VARCHAR(255) UNIQUE,
    neon_database_url TEXT,
    neo4j_group_id VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for performance
CREATE INDEX idx_tenants_slug ON tenants(slug);
```

#### Tenant Database Schema (per Neon project)
```sql
-- Each tenant gets their own database with this schema
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Document storage
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    source VARCHAR(1000) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) UNIQUE NOT NULL, -- Prevent duplicates
    metadata JSONB DEFAULT '{}',
    document_type VARCHAR(100),
    file_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector chunks with embeddings
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 dimensions
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- Vector similarity search index
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Full-text search index
CREATE INDEX idx_chunks_content_fts ON document_chunks USING gin(to_tsvector('english', content));
CREATE INDEX idx_documents_content_fts ON documents USING gin(to_tsvector('english', content));
```

### 1.2 Environment Configuration

```bash
# Core Database Configuration
TENANT_REGISTRY_URL=postgresql://user:pass@host:port/tenant_registry
NEON_API_KEY=neon_api_key_here
NEON_DEFAULT_REGION=aws-us-east-1

# Knowledge Graph Configuration  
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# AI/ML Configuration
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_key # Alternative to Google
DEFAULT_EMBEDDING_MODEL=text-embedding-ada-002

# Development/Testing
DEBUG_MODE=true
LOG_LEVEL=INFO
```

### 1.3 Technology Stack

#### Core Dependencies
```python
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1          # Database migrations
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4   # Password hashing
python-multipart==0.0.6  # File uploads

# Multi-tenant & RAG
neo4j==5.14.1
graphiti-core==0.3.0
openai==1.3.7
google-generativeai==0.3.1
sentence-transformers==2.2.2
langchain==0.0.335

# CLI & Development
typer==0.9.0            # Better CLI than click
rich==13.7.0            # Terminal formatting
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2           # Testing HTTP client
```

## Phase 2: Core Services Implementation (Week 1)

### 2.1 Simplified Tenant Service

```python
# File: services/tenant_service.py
class TenantService:
    """
    Simple tenant management for prototype:
    1. Create/manage tenants in registry
    2. Neon project creation/deletion
    3. Neo4j namespace setup
    """
    
    async def create_tenant(self, tenant_name: str, tenant_slug: str) -> TenantResponse:
        """
        1. Create Neon project
        2. Set up database schema
        3. Create Neo4j namespace
        4. Register in tenant registry
        """
        pass
    
    async def get_tenant_config(self, tenant_slug: str) -> TenantConfig:
        """Get tenant database connections for isolation."""
        pass
```

### 2.2 Document Ingestion Service

```python
# File: services/ingestion_service.py
class DocumentIngestionService:
    """
    Tenant-isolated document processing:
    1. Tenant validation
    2. Content extraction
    3. Chunking and embedding
    4. Vector storage (tenant database)
    5. Knowledge graph extraction (tenant namespace)
    """
    
    async def ingest_document(
        self, 
        tenant_slug: str,
        document: DocumentInput
    ) -> IngestionResult:
        """Process and store document with full tenant isolation."""
        pass
```

### 2.3 Search Service

```python
# File: services/search_service.py
class SearchService:
    """
    Tenant-isolated search and query:
    1. Vector similarity search
    2. Knowledge graph queries
    3. Hybrid RAG responses
    """
    
    async def vector_search(self, tenant_slug: str, query: str) -> SearchResult:
        """Search tenant's vector database."""
        pass
    
    async def graph_search(self, tenant_slug: str, query: str) -> SearchResult:
        """Search tenant's knowledge graph."""
        pass
    
    async def hybrid_query(self, tenant_slug: str, query: str) -> RAGResult:
        """Combined vector + graph RAG response."""
        pass
```

## Phase 3: API Endpoints (Week 1)

### 3.1 Tenant Management Endpoints

```python
# Simplified tenant management (no auth)
POST /tenants                  # Create new tenant
GET  /tenants                  # List all tenants
GET  /tenants/{slug}           # Get tenant details
```

### 3.2 Document Ingestion Endpoints

```python
# Document Management (tenant-isolated)
POST /tenants/{slug}/documents       # Upload document to tenant
GET  /tenants/{slug}/documents       # List tenant documents
DELETE /tenants/{slug}/documents/{id} # Delete tenant document
```

### 3.3 Search & Query Endpoints

```python
# RAG Operations (tenant-isolated)
POST /tenants/{slug}/query           # Hybrid RAG query
POST /tenants/{slug}/search/vector   # Vector similarity search
POST /tenants/{slug}/search/graph    # Knowledge graph search
GET  /tenants/{slug}/search/history  # Query history
```

## Phase 4: CLI Implementation (Week 1)

### 4.1 CLI Command Structure

```bash
# Tenant Management
mt-rag tenant create --name "Acme Corp" --slug "acme"
mt-rag tenant list
mt-rag tenant info --slug acme

# Document Operations
mt-rag docs upload --tenant acme --file document.pdf --title "Company Policy"
mt-rag docs upload --tenant acme --directory ./company-docs/
mt-rag docs list --tenant acme
mt-rag docs delete --tenant acme --id doc-uuid

# RAG Queries
mt-rag query --tenant acme "What is our vacation policy?"
mt-rag search --tenant acme --type vector "machine learning"
mt-rag search --tenant acme --type graph "CEO relationships"
mt-rag chat --tenant acme  # Interactive mode
```

### 4.2 CLI Configuration

```yaml
# ~/.mt-rag/config.yaml
current_tenant: acme
api_url: http://localhost:8000

tenants:
  acme:
    name: "Acme Corp"
  
  demo:
    name: "Demo Company"
```

## Phase 5: EC2 Deployment & Testing (Week 2)

### 5.1 Simple Deployment Architecture

```yaml
# Docker Compose for EC2 deployment
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TENANT_REGISTRY_URL=postgresql://postgres:password@postgres:5432/tenant_registry
      - NEO4J_URI=bolt://neo4j:7687
      - NEON_API_KEY=${NEON_API_KEY}
    depends_on:
      - postgres
      - neo4j
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: tenant_registry
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  neo4j:
    image: neo4j:5.14
    environment:
      NEO4J_AUTH: neo4j/password
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

volumes:
  postgres_data:
  neo4j_data:
```

### 5.2 Testing Strategy

```python
# Test with 2 tenants: "acme" and "demo"
# 1. Create both tenants via API
# 2. Upload different documents to each tenant
# 3. Verify complete isolation in searches
# 4. Test via CLI commands
```

## Success Criteria & Validation

### Technical Validation
- [ ] Complete tenant isolation (no data leaks)
- [ ] Secure authentication (API keys + JWT)
- [ ] Scalable architecture (handles 100+ tenants)
- [ ] Proper error handling and logging
- [ ] Comprehensive test coverage (>90%)

### Business Validation
- [ ] Easy tenant onboarding (<5 minutes)
- [ ] Simple document ingestion (drag-and-drop)
- [ ] Fast, accurate RAG responses (<2 seconds)
- [ ] Intuitive CLI interface
- [ ] Clear pricing model per tenant

## Critical Questions to Answer

1. **Who can create tenants?**
   - Admin-only tenant creation (validated).
2. **What's the user onboarding flow?**
   - Single admin per tenant (validated).
   - Single user per tenant initially (validated).
3. **How do you handle billing?**
   - All tenants will be free (validated).
4. **What are the resource limits?**
   - No resource limitations as of now (validated).
5. **What is the deployment target?**
   - Deployment on Amazon EC2 (validated).

This plan avoids "prototype syndrome" and builds a system that can grow into production. Each phase delivers working functionality while maintaining architectural integrity.
