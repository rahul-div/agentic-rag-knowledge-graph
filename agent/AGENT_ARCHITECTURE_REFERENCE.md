# 🤖 Hybrid RAG Agent Architecture - Complete Reference Guide

**Date:** August 22, 2025  
**Version:** Production Implementation  
**Author:** Comprehensive Code Analysis  

---

## 📋 Table of Contents

1. [Agent Overview](#agent-overview)
2. [System Architecture](#system-architecture)
3. [Tool Ecosystem](#tool-ecosystem)
4. [Comprehensive Search Pipeline](#comprehensive-search-pipeline)
5. [Execution Flow Analysis](#execution-flow-analysis)
6. [Dependency Injection Pattern](#dependency-injection-pattern)
7. [Fallback Strategy](#fallback-strategy)
8. [Technical Q&A](#technical-qa)

---

## 🎯 Agent Overview

### **Core Mission**
Your Hybrid RAG Agent combines three powerful search systems into a unified intelligence platform:

- **🏢 Onyx Cloud:** Enterprise document search with citations
- **🔍 Graphiti Vector:** Semantic similarity search across document chunks  
- **🕸️ Graphiti Knowledge Graph:** Entity relationships and temporal facts

### **Agent Foundation**
```python
# Built on Pydantic AI with flexible LLM support
rag_agent = Agent(
    get_llm_model(),              # Gemini, OpenAI, or Anthropic
    deps_type=AgentDependencies,  # Dependency injection container
    system_prompt=SYSTEM_PROMPT   # Intelligent tool selection guidance
)
```

---

## 🏗️ System Architecture

### **Three-Layer Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    🤖 AGENT LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │         LLM decides which tool to call                 │ │
│  │    (vector_search, onyx_search, comprehensive_search)  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   🔧 TOOL LAYER                             │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Individual │  │     Hybrid   │  │ Comprehensive│     │
│  │    Tools     │  │    Tools     │  │    Search    │     │
│  │              │  │              │  │              │     │
│  │ • vector     │  │ • hybrid     │  │ • Multi-sys  │     │
│  │ • graph      │  │ • get_doc    │  │ • Synthesis  │     │
│  │ • onyx       │  │ • list_docs  │  │ • Fallback   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 💾 DATA LAYER                               │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Onyx Cloud  │  │   pgvector   │  │    Neo4j     │     │
│  │              │  │              │  │              │     │
│  │ • Documents  │  │ • Embeddings │  │ • Entities   │     │
│  │ • Citations  │  │ • Similarity │  │ • Relations  │     │
│  │ • Chat API   │  │ • Chunks     │  │ • Temporal   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tool Ecosystem

### **10 Available Tools**

| **Category** | **Tool** | **Purpose** | **Returns** |
|--------------|----------|-------------|-------------|
| **Individual** | `vector_search` | Semantic similarity search | `List[ChunkResult]` |
| **Individual** | `graph_search` | Knowledge graph facts | `List[GraphSearchResult]` |
| **Individual** | `hybrid_search` | Vector + keyword combo | `List[ChunkResult]` |
| **Individual** | `onyx_search` | Onyx document search | `Dict[str, Any]` |
| **Individual** | `onyx_answer_with_quote` | Onyx QA with citations | `Dict[str, Any]` |
| **🔥 MASTER** | `comprehensive_search` | **Multi-system synthesis** | `Dict[str, Any]` |
| **Utility** | `get_document` | Retrieve specific document | `Optional[Dict]` |
| **Utility** | `list_documents` | Browse available docs | `List[DocumentMetadata]` |
| **Utility** | `get_entity_relationships` | Entity relationship map | `Dict[str, Any]` |
| **Utility** | `get_entity_timeline` | Temporal entity facts | `List[Dict]` |

### **Tool Selection Logic**

The agent's LLM intelligently selects tools based on query characteristics:

```python
# Query Type → Tool Selection Examples
"What is X?" → vector_search (simple factual)
"Who works with whom?" → graph_search (relationships)  
"Find documents about Y" → onyx_search (document-focused)
"Explain the relationships between A and B" → comprehensive_search (complex)
"Tell me everything about Z" → comprehensive_search (comprehensive)
```

---

## 🔄 Comprehensive Search Pipeline

### **The Master Tool: `comprehensive_search_tool`**

This is your most sophisticated tool that orchestrates all three systems:

```python
async def comprehensive_search_tool(
    input_data: ComprehensiveSearchInput, 
    onyx_service=None, 
    document_set_id=None
) -> Dict[str, Any]
```

### **Three-Phase Execution**

#### **Phase 1: Onyx Cloud (Primary System)**
```python
# SEQUENTIAL EXECUTION - Onyx runs first
if input_data.include_onyx and onyx_service is not None:
    onyx_result = await onyx_search_tool(onyx_input, onyx_service, document_set_id)
    # Process Onyx results immediately
    if onyx_result.get("success", False):
        onyx_success = True
        # Continue to Phase 2 for synthesis
```

#### **Phase 2: Graphiti Systems (Parallel Execution)**
```python
# PARALLEL EXECUTION - Vector and Graph run simultaneously
graphiti_tasks = []
if input_data.include_vector:
    graphiti_tasks.append(("vector", vector_search_tool(...)))
if input_data.include_graph:
    graphiti_tasks.append(("graph", graph_search_tool(...)))

# 🔥 KEY: asyncio.gather executes in PARALLEL
search_results = await asyncio.gather(
    *[task for _, task in graphiti_tasks],
    return_exceptions=True
)
```

#### **Phase 3: Intelligent Synthesis**
```python
# Multi-system result combination based on success patterns
if onyx_success and (vector_results or graph_results):
    # TRUE COMPREHENSIVE SYNTHESIS
    synthesis_type = "comprehensive_multi_system"
elif onyx_success:
    synthesis_type = "onyx_primary" 
elif vector_results or graph_results:
    synthesis_type = "vector_graph_synthesis"
```

---

## 🔍 Execution Flow Analysis

### **Detailed Breakdown: Comprehensive Search**

Let me trace through your actual code execution:

#### **Step 1: Task Creation (Lines 726-736)**
```python
# Both tasks are created but NOT executed yet
graphiti_tasks = []
if input_data.include_vector:
    results["fallback_chain"].append("vector_search_started")
    graphiti_tasks.append(("vector", vector_search_tool(VectorSearchInput(...))))

if input_data.include_graph:  
    results["fallback_chain"].append("graph_search_started")
    graphiti_tasks.append(("graph", graph_search_tool(GraphSearchInput(...))))

# graphiti_tasks = [("vector", <coroutine>), ("graph", <coroutine>)]
```

#### **Step 2: Parallel Execution (Lines 739-744)**
```python
if graphiti_tasks:
    logger.info(f"Running Graphiti fallback with {len(graphiti_tasks)} search types")
    
    # 🔥 CRITICAL: asyncio.gather runs ALL coroutines in PARALLEL
    search_results = await asyncio.gather(
        *[task for _, task in graphiti_tasks],  # Extracts coroutines
        return_exceptions=True
    )
    # search_results = [vector_result, graph_result] (in parallel execution order)
```

#### **Step 3: Result Processing (Lines 745-766)**
```python
# Process BOTH results that executed in parallel
for i, (search_type, search_result) in enumerate(zip([t[0] for t in graphiti_tasks], search_results)):
    # [t[0] for t in graphiti_tasks] = ["vector", "graph"]
    # search_results = [vector_result, graph_result]
    # zip creates: [("vector", vector_result), ("graph", graph_result)]
    
    if search_type == "vector" and search_result:
        # Process vector results
        results["vector_results"] = search_result
        
    elif search_type == "graph" and search_result:  
        # Process graph results  
        results["graph_results"] = search_result
```

### **🎯 Answer to Your Question: Why `if` and `elif`?**

The `if` and `elif` pattern exists because:

1. **Different Tasks Can Execute:** Depending on `input_data.include_vector` and `input_data.include_graph`, you might have:
   - Only vector task: `graphiti_tasks = [("vector", ...)]`
   - Only graph task: `graphiti_tasks = [("graph", ...)]`  
   - Both tasks: `graphiti_tasks = [("vector", ...), ("graph", ...)]`

2. **Processing Order Matters:** The `zip()` maintains the relationship between task type and result:
   ```python
   # If both enabled:
   graphiti_tasks = [("vector", <coro1>), ("graph", <coro2>)]
   search_results = [result1, result2]  # From parallel execution
   
   # zip creates: [("vector", result1), ("graph", result2)]
   ```

3. **Mutually Exclusive Processing:** Each result can only be one type:
   - `if search_type == "vector"` → Process as vector result
   - `elif search_type == "graph"` → Process as graph result
   - Cannot be both simultaneously

4. **Graceful Partial Execution:** If only vector is enabled:
   ```python
   graphiti_tasks = [("vector", <coro>)]
   search_results = [vector_result] 
   # Only the "vector" condition triggers, "graph" elif is skipped
   ```

**In Summary:** Both vector and graph searches run **IN PARALLEL** during Phase 2, but they are processed **SEQUENTIALLY** during result handling because each result needs different processing logic.

---

## 🔧 Dependency Injection Pattern

### **AgentDependencies Structure**
```python
@dataclass
class AgentDependencies:
    session_id: str
    onyx_service: Optional[Any] = None           # Injected OnyxService
    onyx_document_set_id: Optional[int] = None   # Document set for searches
    user_id: Optional[str] = None
    search_preferences: Dict[str, Any] = None    # System enable/disable flags
```

### **Initialization Flow**
```python
async def create_hybrid_agent_dependencies(session_id: str, cc_pair_id: int = 285):
    dependencies = AgentDependencies(session_id=session_id)
    
    # Step 1: Test Onyx connectivity
    personas = onyx_service.get_personas()  # 🔍 See Q&A section
    
    # Step 2: Verify CC-pair and create document set
    document_set_id = onyx_service.create_document_set_validated(cc_pair_id=285)
    
    # Step 3: Configure dependencies
    dependencies.onyx_service = onyx_service
    dependencies.onyx_document_set_id = document_set_id
    
    return dependencies
```

---

## 🔄 Fallback Strategy

### **Intelligent Cascading Fallback**

```
┌─────────────────────────────────────────────────────────────┐
│                    FALLBACK CHAIN                           │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │    ONYX     │    │   GRAPHITI  │    │   GRACEFUL  │    │
│  │   CLOUD     │───▶│   SYSTEMS   │───▶│    ERROR    │    │
│  │             │    │             │    │             │    │
│  │ • Doc Sets  │    │ • Vector DB │    │ • User Msg  │    │
│  │ • Citations │    │ • Knowledge │    │ • Logging   │    │
│  │ • 3 Retries │    │   Graph     │    │ • Monitoring│    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### **Fallback Chain Examples**
```python
# Best case (all systems work):
"onyx_attempted -> onyx_success -> vector_search_started -> graph_search_started 
 -> vector_success -> graph_success -> multi_system_synthesis_complete"

# Onyx fails, Graphiti succeeds:
"onyx_attempted -> onyx_failed -> vector_search_started -> graph_search_started
 -> vector_success -> graph_success -> vector_graph_synthesis"

# Everything fails:
"onyx_attempted -> onyx_error -> vector_search_started -> vector_error 
 -> graph_search_started -> graph_error -> graceful_degradation"
```

---

## 📊 Synthesis Strategies

### **Multi-System Response Synthesis**

| **Scenario** | **Synthesis Type** | **Confidence** | **Structure** |
|--------------|-------------------|----------------|---------------|
| All systems succeed | `comprehensive_multi_system` | `very_high` | Onyx primary + Graph relationships + Vector evidence |
| Only Onyx succeeds | `onyx_primary` | `high` | Direct Onyx answer with citations |
| Only Graphiti succeeds | `vector_graph_synthesis` | `medium` | Best vector + Graph relationships |
| Only Vector succeeds | `vector_primary` | `medium` | Best similarity match |
| Only Graph succeeds | `graph_primary` | `low` | Graph facts summary |
| Nothing succeeds | `no_results` | `none` | Error message with guidance |

### **Example Synthesis Output**

```markdown
**Primary Answer (Onyx Cloud):** Aanya Sharma is currently the Chief Product Officer at Cerebro AI as of July 2025. She oversees the Infra, ML Research, and AI Product teams [[1]]().

**Relationship Context (Knowledge Graph):** Aanya Sharma is living in Bangalore. | Her favorite coffee shop is Third Wave Coffee, Indiranagar.

**Supporting Evidence (Vector Search):** Additional context from 2 supporting sources: She mentors a group of interns, one of whom, **Rahul Mehta**, prefers **One UI over Pixel UI**.
```

---

## 🎛️ Agent Usage Examples

### **Creating an Agent Instance**
```python
# Simple creation with defaults
agent, deps = await create_hybrid_rag_agent()

# Advanced creation with configuration  
agent, deps = await create_hybrid_rag_agent(
    session_id="custom_session_123",
    cc_pair_id=285,  # Validated CC-pair
    enable_onyx=True
)
```

### **Running Queries**
```python
# The agent automatically selects the best tool
result = await agent.run("Tell me about Aanya's coffee preferences", deps=deps)

# User gets synthesized response, not raw tool output
print(result.data)  # Natural language response
```

---

## ❓ Technical Q&A

### **Q1: What are "personas" in Onyx Cloud?**

**Answer:** Personas in Onyx Cloud are **user profile configurations** that define:

- **Search permissions** (which documents a user can access)
- **Response styling** (how answers should be formatted)  
- **Domain expertise** (specialized knowledge areas)
- **Access controls** (security and privacy settings)

In your code, `get_personas()` is used as a **connectivity test**:

```python
# Step 1: Test basic connectivity with a simple call
personas = onyx_service.get_personas()
if not personas:
    logger.error(f"❌ Onyx API not accessible - no personas returned")
    # Disable Onyx integration
else:
    logger.info(f"✅ Onyx API accessible - {len(personas)} personas found")
    # Continue with full setup
```

This is a lightweight API call that verifies:
- ✅ Network connectivity to Onyx Cloud
- ✅ Authentication credentials are valid  
- ✅ API service is responding
- ✅ User has basic access permissions

### **Q2: Do vector and graph searches run in parallel or sequentially?**

**Answer:** They run **IN PARALLEL** during execution, but are processed **SEQUENTIALLY** during result handling.

**Code Evidence:**

```python
# PHASE 2A: Task Creation (Sequential)
graphiti_tasks = []
if input_data.include_vector:
    graphiti_tasks.append(("vector", vector_search_tool(...)))  # Creates coroutine
if input_data.include_graph:
    graphiti_tasks.append(("graph", graph_search_tool(...)))    # Creates coroutine

# PHASE 2B: Execution (PARALLEL) 
search_results = await asyncio.gather(
    *[task for _, task in graphiti_tasks],  # Extracts all coroutines
    return_exceptions=True
)
# 🔥 asyncio.gather() runs ALL coroutines simultaneously

# PHASE 2C: Processing (Sequential)
for i, (search_type, search_result) in enumerate(zip([t[0] for t in graphiti_tasks], search_results)):
    if search_type == "vector" and search_result:        # Process vector result
        results["vector_results"] = search_result
    elif search_type == "graph" and search_result:      # Process graph result  
        results["graph_results"] = search_result
```

**Execution Timeline:**
```
Time 0: Start vector_search_tool() and graph_search_tool() simultaneously
Time 1: Both searches running in parallel
Time 2: Both complete, results available  
Time 3: Process vector result sequentially
Time 4: Process graph result sequentially
```

### **Q3: Why use `if` and `elif` for result processing?**

**Answer:** Because each search result can only be **one type**, and the code handles **different execution scenarios**:

**Scenario A: Both Vector and Graph Enabled**
```python
graphiti_tasks = [("vector", <coro1>), ("graph", <coro2>)]
search_results = [vector_result, graph_result]  # Both executed in parallel

# Processing:
# i=0: search_type="vector", search_result=vector_result → if condition
# i=1: search_type="graph", search_result=graph_result → elif condition
```

**Scenario B: Only Vector Enabled**
```python
graphiti_tasks = [("vector", <coro>)]
search_results = [vector_result]  # Only vector executed

# Processing:
# i=0: search_type="vector", search_result=vector_result → if condition
# elif never triggers because loop only has 1 iteration
```

**Scenario C: Only Graph Enabled**
```python
graphiti_tasks = [("graph", <coro>)]
search_results = [graph_result]  # Only graph executed

# Processing:  
# i=0: search_type="graph", search_result=graph_result → elif condition
# if condition fails because search_type != "vector"
```

The `if/elif` pattern ensures **each result is processed exactly once** with the **correct logic for its type**.

---

## 🚀 Performance Characteristics

### **Typical Response Times**
- **Onyx Cloud:** 2-5 seconds (document set search)
- **Vector Search:** 0.5-2 seconds (similarity computation)
- **Graph Search:** 0.8-3 seconds (relationship traversal)
- **Total Comprehensive:** 3-8 seconds (parallel execution)

### **Fallback Behavior**
- **Onyx Failure:** Immediate fallback to Graphiti (no delay)
- **Partial Success:** Best available results synthesis
- **Complete Failure:** Graceful error with user guidance

---

## 📁 File Structure Reference

```
agent/
├── agent.py           # Main agent definition & tool registration
├── tools.py           # All tool implementations & comprehensive search
├── models.py          # Data models (ChunkResult, GraphSearchResult, etc.)
├── prompts.py         # System prompts for tool selection
├── providers.py       # LLM provider configuration
├── db_utils.py        # Database interaction utilities
└── graph_utils.py     # Knowledge graph utilities
```

---

## 🎯 Key Takeaways

1. **🤖 Agent Intelligence:** LLM selects the best tool based on query complexity
2. **⚡ Parallel Execution:** Vector and Graph searches run simultaneously for speed
3. **🔄 Smart Fallback:** Graceful degradation from Onyx → Graphiti → Error
4. **🧠 Synthesis:** Multi-system responses provide comprehensive answers
5. **🔧 Dependency Injection:** Clean separation of concerns with injectable services
6. **📊 Comprehensive Coverage:** 10 tools covering all search scenarios

Your implementation represents a **production-grade hybrid RAG system** with intelligent orchestration, robust error handling, and sophisticated result synthesis!

---

**Document Version:** 1.0  
**Last Updated:** August 22, 2025  
**Implementation Status:** ✅ Production Ready
