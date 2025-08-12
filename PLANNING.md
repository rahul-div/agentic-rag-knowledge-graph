# Multi-Client Project Intelligence System - Planning Document

## Current Architecture Analysis

### 🏗️ **Current System (Project-Centric Graphiti RAG)**

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

### 🚀 **Target Architecture (Multi-Client Project Intelligence Platform)**

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
│  │   ONYX CLOUD    │          │    GRAPHITI LOCAL  │      │
│  │ ┌─────────────┐ │          │  ┌───────────────┐ │      │
│  │ │ Multi-Client│ │          │  │ Neo4j +       │ │      │
│  │ │ Vector DB   │ │          │  │ Project       │ │      │
│  │ │ (Isolated)  │ │          │  │ Knowledge     │ │      │
│  │ └─────────────┘ │          │  │ Graph         │ │      │
│  │ ┌─────────────┐ │          │  └───────────────┘ │      │
│  │ │ Enterprise  │ │          │  ┌───────────────┐ │      │
│  │ │ Search APIs │ │          │  │ Stakeholder   │ │      │
│  │ └─────────────┘ │          │  │ Requirements  │ │      │
│  └─────────────────┘          │  └───────────────┘ │      │
├─────────────────────────────────────────────────────────────┤
│                 Dual Ingestion Pipeline                     │
│  ┌─────────────────┐                                       │
│  │   UNIFIED       │   ┌──── Onyx Cloud API ──────────┐   │
│  │   DOCUMENT      │──►│ • Project Document Sectioning │   │
│  │   PROCESSOR     │   │ • Client Metadata Mapping    │   │
│  │                 │   │ • Multi-Tenant Ingestion     │   │
│  │   (Semantic     │   └─────────────────────────────┘   │
│  │    Chunking)    │   ┌──── Graphiti Local ───────────┐  │
│  │                 │──►│ • Project Entity Extraction  │   │
│  │                 │   │ • Stakeholder Mapping        │   │
│  │                 │   │ • Decision Timeline Building │   │
│  └─────────────────┘   └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Migration Plan

### **Phase 1: Current → Multi-Client Hybrid (Weeks 1-7)**

**What Changes:**
- ✅ **Keep:** All existing Graphiti functionality with project-centric focus
- ✅ **Keep:** PostgreSQL vector database (as backup/metadata store)
- ✅ **Keep:** Neo4j + Graphiti knowledge graph for project relationships
- 🆕 **Add:** Onyx Cloud integration for enterprise search capabilities
- 🆕 **Add:** Dual ingestion pipeline for project documents
- 🆕 **Add:** Intelligent tool routing for project-specific queries

**What Stays The Same:**
- Gemini 2.0 as primary LLM
- FastAPI with streaming responses
- Pydantic AI agent framework
- Environment-based configuration
- PostgreSQL for session/metadata storage
- Neo4j for project knowledge graph storage

### **Phase 2: Cloud → Community Migration (Week 6+)**

**What Changes:**
- 🔄 **Migrate:** From Onyx Cloud API to local Docker deployment
- 🔄 **Update:** Base URL from cloud to localhost:8080
- 🔄 **Remove:** Cloud API key authentication
- 🔄 **Add:** Local Docker infrastructure

**What Stays The Same:**
- All agent tools and functionality
- Dual ingestion pipeline logic
- Intelligent routing algorithms
- Graphiti knowledge graph system

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
- Use vector_search for semantic similarity across project documents
- Use graph_search for project entity relationships  
- Use hybrid_search for complex project queries
"""

# Enhanced System Prompt Strategy  
PROJECT_ROUTING = """
- Use onyx_search for project document discovery and factual questions
- Use onyx_answer_with_quote for comprehensive answers with project citations
- Use graph_search for stakeholder relationships and requirement dependencies
- Use get_entity_timeline for project decision history and evolution
- Use comprehensive_search for complex project analysis requiring multiple perspectives
"""
```

### **Data Flow Architecture**

```python
# Current Ingestion Flow
Project Document → Semantic Chunking → Gemini Embeddings → PostgreSQL
                ↘ Entity Extraction → Graphiti → Neo4j

# Enhanced Dual Ingestion Flow
Project Document → Semantic Chunking → ┌─ Onyx Cloud API → Multi-Client Vector Store
                                     └─ Project Entity Pipeline → Neo4j Knowledge Graph
                                     └─ Metadata Store → PostgreSQL
```

### **Search Strategy Matrix**

| Query Type | Current System | Enhanced System | Rationale |
|------------|---------------|-----------------|-----------|
| Project Questions | vector_search | onyx_answer_with_quote | Enterprise QA with project citations |
| Document Discovery | vector_search | onyx_search | Scalable project document search |
| Stakeholder Queries | graph_search | graph_search (unchanged) | Graphiti excels at relationships |
| Decision History | get_entity_timeline | get_entity_timeline | Graphiti's temporal strength |
| Complex Analysis | hybrid_search | comprehensive_search | Multi-system project intelligence |

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
1. **Onyx API Reliability** → Keep Graphiti as fallback system
2. **Performance Degradation** → Implement intelligent caching and optimization
3. **Data Consistency** → Build validation and synchronization mechanisms
4. **Migration Complexity** → Phased approach with comprehensive testing

### **Operational Risks & Mitigations:**
1. **Increased Complexity** → Comprehensive documentation and monitoring
2. **Cost Management** → Clear migration path to Community Edition
3. **Team Learning Curve** → Gradual rollout with extensive documentation

This architecture evolution maintains all existing strengths while adding enterprise-grade capabilities, positioning the system for both immediate enhancement and long-term scalability.