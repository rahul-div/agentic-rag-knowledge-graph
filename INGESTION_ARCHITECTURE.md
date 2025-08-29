# Ingestion Architecture Overview

## 🏗️ **Two-Pipeline Architecture**

Your hybrid RAG system implements **two distinct ingestion pipelines** corresponding to **two distinct retrieval paths**:

## 🔍 **Pipeline 1: Triple System Ingestion** 

**Location**: `Triple_Ingestion_Pipeline/`

**Main Script**: `unified_ingest_complete.py`

**Systems Covered**:
- **Cloud Path:** 🔮 **Onyx Enterprise Search** - Scalable document search and retrieval
- **Local Path:** 🏠 **Dual Storage** - Complete local retrieval system
  - 🔍 **pgvector**: Semantic similarity search using PostgreSQL + pgvector extension
  - 🕸️ **Neo4j + Graphiti**: Entity relationship discovery and temporal knowledge graph analysis

**Key Features**:
- Production-ready CLI with multiple options
- Three Onyx modes: existing, new connector, skip
- Comprehensive error handling and logging
- Integration testing suite

**Usage**:
```bash
cd Triple_Ingestion_Pipeline
python unified_ingest_complete.py --verbose
```

## 🧠 **Pipeline 2: Local Path: Dual Storage Only**

**Location**: `ingestion/`

**Main Script**: `ingest.py`


**Systems Covered**:
- **Path 2 Only:** 🏠 **Local Path: Dual Storage** - Complete local retrieval system
  - 📊 **Neo4j + Graphiti** - Entity relationships and temporal tracking
  - 🔍 **PostgreSQL + pgvector** - Semantic similarity search

**Key Features**:
- Focused on knowledge graph construction
- Semantic chunking with LLM
- Entity extraction and relationship mapping
- Optimized for Graphiti temporal intelligence

**Usage**:
```bash
python -m ingestion.ingest --verbose
```

## 🔧 **Supporting Modules**

### **Onyx Integration** (used by Triple Pipeline)
- **`ingestion/onyx_ingest.py`** - Onyx Cloud API integration
- **`ingestion/onyx_cloud_integration.py`** - Standalone connector workflow

### **Shared Components**
- **`ingestion/chunker.py`** - Semantic document chunking
- **`ingestion/embedder.py`** - Google Gemini embeddings  
- **`ingestion/graph_builder.py`** - Knowledge graph construction

## 🎯 **Which Pipeline to Use?**

| Use Case | Recommended Pipeline | Retrieval Paths |
|----------|---------------------|-----------------|
| **Complete hybrid RAG** | **Triple Ingestion** | Path 1 (Onyx Cloud) + Path 2 (Local Path: Dual Storage) |
| **Local focus only** | **Local Path: Dual Storage Only** | Path 2 Only (pgvector + Neo4j + Graphiti) |
| **Testing different approaches** | **Both pipelines** | Compare retrieval path effectiveness |
| **Production deployment** | **Triple Ingestion** | Full hybrid capabilities |

## 🔄 **Pipeline Interaction**

Both pipelines share:
- Same database schemas (PostgreSQL + pgvector and Neo4j)
- Same document processing logic
- Same embedding generation (Gemini 768-dimensional)
- Compatible with the same agent tools

**Key Difference**: Triple pipeline additionally handles Onyx Cloud ingestion (Path 1) while Local Path: Dual Storage pipeline focuses only on Path 2 (pgvector + Neo4j + Graphiti working together).

## 📍 **Remember: Local Path: Dual Storage = pgvector + Neo4j + Graphiti**

When referring to "Local Path: Dual Storage" it always means **both independent systems coordinating together**:
- **PostgreSQL + pgvector** for semantic similarity search
- **Neo4j + Graphiti** for entity relationships and temporal tracking