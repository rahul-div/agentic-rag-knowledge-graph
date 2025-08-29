# Multi-Tenant Local Path: Dual Storage Architecture

## 🎯 **Core Principle: Industry-Standard SaaS Multi-Tenancy**

Transform your Local Path: Dual Storage RAG system into a **production-ready multi-tenant platform** where each client has complete data isolation while sharing infrastructure for cost efficiency.

**Architecture Pattern**: Shared Database, Row-Level Tenant Isolation (Used by Supabase, PlanetScale, Auth0)

## 🏗️ **System Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATIONS                      │
├─────────────────────────────────────────────────────────────┤
│  Tenant A    │  Tenant B    │  Tenant C    │  Tenant N      │
│  (client_a)  │  (client_b)  │  (client_c)  │  (client_n)    │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬─────────┘
       │              │              │              │
       └──────────────┼──────────────┼──────────────┘
                      │              │
    ┌─────────────────┴──────────────┴─────────────────┐
    │           JWT AUTHENTICATION LAYER                │
    │   - Tenant ID validation                         │
    │   - User permissions                             │
    │   - Session management                           │
    └─────────────────┬────────────────────────────────┘
                      │
    ┌─────────────────┴─────────────────┐
    │      FASTAPI APPLICATION          │
    │  - Tenant-aware endpoints         │
    │  - Request validation             │
    │  - Tool routing                   │
    └─────────────────┬─────────────────┘
                      │
    ┌─────────────────┴─────────────────┐
    │    PYDANTIC AI AGENT LAYER        │
    │  - local_dual_search (default)    │
    │  - Tenant context propagation     │
    │  - Tool execution isolation       │
    └─────────────────┬─────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
┌────────▼─────────┐     ┌─────────▼──────────┐
│   NEON POSTGRESQL │     │    NEO4J + GRAPHITI │
│   + PGVECTOR      │     │                    │
│                   │     │                    │
│ ┌───────────────┐ │     │ ┌────────────────┐ │
│ │ documents     │ │     │ │ entities       │ │
│ │ - tenant_id   │ │     │ │ - tenant_id    │ │
│ │ - id          │ │     │ │ - properties   │ │
│ │ - content     │ │     │ │                │ │
│ └───────────────┘ │     │ └────────────────┘ │
│                   │     │                    │
│ ┌───────────────┐ │     │ ┌────────────────┐ │
│ │ chunks        │ │     │ │ relationships  │ │
│ │ - tenant_id   │ │     │ │ - tenant_id    │ │
│ │ - document_id │ │     │ │ - source/target│ │
│ │ - embedding   │ │     │ │                │ │
│ │ - content     │ │     │ │                │ │
│ └───────────────┘ │     │ └────────────────┘ │
└───────────────────┘     └────────────────────┘
```

## 🔐 **Tenant Isolation Strategy**

### **1. Database-Level Isolation (PostgreSQL)**
- **Row-Level Security (RLS)**: Every table has `tenant_id` column
- **Index Optimization**: Composite indexes on `(tenant_id, *)` 
- **Vector Search Isolation**: Custom functions with tenant filtering
- **Query Performance**: Tenant-first index design

### **2. Graph-Level Isolation (Neo4j + Graphiti)**
- **Node Properties**: All entities tagged with `tenant_id`
- **Relationship Properties**: All relationships tagged with `tenant_id`
- **Cypher Filtering**: All queries include tenant context
- **Performance Optimization**: Tenant-based graph partitioning

### **3. Application-Level Isolation**
- **JWT Token Claims**: Tenant ID embedded in authentication
- **Tool Context**: All AI tools receive tenant context
- **Session Management**: Sessions linked to tenant
- **Request Validation**: Multi-layer tenant verification

## 📊 **Data Model Design**

### **PostgreSQL Schema (Tenant-Aware)**
```sql
-- Core tenant table
CREATE TABLE tenants (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    
    -- Resource limits for each tenant
    max_documents INTEGER DEFAULT 1000,
    max_storage_mb INTEGER DEFAULT 500,
    
    CONSTRAINT valid_status CHECK (status IN ('active', 'suspended', 'deleted'))
);

-- Documents with tenant isolation
CREATE TABLE documents (
    id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(id),
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chunks with tenant isolation + vector embeddings
CREATE TABLE chunks (
    id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(id),
    document_id VARCHAR(50) NOT NULL REFERENCES documents(id),
    content TEXT NOT NULL,
    embedding VECTOR(768),  -- OpenAI/Gemini embedding dimension
    chunk_index INTEGER NOT NULL,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions with tenant context
CREATE TABLE sessions (
    id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(id),
    user_id VARCHAR(100) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance indexes (tenant-first design)
CREATE INDEX CONCURRENTLY idx_documents_tenant_id ON documents(tenant_id);
CREATE INDEX CONCURRENTLY idx_chunks_tenant_embedding ON chunks(tenant_id, embedding) USING ivfflat;
CREATE INDEX CONCURRENTLY idx_chunks_tenant_document ON chunks(tenant_id, document_id);
CREATE INDEX CONCURRENTLY idx_sessions_tenant_user ON sessions(tenant_id, user_id);
```

### **Neo4j Schema (Tenant-Aware)**
```cypher
// Constraint for tenant isolation
CREATE CONSTRAINT tenant_entity_constraint IF NOT EXISTS
FOR (n:Entity) REQUIRE n.tenant_id IS NOT NULL;

CREATE CONSTRAINT tenant_relationship_constraint IF NOT EXISTS
FOR ()-[r:RELATES_TO]-() REQUIRE r.tenant_id IS NOT NULL;

// Index for performance
CREATE INDEX tenant_entity_index IF NOT EXISTS
FOR (n:Entity) ON (n.tenant_id);

// Example entity with tenant tagging
MERGE (e:Entity {
    name: "Project Alpha",
    type: "project",
    tenant_id: "client_abc",
    created_at: datetime(),
    properties: {
        status: "active",
        priority: "high"
    }
})

// Example relationship with tenant tagging  
MATCH (a:Entity {tenant_id: "client_abc", name: "Project Alpha"})
MATCH (b:Entity {tenant_id: "client_abc", name: "Team Lead"})
MERGE (a)-[r:MANAGED_BY {
    tenant_id: "client_abc",
    relationship_type: "management",
    created_at: datetime()
}]->(b)
```

## 🛠️ **Implementation Architecture**

### **Tenant Management Layer**
- **Tenant Registry**: Central tenant configuration
- **Resource Limits**: Per-tenant quotas and limits
- **Billing Integration**: Usage tracking and metering
- **Health Monitoring**: Per-tenant system health

### **Authentication & Authorization**
- **JWT with Tenant Claims**: Secure tenant context
- **API Key Management**: Tenant-specific API keys
- **Permission Matrix**: Granular access control
- **Session Isolation**: Tenant-aware sessions

### **AI Agent Integration**
- **Context Propagation**: Tenant ID flows through all operations
- **Tool Isolation**: All tools respect tenant boundaries
- **Search Synthesis**: Intelligent local dual storage queries
- **Response Attribution**: Source citations with tenant validation

## 🔄 **Local Dual Search Workflow**

```python
# Tenant-aware local dual search process
async def local_dual_search_tenant(query: str, tenant_id: str, limit: int = 10):
    """
    SMART Local Path: Dual Storage search with tenant isolation
    
    Workflow:
    1. Validate tenant access
    2. Parallel vector + graph search within tenant boundary
    3. Intelligent result synthesis
    4. Source attribution with tenant validation
    """
    
    # Step 1: Tenant validation
    tenant = await validate_tenant(tenant_id)
    
    # Step 2: Parallel search execution
    vector_task = vector_search_tenant(query, tenant_id, limit)
    graph_task = graph_search_tenant(query, tenant_id, limit)
    
    vector_results, graph_results = await asyncio.gather(vector_task, graph_task)
    
    # Step 3: Intelligent synthesis
    synthesized = await synthesize_results(vector_results, graph_results, tenant_id)
    
    return synthesized
```

## 🚀 **Deployment Benefits**

### **Cost Efficiency**
- **Shared Infrastructure**: One database cluster serves all tenants
- **Resource Optimization**: Dynamic scaling based on aggregate usage
- **Maintenance Reduction**: Single codebase, unified operations

### **Scalability**
- **Horizontal Scaling**: Add tenants without infrastructure changes
- **Performance Isolation**: Tenant resource limits prevent noisy neighbors
- **Geographic Distribution**: Tenant data can be geo-located

### **Security**
- **Complete Data Isolation**: Zero cross-tenant data leakage
- **Audit Trail**: All operations logged with tenant context
- **Compliance Ready**: SOC2, GDPR, HIPAA compatible architecture

## 📈 **Growth Path**

### **Phase 1**: Single-tenant to multi-tenant migration
### **Phase 2**: Advanced tenant features (custom models, specialized tools)  
### **Phase 3**: Enterprise features (SSO, advanced security, SLA guarantees)
### **Phase 4**: Platform scaling (thousands of tenants, global deployment)

This architecture provides the foundation for a **production-ready, enterprise-grade** multi-tenant RAG platform focused exclusively on Local Path: Dual Storage efficiency and security.