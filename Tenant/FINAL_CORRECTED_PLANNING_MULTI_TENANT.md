# CORRECTED Multi-Tenant RAG System - Official Neon & Graphiti Best Practices

## 🚨 **ARCHITECTURE CORRECTION COMPLETE**

This document provides the **CORRECTED** multi-tenant implementation following **official Neon and Graphiti best practices** for production-ready scalability.

---

## Executive Summary

### 🎯 **Mission Statement**
Transform the existing single-tenant RAG system into a production-ready multi-tenant SaaS platform using:
- **Neon PostgreSQL**: Project-per-tenant architecture (official recommendation)
- **Graphiti Neo4j**: Shared instance with group_id namespacing (official approach)
- **Complete tenant isolation** with operational simplicity

---

## Current Architecture Analysis

### 🏗️ **Current System (Single-Tenant RAG)**

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                              │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │   FastAPI       │          │   Session Mgmt     │      │
│  │   Endpoints     │          │   Streaming SSE    │      │
│  └────────┬────────┘          └────────────────────┘      │
├───────────┴─────────────────────────────────────────────────┤
│                    Pydantic AI Agent                       │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │  Hybrid Agent   │◄────────►│   10-Tool Arsenal  │      │
│  │  (Gemini/GPT)   │          │  - vector_search   │      │
│  └─────────────────┘          │  - graph_search    │      │
│                                │  - comprehensive   │      │
│                                │  - onyx_search     │      │
│                                │  - entity_rels     │      │
│                                └────────────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                  Single-Tenant Data Layer                   │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │   Neon PG       │          │    Neo4j + Graphiti│      │
│  │   + pgvector    │          │    Knowledge Graph │      │
│  │   Vector Store  │          │    Global Namespace│      │
│  └─────────────────┘          └────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

**Current Tech Stack:**
- **AI Framework:** Pydantic AI with intelligent tool selection
- **LLM Models:** Gemini 2.0 Flash / OpenAI GPT (configurable)
- **Vector DB:** Neon PostgreSQL with pgvector (768/1536-dimensional embeddings)
- **Knowledge Graph:** Neo4j + Graphiti (temporal, entity relationships)
- **API Framework:** FastAPI with Server-Sent Events streaming
- **Database ORM:** Raw SQL with asyncpg connection pooling
- **Session Management:** UUID-based with conversation history

---

## Target Architecture: Multi-Tenant RAG System

### 🏢 **CORRECTED Multi-Tenant Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                  Multi-Tenant API Layer                     │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │   FastAPI       │          │   Tenant Auth      │      │
│  │   + JWT Auth    │          │   Context Injection│      │
│  └────────┬────────┘          └────────────────────┘      │
├───────────┴─────────────────────────────────────────────────┤
│              Enhanced Pydantic AI Agent                    │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │  Tenant-Aware   │◄────────►│   Same 10+ Tools   │      │
│  │  Agent          │          │   + Tenant Context │      │
│  │  (Same LLMs)    │          │   Injection        │      │
│  └─────────────────┘          └────────────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                Multi-Tenant Data Layer                     │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │   Neon Projects │          │    Neo4j + Graphiti│      │
│  │   (Per-Tenant)  │          │    + group_id      │      │
│  │   Isolated DBs  │          │    Namespacing     │      │
│  └─────────────────┘          └────────────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                Tenant Management Layer                     │
│  ┌─────────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │   Catalog DB    │  │   Per-Tenant  │  │  Resource    │ │
│  │   Tenant        │  │   Database    │  │  Management  │ │
│  │   Metadata      │  │   Isolation   │  │  & Scaling   │ │
│  │   (Catalog DB)  │  │   Complete    │  │              │ │
│  └─────────────────┘  └───────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Strategy: Project-Per-Tenant

### **Phase 1: Catalog Database & Project-Per-Tenant Setup (Week 1-2)**

#### **Project-Per-Tenant Database Architecture**

- **Objective:** Implement project-per-tenant architecture following official Neon best practices
- **Approach:** One Neon project (isolated database) per tenant with catalog database for orchestration
- **Key Benefits:**
  - Complete database isolation (no RLS complexity)
  - Linear scaling (unlimited tenants)
  - Cost optimization (scale-to-zero per tenant)
  - Operational simplicity

#### **Implementation Components:**

**1. Catalog Database (Control Plane)**
```sql
-- Main catalog database for tenant management
CREATE TABLE tenant_projects (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_name VARCHAR(255) NOT NULL,
    tenant_email VARCHAR(255) UNIQUE NOT NULL,
    neon_project_id VARCHAR(100) NOT NULL UNIQUE,
    neon_database_url TEXT NOT NULL,
    region VARCHAR(50) NOT NULL DEFAULT 'aws-us-east-1',
    status VARCHAR(20) DEFAULT 'active',
    plan VARCHAR(50) DEFAULT 'basic',
    max_documents INTEGER DEFAULT 1000,
    max_storage_mb INTEGER DEFAULT 500,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tenant configuration and metadata
CREATE TABLE tenant_config (
    tenant_id UUID PRIMARY KEY REFERENCES tenant_projects(tenant_id),
    settings JSONB DEFAULT '{}',
    feature_flags JSONB DEFAULT '{}',
    api_limits JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tenant usage tracking for billing
CREATE TABLE tenant_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant_projects(tenant_id),
    metric_name VARCHAR(50) NOT NULL,
    metric_value BIGINT NOT NULL,
    period_date DATE NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, metric_name, period_date)
);
```

**2. Per-Tenant Database Schema (Deployed to Each Tenant Project)**
```sql
-- Each tenant gets their own isolated database with complete schema
-- This is the SAME schema as current single-tenant, but per tenant

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents table (NO tenant_id - entire DB is for one tenant)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chunks with vector embeddings
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(768),
    chunk_index INTEGER NOT NULL,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions for conversation tracking
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

-- Messages for conversation history
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_messages_session ON messages(session_id, created_at);
CREATE INDEX idx_documents_created ON documents(created_at);

-- Vector search function (same as single-tenant)
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding VECTOR(768),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT 
        chunks.id,
        chunks.document_id,
        chunks.content,
        1 - (chunks.embedding <=> query_embedding) AS similarity
    FROM chunks
    WHERE 1 - (chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY chunks.embedding <=> query_embedding
    LIMIT match_count;
$$;
```

**3. Tenant Project Management Service**
```python
from neon_api import NeonAPI

class TenantProjectManager:
    """Manages Neon projects for tenant isolation"""
    
    def __init__(self, neon_api_key: str):
        self.neon_api = NeonAPI(neon_api_key)
        
    async def create_tenant_project(self, tenant_name: str, tenant_email: str):
        """Create isolated Neon project for tenant"""
        project = await self.neon_api.create_project(
            name=f"rag-tenant-{tenant_name.lower().replace(' ', '-')}",
            pg_version=16,
            region_id="aws-us-east-1"
        )
        
        # Deploy schema to new project
        await self.deploy_tenant_schema(project.database_url)
        
        return {
            'tenant_id': str(uuid.uuid4()),
            'project_id': project.id,
            'database_url': project.database_url,
            'tenant_name': tenant_name,
            'tenant_email': tenant_email
        }
        
    async def deploy_tenant_schema(self, database_url: str):
        """Deploy complete RAG schema to tenant database"""
        # Deploy the same schema as single-tenant to isolated DB
        async with asyncpg.connect(database_url) as conn:
            await conn.execute(TENANT_SCHEMA_SQL)
```

---

### **Phase 2: Graphiti Multi-Tenancy with group_id (Week 2)**

#### **Shared Graphiti with Tenant Namespacing**

- **Objective:** Implement tenant isolation in Neo4j using Graphiti's group_id feature
- **Approach:** Single shared Neo4j instance with tenant namespacing via group_id
- **Official Pattern:** Per Graphiti documentation for multi-tenancy

```python
class TenantGraphitiClient:
    """
    Tenant-aware wrapper for Graphiti operations.
    Uses shared Graphiti instance with group_id namespacing for tenant isolation.
    """
    
    def __init__(self, shared_graphiti_client: Graphiti):
        """
        Initialize with shared Graphiti instance.
        
        Args:
            shared_graphiti_client: Single shared Graphiti instance for all tenants
        """
        self.graphiti = shared_graphiti_client
    
    async def add_episode_for_tenant(
        self, 
        tenant_id: str, 
        episode_body: str, 
        episode_id: Optional[str] = None
    ) -> str:
        """Add episode to tenant's namespace"""
        return await self.graphiti.add_episode(
            episode_body=episode_body,
            episode_id=episode_id,
            group_id=tenant_id  # ✅ Tenant isolation via group_id
        )
    
    async def search_for_tenant(
        self, 
        tenant_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search within tenant's namespace"""
        return await self.graphiti.search(
            query=query,
            group_id=tenant_id,  # ✅ Tenant isolation via group_id
            limit=limit
        )
    
    async def get_entity_relationships_for_tenant(
        self, 
        tenant_id: str, 
        entity_name: str, 
        relationship_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get entity relationships within tenant's namespace"""
        return await self.graphiti.get_entity_relationships(
            entity_name=entity_name,
            relationship_types=relationship_types,
            group_id=tenant_id  # ✅ Tenant isolation via group_id
        )
```

---

### **Phase 3: Multi-Tenant Application Layer (Week 3-4)**

#### **Tenant-Aware Agent Dependencies**

```python
@dataclass
class TenantAgentDependencies:
    """Dependencies injected per tenant"""
    tenant_id: UUID
    tenant_database: AsyncDatabase
    shared_graphiti: TenantGraphitiClient  # Shared Graphiti with tenant methods
    
    @classmethod
    async def create_for_tenant(
        cls, 
        tenant_id: UUID, 
        tenant_manager: TenantProjectManager,
        shared_graphiti_client: TenantGraphitiClient
    ) -> 'TenantAgentDependencies':
        # Get tenant-specific database connection
        db_url = await tenant_manager.get_tenant_database_url(tenant_id)
        tenant_db = AsyncDatabase(db_url)
        
        return cls(
            tenant_id=tenant_id,
            tenant_database=tenant_db,
            shared_graphiti=shared_graphiti_client  # Shared instance with namespacing
        )
```

#### **Enhanced Multi-Tenant Tools**

```python
# Vector search - uses tenant-specific database
async def vector_search_tool(
    input_data: VectorSearchInput, 
    deps: TenantAgentDependencies
) -> List[ChunkResult]:
    """Vector search within tenant's dedicated database"""
    
    # No tenant_id filtering needed - entire database is for this tenant
    query = """
        SELECT chunk_id, document_id, content, similarity
        FROM match_chunks($1, $2, $3)
    """
    
    results = await deps.tenant_database.fetch_all(
        query, input_data.embedding, input_data.threshold, input_data.limit
    )
    
    return [ChunkResult.from_row(row) for row in results]

# Graph search - uses shared Graphiti with tenant namespacing
async def graph_search_tool(
    input_data: GraphSearchInput,
    deps: TenantAgentDependencies
) -> List[GraphSearchResult]:
    """Graph search within tenant's namespace"""
    
    # Use shared Graphiti with tenant-aware method
    results = await deps.shared_graphiti.search_for_tenant(
        tenant_id=str(deps.tenant_id),
        query=input_data.query,
        limit=input_data.limit
    )
    
    return [GraphSearchResult.from_dict(r) for r in results]
```

#### **Multi-Tenant API Endpoints**

```python
class TenantAuthMiddleware:
    """Extract and validate tenant context from requests"""
    
    async def __call__(self, request: Request, call_next):
        # Extract API key from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(401, "Missing or invalid API key")
        
        api_key = auth_header.split(" ")[1]
        
        # Authenticate and get tenant ID
        tenant_id = await self.authenticate_tenant(api_key)
        
        # Add tenant context to request state
        request.state.tenant_id = tenant_id
        
        return await call_next(request)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    tenant_id: UUID = Depends(get_tenant_id)
) -> ChatResponse:
    """Chat endpoint with tenant isolation"""
    
    # Create tenant-specific agent dependencies
    deps = await TenantAgentDependencies.create_for_tenant(
        tenant_id, tenant_project_manager, shared_graphiti_client
    )
    
    # Same chat logic as before, but isolated per tenant
    agent = PydanticAIAgent(deps)
    response = await agent.chat(request.message)
    
    return ChatResponse(
        message=response,
        tenant_id=tenant_id,
        session_id=request.session_id
    )

# Tenant management endpoints
@app.post("/tenants", response_model=TenantResponse)
async def create_tenant_endpoint(request: CreateTenantRequest) -> TenantResponse:
    """Create new tenant with dedicated Neon project"""
    tenant_info = await tenant_project_manager.create_tenant_project(
        tenant_name=request.name,
        tenant_email=request.email
    )
    
    return TenantResponse(
        tenant_id=tenant_info['tenant_id'], 
        status="created",
        project_id=tenant_info['project_id']
    )
```

---

## Migration Strategy

### **Existing Data Migration**

1. **Create Default Tenant Project**
   ```python
   async def migrate_existing_data():
       # Create "Default Tenant" project
       default_tenant = await tenant_project_manager.create_tenant_project(
           tenant_name="Default Tenant",
           tenant_email="admin@company.com"
       )
       
       # Migrate existing single-tenant data to default tenant project
       await migrate_data_to_tenant_database(
           source_db_url=CURRENT_DATABASE_URL,
           target_db_url=default_tenant['database_url']
       )
       
       return default_tenant['tenant_id']
   ```

2. **Zero-Downtime Migration**
   - Deploy multi-tenant code alongside single-tenant
   - Route existing traffic to default tenant
   - Gradually onboard new tenants to isolated projects
   - Remove single-tenant infrastructure after validation

---

## Performance & Scaling Characteristics

### **Database Layer Performance**
- **Per-Tenant Scaling**: Each tenant's database scales independently
- **Cost Optimization**: Inactive tenants scale to zero automatically
- **No Cross-Tenant Interference**: Complete isolation prevents noisy neighbor issues
- **Connection Pooling**: Per-tenant connection pools for optimal resource usage

### **Graphiti Layer Performance**
- **Shared Instance Efficiency**: Single Neo4j instance reduces operational overhead
- **Tenant Namespacing**: group_id provides efficient logical isolation
- **Query Performance**: No impact from other tenants' data in queries
- **Memory Optimization**: Shared graph algorithms and caching

### **API Layer Scaling**
- **Stateless Design**: Same horizontal scaling as single-tenant
- **Tenant Context Injection**: Minimal overhead for tenant resolution
- **Tool Reusability**: All existing tools work with tenant context
- **Session Management**: Per-tenant session isolation

---

## Testing & Validation Strategy

### **Tenant Isolation Testing**

```python
async def test_complete_tenant_isolation():
    """Verify zero cross-tenant data leakage"""
    
    # Create two tenants with separate Neon projects
    tenant_a = await create_tenant("Tenant A", "a@test.com")
    tenant_b = await create_tenant("Tenant B", "b@test.com")
    
    # Add data to tenant A only
    await add_test_data(tenant_a, "Secret A Data")
    
    # Verify tenant B cannot access tenant A's data
    results = await search_tenant_data(tenant_b, "Secret A Data")
    assert len(results) == 0, "Data leaked between tenants!"
    
    # Verify different database URLs (complete isolation)
    tenant_a_url = await get_tenant_database_url(tenant_a)
    tenant_b_url = await get_tenant_database_url(tenant_b)
    assert tenant_a_url != tenant_b_url, "Tenants sharing database!"
```

### **Performance Testing**
- **Multi-tenant load testing**: 10+ tenants, 100+ concurrent requests each
- **Resource isolation validation**: High load on one tenant doesn't affect others
- **Scale testing**: Validate linear scaling characteristics
- **Cost optimization testing**: Verify inactive tenants scale to zero

---

## Production Deployment Strategy

### **Infrastructure Requirements**
- **Catalog Database**: Single Neon project for tenant metadata
- **Neon API Access**: Programmatic project creation/management
- **Neo4j Instance**: Single shared instance for all tenants
- **Application Deployment**: Same infrastructure as single-tenant

### **Rollout Plan**
1. **Week 1**: Deploy catalog database and tenant management service
2. **Week 2**: Deploy multi-tenant application code (backward compatible)
3. **Week 3**: Migrate existing data to default tenant project
4. **Week 4**: Onboard first external tenants
5. **Week 5**: Validate isolation, performance, and scaling
6. **Week 6**: Remove single-tenant legacy infrastructure

---

## Success Metrics

### **Technical Success Criteria**
- ✅ Complete tenant data isolation (zero cross-tenant access)
- ✅ Performance parity with single-tenant (< 5% degradation)
- ✅ Linear scaling characteristics (unlimited tenants)
- ✅ Cost optimization (inactive tenants scale to zero)
- ✅ Operational simplicity (no complex schema management)

### **Business Success Metrics**
- ✅ Ability to onboard 10+ tenants simultaneously
- ✅ Independent tenant configuration and scaling
- ✅ Tenant-specific usage analytics and billing
- ✅ Zero-downtime tenant provisioning
- ✅ Self-service tenant management capabilities

---

## Key Architectural Benefits

### **Following Official Best Practices**
1. **Neon Project-Per-Tenant**: Official recommendation for scalable multi-tenancy
2. **Graphiti group_id Namespacing**: Official pattern for tenant isolation
3. **Production-Proven Architecture**: Used by enterprise customers
4. **Operational Simplicity**: No complex RLS or shared schema management

### **Technical Advantages**
1. **True Isolation**: Complete database separation per tenant
2. **Linear Scaling**: No architectural limits on tenant count
3. **Cost Efficiency**: Pay only for active tenant resources
4. **Performance Predictability**: No cross-tenant performance interference
5. **Simplified Operations**: Standard database operations per tenant

### **Business Benefits**
1. **Rapid Tenant Onboarding**: Automated project creation
2. **Flexible Pricing Models**: Per-tenant resource tracking
3. **Enterprise Compliance**: Complete data isolation
4. **Scaling Confidence**: Architecture proven at scale
5. **Operational Excellence**: Simplified monitoring and management

---

This architecture follows the **official Neon and Graphiti recommendations** for production-ready multi-tenancy, ensuring scalability, security, and operational simplicity.
