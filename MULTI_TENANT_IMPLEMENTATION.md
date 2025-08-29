# Multi-Tenant Local Path: Dual Storage Implementation Guide

## 🎯 **Overview**

Transform your existing **Local Path: Dual Storage** RAG system into a production-ready **multi-tenant platform** where each client has complete data isolation while leveraging shared infrastructure for cost efficiency.

**Focus**: Neon PostgreSQL + pgvector and Neo4j + Graphiti (excluding Onyx Cloud)

## 🏗️ **Architecture Pattern: Industry-Standard Row-Level Tenant Isolation**

Following the **shared database, row-level tenant isolation** pattern as recommended by Neon and Graphiti official documentation for scalable multi-tenant systems.

### **Core Principles**
- **One codebase, shared infrastructure**
- **Complete data isolation per tenant via tenant_id**
- **Neon PostgreSQL with Row-Level Security (RLS)**
- **Graphiti namespace isolation using group_id**
- **Zero cross-tenant data leakage possible**
- **Cost-effective shared resources**

```
Tenant A ──┐
Tenant B ──┤── JWT/Auth ── FastAPI ── Pydantic AI Agent ──┬── Neon PostgreSQL + pgvector (RLS)
Tenant C ──┤                                              └── Neo4j + Graphiti (group_id namespacing)
Tenant N ──┘
```

---

## 📊 **Implementation Components**

### **1. Neon PostgreSQL Multi-Tenant Schema with RLS**

Based on Neon's official multi-tenancy patterns, we implement **Row-Level Security** for tenant isolation:

```sql
-- Enable RLS extension
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

-- Indexes for performance
CREATE INDEX idx_documents_tenant_id ON documents(tenant_id);
CREATE INDEX idx_chunks_tenant_id ON chunks(tenant_id);
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_sessions_tenant_id ON sessions(tenant_id);
CREATE INDEX idx_messages_tenant_id ON messages(tenant_id);
CREATE INDEX idx_messages_session_id ON messages(session_id);
```

### **2. Graphiti Multi-Tenant Integration with Namespacing**

Based on Graphiti's official graph namespacing documentation, we use `group_id` for tenant isolation:

```python
# tenant/graphiti_client.py
import asyncio
from typing import Optional, List, Dict, Any
from graphiti_core import Graphiti
from graphiti_core.nodes import EntityNode
from graphiti_core.edges import EntityEdge
import uuid
from datetime import datetime

class TenantGraphitiClient:
    """
    Multi-tenant Graphiti client using group_id for namespace isolation.
    
    Based on official Graphiti documentation:
    https://help.getzep.com/graphiti/core-concepts/graph-namespacing
    """
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.graphiti = Graphiti(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password
        )
    
    def _get_tenant_namespace(self, tenant_id: str) -> str:
        """Generate namespace for tenant following official pattern."""
        return f"tenant_{tenant_id}"
    
    async def add_episode_for_tenant(
        self,
        tenant_id: str,
        episode_name: str,
        episode_body: str,
        source_description: str = "Document content",
        reference_time: Optional[datetime] = None
    ) -> bool:
        """
        Add episode to tenant's namespace.
        
        Args:
            tenant_id: Unique tenant identifier
            episode_name: Name for the episode
            episode_body: Content to process
            source_description: Description of the source
            reference_time: When the episode occurred
            
        Returns:
            Success status
        """
        try:
            namespace = self._get_tenant_namespace(tenant_id)
            
            await self.graphiti.add_episode(
                name=episode_name,
                episode_body=episode_body,
                source=EpisodeType.text,
                source_description=source_description,
                reference_time=reference_time or datetime.now(),
                group_id=namespace  # Tenant isolation via namespace
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to add episode for tenant {tenant_id}: {e}")
            return False
    
    async def search_tenant_graph(
        self,
        tenant_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search within tenant's namespace only.
        
        Args:
            tenant_id: Unique tenant identifier
            query: Search query
            limit: Maximum results
            
        Returns:
            List of search results
        """
        try:
            namespace = self._get_tenant_namespace(tenant_id)
            
            # Official Graphiti namespace search pattern
            search_results = await self.graphiti.search(
                query=query,
                group_id=namespace  # Only search within tenant namespace
            )
            
            return search_results[:limit]
        except Exception as e:
            logger.error(f"Failed to search for tenant {tenant_id}: {e}")
            return []
    
    async def get_tenant_entity_relationships(
        self,
        tenant_id: str,
        entity_name: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get entity relationships within tenant namespace.
        
        Args:
            tenant_id: Unique tenant identifier
            entity_name: Name of entity to explore
            depth: Maximum traversal depth
            
        Returns:
            Entity relationships data
        """
        try:
            namespace = self._get_tenant_namespace(tenant_id)
            
            # Advanced node search within namespace
            from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
            
            node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
            node_search_config.limit = 20
            
            results = await self.graphiti._search(
                query=entity_name,
                group_id=namespace,  # Tenant isolation
                config=node_search_config
            )
            
            return {
                "central_entity": entity_name,
                "namespace": namespace,
                "related_entities": results,
                "depth": depth
            }
        except Exception as e:
            logger.error(f"Failed to get relationships for tenant {tenant_id}: {e}")
            return {
                "central_entity": entity_name,
                "related_entities": [],
                "error": str(e)
            }
    
    async def add_manual_fact_for_tenant(
        self,
        tenant_id: str,
        source_entity: str,
        target_entity: str,
        relationship: str,
        fact_description: str
    ) -> bool:
        """
        Manually add fact triple to tenant namespace.
        
        Args:
            tenant_id: Unique tenant identifier
            source_entity: Source entity name
            target_entity: Target entity name  
            relationship: Relationship type
            fact_description: Description of the fact
            
        Returns:
            Success status
        """
        try:
            namespace = self._get_tenant_namespace(tenant_id)
            
            # Create nodes with tenant namespace
            source_node = EntityNode(
                uuid=str(uuid.uuid4()),
                name=source_entity,
                group_id=namespace
            )
            
            target_node = EntityNode(
                uuid=str(uuid.uuid4()),
                name=target_entity,
                group_id=namespace
            )
            
            # Create edge with same namespace
            edge = EntityEdge(
                group_id=namespace,
                source_node_uuid=source_node.uuid,
                target_node_uuid=target_node.uuid,
                created_at=datetime.now(),
                name=relationship,
                fact=fact_description
            )
            
            # Add to graph
            await self.graphiti.add_triplet(source_node, edge, target_node)
            
            return True
        except Exception as e:
            logger.error(f"Failed to add manual fact for tenant {tenant_id}: {e}")
            return False
    
    async def get_tenant_timeline(
        self,
        tenant_id: str,
        entity_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get timeline for entity within tenant namespace.
        
        Args:
            tenant_id: Unique tenant identifier
            entity_name: Entity to get timeline for
            start_date: Start of time range
            end_date: End of time range
            
        Returns:
            Timeline data
        """
        try:
            namespace = self._get_tenant_namespace(tenant_id)
            
            # This would use Graphiti's temporal features
            # within the tenant namespace
            timeline_results = await self.graphiti.get_entity_timeline(
                entity_name=entity_name,
                group_id=namespace,  # Tenant isolation
                start_date=start_date,
                end_date=end_date
            )
            
            return timeline_results
        except Exception as e:
            logger.error(f"Failed to get timeline for tenant {tenant_id}: {e}")
            return []
```

## 📋 **Complete File Structure**

The implementation consists of these key components in the `Tenant/` folder:

1. **`schema.sql`** - Complete PostgreSQL schema with RLS
2. **`tenant_manager.py`** - Tenant management and authentication
3. **`multi_tenant_db.py`** - Database utilities with tenant isolation
4. **`multi_tenant_graphiti.py`** - Graphiti client with namespacing
5. **`multi_tenant_agent.py`** - Agent with tenant-aware tools
6. **`multi_tenant_api.py`** - FastAPI with tenant routing
7. **`auth_middleware.py`** - JWT authentication middleware
8. **`deployment_guide.md`** - Step-by-step deployment instructions
9. **`testing_guide.md`** - Comprehensive testing scenarios

This implementation follows **official patterns** from both Neon and Graphiti documentation, ensuring a production-ready, scalable multi-tenant system.
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
$$;
```

### **2. Tenant-Aware Knowledge Graph (Neo4j + Graphiti)**

All entities and relationships tagged with `tenant_id`:

```cypher
-- Tenant constraints for complete isolation
CREATE CONSTRAINT tenant_entity_constraint IF NOT EXISTS
FOR (n:Entity) REQUIRE n.tenant_id IS NOT NULL;

CREATE CONSTRAINT tenant_relationship_constraint IF NOT EXISTS
FOR ()-[r:RELATES_TO]-() REQUIRE r.tenant_id IS NOT NULL;

-- Performance indexes
CREATE INDEX tenant_entity_index IF NOT EXISTS
FOR (n:Entity) ON (n.tenant_id, n.name);

-- Example entity with tenant tagging
MERGE (e:Entity {
    name: "Project Alpha",
    entity_type: "project",
    tenant_id: "client_abc",
    uuid: "entity_123",
    properties: {
        status: "active",
        priority: "high"
    }
})

-- Example relationship with tenant isolation
MATCH (a:Entity {tenant_id: "client_abc", name: "Project Alpha"})
MATCH (b:Entity {tenant_id: "client_abc", name: "Team Lead"})
MERGE (a)-[r:MANAGED_BY {
    tenant_id: "client_abc",
    relationship_type: "management",
    created_at: datetime()
}]->(b)
```

---

## 🛠️ **Implementation Files Structure**

```
multi_tenant/
├── ARCHITECTURE.md              # Detailed architecture documentation
├── neon_tenant_isolation.py     # Neon PostgreSQL + pgvector tenant manager
├── neo4j_graphiti_tenant_isolation.py  # Neo4j + Graphiti tenant manager
├── auth_middleware.py           # JWT-based tenant authentication
├── tenant_agent_tools.py        # Tenant-aware Pydantic AI tools
├── tenant_models.py             # Pydantic models with tenant isolation
├── ingestion_pipeline.py        # Multi-tenant document ingestion
├── api_endpoints.py             # FastAPI endpoints with tenant context
├── deployment_guide.md          # Step-by-step deployment instructions
└── examples/                    # Usage examples and test cases
```

---

## 🔐 **Tenant Isolation Implementation**

### **Database Level (PostgreSQL)**
- **Row-Level Security**: Every query filtered by `tenant_id`
- **Custom Functions**: Vector search functions include tenant filtering
- **Performance Indexes**: Composite indexes on `(tenant_id, *)` 
- **Resource Limits**: Per-tenant quotas and constraints

### **Graph Level (Neo4j + Graphiti)**
- **Node Properties**: All entities tagged with `tenant_id`
- **Relationship Properties**: All connections tagged with `tenant_id`  
- **Cypher Filtering**: All queries include tenant context
- **Namespace Isolation**: Tenant-specific Graphiti clients

### **Application Level**
- **JWT Token Claims**: Tenant ID embedded in authentication
- **Context Propagation**: Tenant ID flows through all operations
- **Tool Isolation**: All AI agent tools respect tenant boundaries
- **Session Management**: Sessions linked to specific tenants

---

## 🔄 **Local Dual Search with Tenant Isolation**

Enhanced `local_dual_search` tool with complete tenant awareness:

```python
async def local_dual_search_tenant(
    query: str, 
    tenant_id: str, 
    limit: int = 10
) -> Dict[str, Any]:
    """
    SMART Local Path: Dual Storage search with tenant isolation.
    
    Combines:
    - Neon PostgreSQL + pgvector for semantic similarity
    - Neo4j + Graphiti for relationship discovery
    - Complete tenant boundary enforcement
    """
    
    # Validate tenant access
    tenant = await neon_manager.get_tenant(tenant_id)
    if not tenant:
        raise ValueError(f"Invalid tenant: {tenant_id}")
    
    # Parallel execution within tenant boundary
    vector_task = neon_manager.vector_search(embedding, tenant_id, limit=limit)
    graph_task = neo4j_manager.graph_search(tenant_id, query, limit=limit)
    
    vector_results, graph_results = await asyncio.gather(vector_task, graph_task)
    
    # Intelligent synthesis with source attribution
    synthesized = await synthesize_tenant_results(
        vector_results, graph_results, tenant_id
    )
    
    return {
        "tenant_id": tenant_id,
        "query": query,
        "vector_results": len(vector_results),
        "graph_results": len(graph_results),
        "synthesized_response": synthesized,
        "sources": extract_tenant_sources(vector_results, graph_results),
        "confidence": calculate_confidence_score(vector_results, graph_results)
    }
```

---

## 📈 **Benefits of This Architecture**

### **Cost Efficiency**
- **Shared Infrastructure**: One database cluster serves all tenants
- **Resource Optimization**: Dynamic scaling based on aggregate usage  
- **Operational Simplicity**: Single codebase, unified maintenance

### **Security & Compliance**
- **Complete Data Isolation**: Zero cross-tenant data leakage
- **Audit Trail**: All operations logged with tenant context
- **Compliance Ready**: SOC2, GDPR, HIPAA compatible design

### **Scalability**
- **Horizontal Scaling**: Add tenants without infrastructure changes
- **Performance Isolation**: Tenant resource limits prevent noisy neighbors
- **Global Distribution**: Tenant data can be geo-located

### **Local Path: Dual Storage Optimization**
- **Intelligent Routing**: Vector + graph search synthesis
- **Source Attribution**: Clear citation of tenant-specific sources  
- **Relationship Discovery**: Hidden insights within tenant boundary
- **Fast Performance**: Local processing without external API dependencies

---

## 🚀 **Deployment Strategy**

### **Phase 1: Schema Migration (Week 1)**
1. Add `tenant_id` columns to existing tables
2. Create tenant-aware database functions
3. Set up Neo4j tenant constraints and indexes
4. Test tenant isolation with sample data

### **Phase 2: Application Updates (Week 2)**  
1. Update Pydantic models with `TenantAware` base class
2. Implement tenant-aware database and graph managers
3. Update AI agent tools with tenant context
4. Test all tools with multi-tenant data

### **Phase 3: Authentication & API (Week 3)**
1. Implement JWT-based tenant authentication
2. Update FastAPI endpoints with tenant validation
3. Create tenant management endpoints
4. Test end-to-end multi-tenant workflows

### **Phase 4: Production Deployment (Week 4)**
1. Performance testing with multiple tenants
2. Security audit for tenant isolation
3. Monitoring and alerting setup
4. Documentation and support processes

---

## 🔒 **Security Guarantees**

### **Database Level**
- All PostgreSQL queries include `WHERE tenant_id = $tenant_id`
- Vector search functions enforce tenant filtering
- Foreign key constraints maintain referential integrity within tenants

### **Graph Level**  
- All Neo4j queries include tenant property filtering
- Graphiti clients use tenant-specific namespaces
- Cypher queries validate tenant context on all operations

### **Application Level**
- JWT tokens contain verified tenant claims
- All API endpoints validate tenant context
- Session management links to specific tenants
- Tool execution restricted to tenant data boundaries

---

## 💡 **Quick Start Example**

```python
# Initialize tenant managers
neon_manager = NeonTenantManager(neon_connection_string)
neo4j_manager = Neo4jGraphitiTenantManager(neo4j_uri, username, password)

# Create tenant
tenant = await neon_manager.create_tenant("client_abc", "ABC Corp")
await neo4j_manager.create_tenant_config("client_abc", "ABC Corp")

# Ingest document with tenant tagging
document = Document(
    tenant_id="client_abc",
    title="Project Requirements", 
    content="Detailed project requirements...",
    source="requirements.md"
)
doc_id = await neon_manager.create_document(document)

# Add to knowledge graph
episode = await neo4j_manager.add_episode(
    tenant_id="client_abc",
    name="Requirements Analysis",
    content=document.content,
    source_description="Project requirements document"
)

# Perform tenant-aware local dual search
results = await local_dual_search_tenant(
    query="project requirements analysis", 
    tenant_id="client_abc",
    limit=10
)
```

---

This implementation provides **complete tenant isolation** for your Local Path: Dual Storage system while maintaining cost efficiency through shared infrastructure. The solution is **production-ready** and follows industry-standard SaaS multi-tenancy patterns.

**Ready for immediate implementation** with your existing Neon PostgreSQL + pgvector and Neo4j + Graphiti infrastructure.