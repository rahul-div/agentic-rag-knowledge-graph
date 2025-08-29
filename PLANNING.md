# Onyx + Graphiti Hybrid Architecture - Planning Document

## Current Architecture Analysis

### 🏗️ **Current System (Graphiti-Only RAG)**

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                              │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │   FastAPI       │          │   Streaming SSE    │      │
│  │   Endpoints     │          │   Responses        │      │
│  └────────┬────────┘          └────────────────────┘      │
├───────────┴─────────────────────────────────────────────────┤
│                    Pydantic AI Agent                       │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │  Single Agent   │◄────────►│   Current Tools    │      │
│  │  (Gemini 2.0)   │          │  - vector_search   │      │
│  └─────────────────┘          │  - graph_search    │      │
│                                │  - hybrid_search   │      │
│                                │  - get_document    │      │
│                                │  - get_entity_rels │      │
│                                └────────────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                  Data Processing Layer                      │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │   PostgreSQL    │          │    Neo4j + Graphiti│      │
│  │   + pgvector    │          │    Knowledge Graph │      │
│  │   Vector Store  │          │    Temporal Graphs │      │
│  └─────────────────┘          └────────────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    Ingestion Pipeline                       │
│  ┌─────────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │   Semantic      │  │   Gemini      │  │  GraphBuilder │ │
│  │   Chunker       │→ │   Embedder    │→ │  (Entity     │ │
│  │   (LLM-powered) │  │   (768-dim)   │  │   Extraction)│ │
│  └─────────────────┘  └───────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Current Tech Stack:**
- **AI Models:** Google Gemini 2.0 Flash Thinking (LLM + Embeddings)
- **Vector DB:** PostgreSQL with pgvector (768-dimensional embeddings)
- **Knowledge Graph:** Neo4j + Graphiti (temporal, entity relationships)
- **Agent Framework:** Pydantic AI with 7 tools
- **API:** FastAPI with Server-Sent Events streaming
- **Configuration:** Environment-based (.env)

**Current Tools:**
1. `vector_search` - Semantic similarity search
2. `graph_search` - Knowledge graph traversal
3. `hybrid_search` - Combined vector + graph search
4. `get_document` - Document retrieval
5. `list_documents` - Document listing
6. `get_entity_relationships` - Entity relationship queries
7. `get_entity_timeline` - Temporal entity analysis

---

### 🚀 **Target Architecture (Onyx + Graphiti Hybrid)**

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                              │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │   FastAPI       │          │   Streaming SSE    │      │
│  │   Endpoints     │          │   Tool Visibility  │      │
│  └────────┬────────┘          └────────────────────┘      │
├───────────┴─────────────────────────────────────────────────┤
│              Enhanced Pydantic AI Agent                    │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │  Smart Agent    │◄────────►│  Expanded Toolset  │      │
│  │  (Gemini 2.0)   │          │ ┌─ ONYX TOOLS ─┐   │      │
│  │  w/ Routing     │          │ │ onyx_search   │   │      │
│  │  Intelligence   │          │ │ onyx_answer   │   │      │
│  └─────────────────┘          │ │ onyx_ingest   │   │      │
│                                │ └───────────────┘   │      │
│                                │ ┌─ GRAPHITI ──┐   │      │
│                                │ │ graph_search │   │      │
│                                │ │ entity_rels  │   │      │
│                                │ │ timeline     │   │      │
│                                │ └───────────────┘   │      │
│                                │ ┌─ HYBRID ────┐   │      │
│                                │ │ comprehensive │   │      │
│                                │ │ multi_search │   │      │
│                                │ └───────────────┘   │      │
│                                └────────────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                  Dual Storage Layer                         │
│  ┌─────────────────┐          ┌────────────────────┐      │
│  │   ONYX CLOUD    │          │    LOCAL DUAL      │      │
│  │ ┌─────────────┐ │          │    STORAGE         │      │
│  │ │ Enterprise  │ │          │  ┌───────────────┐ │      │
│  │ │ Vector DB   │ │          │  │ pgvector      │ │      │
│  │ │ (Scalable)  │ │          │  │ Semantic      │ │      │
│  │ └─────────────┘ │          │  │ Search        │ │      │
│  │ ┌─────────────┐ │          │  └───────────────┘ │      │
│  │ │ 40+ Connec- │ │          │  ┌───────────────┐ │      │
│  │ │ tors & APIs │ │          │  │ Neo4j +       │ │      │
│  │ └─────────────┘ │          │  │ Graphiti      │ │      │
│  └─────────────────┘          │  └───────────────┘ │      │
├─────────────────────────────────────────────────────────────┤
│                 Dual Ingestion Pipeline                     │
│  ┌─────────────────┐                                       │
│  │   UNIFIED       │   ┌──── Onyx Cloud API ──────────┐   │
│  │   DOCUMENT      │──►│ • Document Sectioning        │   │
│  │   PROCESSOR     │   │ • Metadata Mapping           │   │
│  │                 │   │ • Enterprise Ingestion       │   │
│  │   (Semantic     │   └─────────────────────────────┘   │
│  │    Chunking)    │   ┌──── Local Dual Storage ────────┐  │
│  │                 │──►│ • pgvector Semantic Storage   │   │
│  │                 │   │ • Neo4j + Graphiti KG Build  │   │
│  │                 │   │ • Entity & Relationship Map  │   │
│  └─────────────────┘   └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Migration Plan

### **Phase 1: Current → Cloud Hybrid (Weeks 1-5)**

**What Changes:**
- ✅ **Keep:** All existing Graphiti functionality
- ✅ **Keep:** PostgreSQL vector database (as backup)
- ✅ **Keep:** Neo4j + Graphiti knowledge graph
- 🆕 **Add:** Onyx Cloud integration via API
- 🆕 **Add:** Dual ingestion pipeline
- 🆕 **Add:** Intelligent tool routing in agent

**What Stays The Same:**
- Gemini 2.0 as primary LLM
- FastAPI with streaming responses
- Pydantic AI agent framework
- Environment-based configuration
- PostgreSQL for session/metadata storage
- Neo4j for knowledge graph storage

### **Phase 2: Cloud → Community Migration (Week 6+)**

**What Changes:**
- 🔄 **Migrate:** From Onyx Cloud API to local Docker deployment
- 🔄 **Update:** Base URL from cloud to localhost:8080
- 🔄 **Remove:** Cloud API key authentication
- 🔄 **Add:** Local Docker infrastructure

**What Stays The Same:**
- All agent tools and functionality
- Triple ingestion pipeline logic (Onyx Cloud + Local Dual Storage)
- Intelligent routing algorithms
- Local Dual Storage system (pgvector + Neo4j + Graphiti)

---

## Technical Implementation Details

### **Current System Strengths to Preserve:**

1. **Gemini Integration Excellence**
   - Optimized for Gemini 2.0 Flash Thinking
   - 768-dimensional embeddings perfectly configured
   - Comprehensive error handling and validation

2. **Graphiti Temporal Intelligence**
   - Real-time knowledge graph updates
   - Entity relationship tracking
   - Historical fact evolution
   - Custom entity types and relationships

3. **Agent Tool Orchestration**
   - Sophisticated tool routing logic
   - Context-aware search strategy selection
   - Streaming responses with tool visibility

4. **Production-Ready Infrastructure**
   - Connection pooling (PostgreSQL, Neo4j)
   - Comprehensive logging and monitoring
   - Rate limiting and timeout handling
   - Environment-based configuration

### **Enhanced Capabilities After Migration:**

1. **Enterprise Search Power (via Onyx)**
   - Scalable document processing
   - 40+ enterprise connectors
   - Advanced document management
   - Professional search algorithms

2. **Intelligent Hybrid Search**
   - Onyx for factual/document discovery queries
   - Graphiti for relationship/temporal queries  
   - Combined results with confidence scoring
   - Query-type-based routing intelligence

3. **Dual Data Redundancy**
   - Onyx handles enterprise-scale vector operations
   - Graphiti maintains relationship intelligence
   - PostgreSQL provides backup and metadata
   - Cross-system consistency validation

4. **Cost Optimization Path**
   - Start with Onyx Cloud for development/testing
   - Migrate to Community Edition for production
   - Zero ongoing cloud costs post-migration
   - Full system control and customization

---

## Key Integration Points

### **Agent Intelligence Enhancement**

```python
# Current System Prompt Strategy
CURRENT_ROUTING = """
- Use vector_search for semantic similarity
- Use graph_search for entity relationships  
- Use hybrid_search for complex queries
"""

# Enhanced System Prompt Strategy  
HYBRID_ROUTING = """
- Use onyx_search for document discovery and factual questions
- Use onyx_answer_with_quote for comprehensive answers with citations
- Use graph_search for entity relationships and network analysis
- Use get_entity_timeline for temporal/historical questions
- Use comprehensive_search for complex research requiring multiple perspectives
"""
```

### **Data Flow Architecture**

```python
# Current Ingestion Flow
Document → Semantic Chunking → Gemini Embeddings → PostgreSQL
       ↘ Entity Extraction → Graphiti → Neo4j

# Enhanced Dual Ingestion Flow
Document → Semantic Chunking → ┌─ Onyx Cloud API → Onyx Vector Store
                              └─ Local Dual Storage → pgvector + Neo4j + Graphiti
```

### **Search Strategy Matrix**

| Query Type | Current System | Enhanced System | Rationale |
|------------|---------------|-----------------|-----------|
| Factual Questions | vector_search | onyx_answer_with_quote | Enterprise QA with citations |
| Document Discovery | vector_search | onyx_search | Scalable semantic search |
| Relationship Queries | graph_search | graph_search (unchanged) | Graphiti excels at this |
| Temporal Analysis | get_entity_timeline | get_entity_timeline | Graphiti's unique strength |
| Complex Research | hybrid_search | comprehensive_search | Multi-system intelligence |

---

## Success Metrics & Validation

### **Technical Success Criteria:**
- [ ] All existing functionality preserved
- [ ] Onyx Cloud integration working (API calls successful)
- [ ] Dual ingestion pipeline operational
- [ ] Agent intelligently routes between systems
- [ ] Response quality maintained or improved
- [ ] System latency remains acceptable (<3s for complex queries)

### **Business Value Delivered:**
- ✅ **Immediate:** Enhanced search capabilities via Onyx enterprise features
- ✅ **Short-term:** Improved answer quality with citations and source tracking
- ✅ **Medium-term:** Scalable architecture supporting larger document volumes
- ✅ **Long-term:** Cost optimization through Community Edition migration

---

## Risk Mitigation

### **Technical Risks & Mitigations:**

1. **Onyx API Reliability** → Keep Local Dual Storage as fallback system
2. **Performance Degradation** → Implement intelligent caching and optimization
3. **Data Consistency** → Build validation and synchronization mechanisms
4. **Migration Complexity** → Phased approach with comprehensive testing

### **Operational Risks & Mitigations:**

1. **Increased Complexity** → Comprehensive documentation and monitoring
2. **Cost Management** → Clear migration path to Community Edition
3. **Team Learning Curve** → Gradual rollout with extensive documentation

This architecture evolution maintains all existing strengths while adding enterprise-grade capabilities, positioning the system for both immediate enhancement and long-term scalability.
