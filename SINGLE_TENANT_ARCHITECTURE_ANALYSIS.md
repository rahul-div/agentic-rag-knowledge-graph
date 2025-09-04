# 🏗️ Single-Tenant RAG System Architecture Analysis

**Date:** January 15, 2025  
**Subject:** Complete ana**Database Schema:**

- **Sessions:** User conversation sessions with metadata
- **Messages:** Chat history with role (user/assistant/system)  
- **Documents:** Full document storage with metadata
- **Chunks:** Document chunks with vector embeddings
- **Vector Functions:** `match_chunks()`, `hybrid_search()` using pgvectorof current single-tenant dual storage RAG system  
**Goal:** Understand current architecture to guide multi-tenant migration  

---

## 📋 Executive Summary

Your current single-tenant RAG system is a sophisticated **hybrid intelligence platform** combining three powerful search systems:

1. **🔍 Neon PostgreSQL + pgvector** - Semantic similarity search with vector embeddings
2. **🕸️ Neo4j + Graphiti** - Knowledge graph for entity relationships and temporal facts  
3. **☁️ Onyx Cloud** - Enterprise document search (optional integration layer)

The system uses **Pydantic AI** as the orchestration layer with intelligent tool selection, dependency injection, and comprehensive fallback strategies.

---

## 🎯 Current Architecture Overview

### **System Type: Hybrid RAG (Dual Storage + Cloud Enhancement)**

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    🤖 PYDANTIC AI AGENT                            │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  LLM (Gemini/OpenAI) decides which tool to call:              │ │  
│  │  • vector_search, graph_search, onyx_search                   │ │
│  │  • comprehensive_search (multi-system synthesis)               │ │
│  │  • local_dual_search (vector + graph only)                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                       🔧 TOOL LAYER                                │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Individual │  │    Hybrid    │  │ Comprehensive│              │
│  │    Tools     │  │    Tools     │  │   Synthesis  │              │
│  │              │  │              │  │              │              │
│  │ • vector     │  │ • hybrid     │  │ • Multi-sys  │              │
│  │ • graph      │  │ • get_doc    │  │ • Fallback   │              │
│  │ • onyx       │  │ • list_docs  │  │ • Citations  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                     💾 SINGLE-TENANT DATA LAYER                    │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Neon PG     │  │    Neo4j     │  │  Onyx Cloud  │              │
│  │  + pgvector  │  │  + Graphiti  │  │  (Optional)  │              │
│  │              │  │              │  │              │              │
│  │ • Embeddings │  │ • Entities   │  │ • Documents  │              │
│  │ • Similarity │  │ • Relations  │  │ • Citations  │              │
│  │ • Chunks     │  │ • Temporal   │  │ • Chat API   │              │
│  │ • Documents  │  │ • Semantics  │  │ • CC-pairs   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Core Components Deep Dive

### **1. Agent Layer (`agent/agent.py`)**

**Framework:** Pydantic AI with dependency injection pattern

```python
# Agent Foundation
rag_agent = Agent(
    get_llm_model(),              # Supports Gemini, OpenAI, Anthropic
    deps_type=AgentDependencies,  # Dependency injection container
    system_prompt=SYSTEM_PROMPT   # Intelligent tool selection guidance
)

# Dependency Injection Container
@dataclass
class AgentDependencies:
    session_id: str
    onyx_service: Optional[Any] = None          # OnyxService instance
    onyx_document_set_id: Optional[int] = None  # Document set ID
    user_id: Optional[str] = None
    search_preferences: Dict[str, Any] = None   # System flags
```

**Key Characteristics:**

- **Session-based:** Each conversation has a unique session_id
- **Tool-agnostic:** LLM decides which tools to call based on query
- **Fallback-aware:** Graceful degradation when systems fail
- **Stateful:** Maintains conversation context and preferences

### **2. Database Layer (`agent/db_utils.py`)**

**Primary Storage:** Neon PostgreSQL with pgvector extension

```python
class DatabasePool:
    """Manages PostgreSQL connection pool"""
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.pool: Optional[Pool] = None  # asyncpg connection pool
```

**Database Schema:**
- **Sessions:** User conversation sessions with metadata
- **Messages:** Chat history with role (user/assistant/system)
- **Documents:** Full document storage with metadata
- **Chunks:** Document chunks with vector embeddings
- **Vector Functions:** `match_chunks()`, `hybrid_search()` using pgvector

**Core Operations:**
```python
# Vector similarity search
async def vector_search(embedding: List[float], limit: int = 10)

# Hybrid search (vector + keyword)
async def hybrid_search(embedding, query_text, limit, text_weight)

# Document management
async def get_document(document_id: str)
async def list_documents(limit, offset, metadata_filter)
```

### **3. Knowledge Graph Layer (`agent/graph_utils.py`)**

**Technology Stack:** Neo4j + Graphiti with Gemini integration

```python
class GraphitiClient:
    """Manages Graphiti knowledge graph operations using Gemini"""
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        # Gemini API configuration
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.llm_model = os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash")
        self.embedding_model = "text-embedding-004"
```

**Graphiti Integration:**
```python
# Initialize with Gemini clients
llm_client = GeminiClient(config=LLMConfig(api_key=self.api_key, model=self.llm_model))
embedder = GeminiEmbedder(config=GeminiEmbedderConfig(api_key=self.api_key))
reranker = GeminiRerankerClient(config=LLMConfig(api_key=self.api_key))

self.graphiti = Graphiti(
    neo4j_uri, neo4j_user, neo4j_password,
    llm_client=llm_client, embedder=embedder, cross_encoder=reranker
)
```

**Core Operations:**
```python
# Add content to knowledge graph
async def add_episode(episode_id, content, source, timestamp, metadata)

# Search for facts and relationships
async def search(query, center_node_distance=2, use_hybrid_search=True)

# Entity relationship discovery
async def get_related_entities(entity_name, relationship_types, depth)
```

### **4. Tool Layer (`agent/tools.py`)**

**Architecture:** 10 tools with intelligent parallel execution

#### **Individual Search Tools:**
```python
# Vector similarity search
async def vector_search_tool(input_data: VectorSearchInput) -> List[ChunkResult]

# Knowledge graph search
async def graph_search_tool(input_data: GraphSearchInput) -> List[GraphSearchResult]

# Onyx Cloud search
async def onyx_search_tool(input_data, onyx_service, document_set_id) -> Dict[str, Any]
```

#### **Master Synthesis Tool:**
```python
# Comprehensive multi-system search with intelligent synthesis
async def comprehensive_search_tool(input_data: ComprehensiveSearchInput) -> Dict[str, Any]:
    # Phase 1: Onyx Cloud (primary)
    # Phase 2: Local systems in parallel (asyncio.gather)
    # Phase 3: Intelligent synthesis based on results
```

#### **Local Dual Storage Tool:**
```python
# SMART Local Path: Combines vector + graph with synthesis
async def local_dual_search_tool(input_data: LocalDualSearchInput) -> Dict[str, Any]:
    # Parallel execution of vector and graph search
    # Intelligent synthesis with confidence scoring
    # Source citations and relationship insights
```

### **5. API Layer (`agent/api.py`)**

**Framework:** FastAPI with streaming support

```python
# Non-streaming chat
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest)

# Streaming chat with Server-Sent Events
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest)

# Individual search endpoints
@app.post("/search/vector")
@app.post("/search/graph") 
@app.post("/search/hybrid")
```

**Key Features:**
- **Session Management:** Automatic session creation and context handling
- **Conversation History:** Persistent chat history with metadata
- **Tool Call Extraction:** Tracks which tools the agent used
- **Error Handling:** Graceful degradation and error responses
- **Health Checks:** Database and graph connection monitoring

---

## 🔍 Data Flow Analysis

### **Typical Query Execution Flow**

```
1. 📥 User Query → FastAPI Endpoint
   │
2. 🔍 Session Management
   │  • Get/create session
   │  • Load conversation context
   │  • Build full prompt with history
   │
3. 🤖 Agent Execution (Pydantic AI)
   │  • LLM analyzes query
   │  • Selects appropriate tool(s)
   │  • Dependency injection provides services
   │
4. 🔧 Tool Execution (Parallel when possible)
   │  ┌─ Vector Search ────┐
   │  │  • Generate embedding (Gemini)
   │  │  • Query pgvector
   │  │  • Return ChunkResults
   │  │
   │  ├─ Graph Search ─────┤ ← PARALLEL
   │  │  • Query Graphiti
   │  │  • Extract facts/relationships  
   │  │  • Return GraphSearchResults
   │  │
   │  └─ Onyx Search ──────┘
   │     • Document set search
   │     • Enterprise citations
   │     • Return structured data
   │
5. 🧠 Synthesis & Response
   │  • Multi-system result combination
   │  • Source citation generation
   │  • Confidence scoring
   │
6. 💾 Storage & Response
   │  • Save conversation turn
   │  • Extract tool calls
   │  • Return ChatResponse
```

### **Parallel Execution Architecture**

The system uses `asyncio.gather()` for optimal performance:

```python
# Example from comprehensive_search_tool
graphiti_tasks = []
if include_vector:
    graphiti_tasks.append(("vector", vector_search_tool(input)))
if include_graph:
    graphiti_tasks.append(("graph", graph_search_tool(input)))

# 🚀 PARALLEL EXECUTION
search_results = await asyncio.gather(
    *[task for _, task in graphiti_tasks],
    return_exceptions=True
)
```

---

## 🏷️ Single-Tenant Characteristics

### **Current Limitations (Why Migration Needed)**

1. **Shared Database Schema:**
   ```sql
   -- All tables are global - no tenant isolation
   CREATE TABLE documents (id UUID PRIMARY KEY, title TEXT, content TEXT);
   CREATE TABLE chunks (id UUID PRIMARY KEY, document_id UUID, embedding vector(768));
   ```

2. **Shared Neo4j Instance:**
   ```python
   # Single graph instance - no namespacing
   self.graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password, ...)
   # All entities and relationships in same graph
   ```

3. **Global Configuration:**
   ```python
   # Environment variables are global
   DATABASE_URL = os.getenv("DATABASE_URL")
   NEO4J_URI = os.getenv("NEO4J_URI") 
   # No per-tenant configuration
   ```

4. **Shared Sessions:**
   ```python
   # Sessions are global - no tenant context
   async def create_session(user_id=None, metadata=None):
       # No tenant_id parameter
   ```

5. **Global Search Results:**
   ```python
   # Vector search across all documents
   async def vector_search(embedding, limit):
       # No tenant filtering in queries
   ```

### **Current Strengths to Preserve**

1. **Robust Tool Architecture:** The 10-tool system with intelligent selection
2. **Parallel Execution:** Efficient async operations with proper error handling
3. **Dependency Injection:** Clean separation of concerns
4. **Comprehensive Synthesis:** Multi-system result combination
5. **Fallback Strategies:** Graceful degradation when systems fail
6. **Conversation Management:** Session-based context and history
7. **API Design:** Clean FastAPI with streaming support

---

## 🚀 Migration Path to Multi-Tenancy

### **Key Changes Required**

#### **1. Database Layer Transformation**
```sql
-- BEFORE (Single-tenant)
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    title TEXT,
    content TEXT
);

-- AFTER (Multi-tenant with RLS)
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    title TEXT,
    content TEXT
);

-- Row Level Security
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_documents ON documents
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

#### **2. Graphiti Namespacing**
```python
# BEFORE (Single namespace)
await self.graphiti.add_episode(
    name=episode_id,
    episode_body=content,
    source=EpisodeType.text
)

# AFTER (Multi-tenant with group_id)
await self.graphiti.add_episode(
    name=episode_id,
    episode_body=content,
    source=EpisodeType.text,
    group_id=f"tenant_{tenant_id}"  # Graphiti namespacing
)
```

#### **3. Dependency Injection Enhancement**
```python
# BEFORE
@dataclass
class AgentDependencies:
    session_id: str
    user_id: Optional[str] = None

# AFTER
@dataclass
class AgentDependencies:
    session_id: str
    tenant_id: str                    # 🆕 Tenant context
    user_id: Optional[str] = None
    tenant_config: TenantConfig       # 🆕 Per-tenant settings
    tenant_db_manager: TenantDBManager # 🆕 Tenant-aware DB access
```

#### **4. Tool Layer Updates**
```python
# BEFORE
async def vector_search_tool(input_data: VectorSearchInput):
    # Global search
    results = await vector_search(embedding, limit)

# AFTER
async def vector_search_tool(input_data: VectorSearchInput, tenant_context: TenantContext):
    # Tenant-aware search
    results = await tenant_context.db_manager.vector_search(embedding, limit)
```

### **Migration Strategy Overview**

1. **Phase 1: Schema Migration**
   - Add tenant_id columns to all tables
   - Implement Row Level Security (RLS)
   - Create tenant management tables

2. **Phase 2: Application Layer**
   - Update dependency injection for tenant context
   - Modify all database queries for tenant filtering
   - Implement Graphiti group_id namespacing

3. **Phase 3: API Layer** 
   - Add tenant authentication/authorization
   - Update endpoint signatures for tenant context
   - Implement tenant-aware session management

4. **Phase 4: Testing & Validation**
   - Tenant isolation testing
   - Performance benchmarking
   - Security validation

---

## 📊 Architecture Quality Assessment

### **Strengths of Current Design**

✅ **Modular Architecture:** Clean separation between agent, tools, and data layers  
✅ **Async Performance:** Proper use of asyncio for parallel operations  
✅ **Error Resilience:** Comprehensive fallback strategies  
✅ **Type Safety:** Strong Pydantic model usage throughout  
✅ **Dependency Injection:** Clean IoC pattern for service management  
✅ **Multi-System Integration:** Seamless combination of vector, graph, and cloud search  
✅ **Conversation Context:** Proper session and message management  
✅ **Tool Intelligence:** LLM-driven tool selection with rich descriptions  

### **Areas for Multi-Tenant Enhancement**

🔄 **Tenant Context Propagation:** Need tenant_id throughout the call stack  
🔄 **Database Isolation:** Implement RLS and tenant-aware queries  
🔄 **Configuration Management:** Per-tenant settings and feature flags  
🔄 **Resource Isolation:** Tenant-specific connection pools and limits  
🔄 **Security Enhancement:** Authentication, authorization, and audit logging  
🔄 **Monitoring & Metrics:** Tenant-specific observability  

---

## 🎯 Conclusion

Your current single-tenant RAG system is **exceptionally well-architected** with:

- **Sophisticated AI orchestration** using Pydantic AI
- **Dual storage excellence** with pgvector + Graphiti integration  
- **Enterprise-grade patterns** including dependency injection and async operations
- **Intelligent synthesis** combining multiple search systems
- **Production-ready features** like streaming, error handling, and health checks

The **migration to multi-tenancy** will enhance this solid foundation by adding:
- **Tenant isolation** at database and graph levels
- **Per-tenant configuration** and resource management  
- **Enhanced security** with proper tenant authentication
- **Scalable architecture** supporting multiple organizations

The existing codebase provides an excellent foundation for multi-tenant migration, with minimal architectural changes required thanks to the clean dependency injection and modular design already in place.

---

**Next Steps:** Proceed with the multi-tenant implementation using the validated approach in `/Tenant/` directory, following the migration guide in `MULTI_TENANT_MIGRATION_GUIDE.md`.
