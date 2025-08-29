# 🤖 Development Context & Chat History
*Generated on August 26, 2025*

## 📊 **Project Overview**
**Project**: Hybrid Agentic RAG Knowledge Graph System
**Location**: `/Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph/`
**Status**: Production-ready, fully documented, and unified

## 🎯 **Task Description**
Deeply analyze, document, and update the hybrid RAG system that integrates:
- **Onyx Cloud** (Enterprise document search)
- **PostgreSQL + pgvector** (Semantic similarity search) 
- **Neo4j + Graphiti** (Temporal relationships)

Ensure all documentation and quick start materials are accurate, unified, and reflect the real implementation. Remove redundant documentation and ensure the main README.md is the single source of truth.

## ✅ **Completed Work**

### 1. **System Analysis & Architecture Understanding**
- Analyzed implementation and fallback logic of all 10 tools in `agent/tools.py`
- Verified Onyx Cloud integration with correct API endpoint `/api/chat/send-message-simple-api`
- Confirmed agent.py is the main Pydantic AI agent connecting API and CLI
- Understood the hybrid architecture with intelligent tool selection and fallback mechanisms

### 2. **Documentation Unification**
- **BEFORE**: Multiple scattered documentation files
  - `README.md` (incomplete)
  - `README_HYBRID_AGENT.md` (duplicate info)
  - `FINAL_LAUNCH_INSTRUCTIONS.md` (outdated)
  - `SETUP_AND_RUN_GUIDE.md` (redundant)

- **AFTER**: Single comprehensive `README.md` containing:
  - Complete system architecture overview
  - Detailed setup instructions with all prerequisites
  - API documentation with examples
  - Troubleshooting guide with common issues
  - Best practices and performance optimization
  - Full project structure documentation

### 3. **File Management**
- **Removed redundant files**:
  - `README_HYBRID_AGENT.md` ❌
  - `FINAL_LAUNCH_INSTRUCTIONS.md` ❌ 
  - `SETUP_AND_RUN_GUIDE.md` ❌
- **Updated and aligned**:
  - `README.md` ✅ (now comprehensive single source of truth)
  - `quick_start.py` ✅ (updated to match current architecture)

### 4. **Quick Start Script Enhancement**
Updated `quick_start.py` with:
- Accurate environment variable checks
- Removed non-existent file references
- Enhanced documentation accuracy
- Better setup instructions with concrete examples
- Verification that all referenced files exist

## 🏗️ **Current System Architecture**

### **Core Components**
```
agentic-rag-knowledge-graph/
├── 🤖 Agent System
│   ├── comprehensive_agent_api.py     # FastAPI backend server
│   ├── comprehensive_agent_cli.py     # Interactive CLI client  
│   ├── agent/
│   │   ├── agent.py                   # Main Pydantic AI agent
│   │   ├── tools.py                   # 10 specialized search tools
│   │   ├── prompts.py                 # System prompts
│   │   ├── providers.py               # LLM provider abstraction
│   │   ├── models.py                  # Pydantic data models
│   │   ├── db_utils.py                # Vector database utilities
│   │   └── graph_utils.py             # Knowledge graph utilities
├── 🔍 Onyx Integration
│   ├── onyx/service.py                # Onyx Cloud API client
│   ├── onyx/interface.py              # Service interface
│   └── onyx/config.py                 # Configuration management
├── 📄 Document Processing
│   ├── ingestion/ingest.py            # Main ingestion pipeline
│   ├── ingestion/chunker.py           # Semantic chunking
│   ├── ingestion/embedder.py          # Gemini embeddings
│   └── ingestion/graph_builder.py     # Knowledge graph construction
└── 🗄️ Configuration
    ├── sql/schema.sql                 # PostgreSQL + pgvector schema
    ├── requirements_final.txt         # Python dependencies
    ├── start_api.sh                   # Automated API startup
    └── start_cli.sh                   # Automated CLI startup
```

### **10 Specialized Agent Tools**
1. **`onyx_search`** - Advanced document search with relevance scoring
2. **`onyx_answer_with_quote`** - QA with citations and supporting quotes
3. **`vector_search`** - Semantic similarity search across document chunks
4. **`graph_search`** - Knowledge graph queries for facts and relationships
5. **`hybrid_search`** - Combined vector and keyword search
6. **`get_document`** - Retrieve complete document content
7. **`list_documents`** - Browse available documents with metadata
8. **`get_entity_relationships`** - Explore entity connections in knowledge graph
9. **`get_entity_timeline`** - Timeline analysis for specific entities
10. **`comprehensive_search`** - Multi-system search with intelligent synthesis

## 🔧 **Technical Configuration**

### **Required Environment Variables**
```env
# Google Gemini (Required)
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini
LLM_CHOICE=gemini-2.0-flash-thinking-exp-1219
EMBEDDING_MODEL=embedding-001

# Onyx Cloud (Optional but recommended)
ONYX_API_KEY=your_onyx_api_key_here
ONYX_BASE_URL=https://cloud.onyx.app

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Application
APP_PORT=8058
LOG_LEVEL=INFO
```

### **Technology Stack**
- **Pydantic AI** - Agent framework with tool orchestration
- **FastAPI** - High-performance API backend with streaming support
- **Google Gemini** - LLM and 768-dimensional embeddings
- **Onyx Cloud** - Enterprise document search and retrieval
- **PostgreSQL + pgvector** - Vector database for similarity search
- **Neo4j + Graphiti** - Knowledge graph and temporal relationships
- **Rich Terminal UI** - Beautiful CLI with real-time progress

## 🚀 **Quick Start Commands**

### **Status Check**
```bash
cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph
python3 quick_start.py
```

### **Document Ingestion**
```bash
python -m ingestion.ingest
```

### **Start System (2 Terminals)**
```bash
# Terminal 1: API Server
./start_api.sh
# or manually: python comprehensive_agent_api.py

# Terminal 2: CLI Client  
./start_cli.sh
# or manually: python comprehensive_agent_cli.py
```

## 🔍 **Key Insights from Development**

### **Tool Selection Logic**
- **Simple factual queries** → `graph_search` for precise facts
- **Document similarity** → `vector_search` for semantic matching
- **Complex analysis** → `comprehensive_search` for multi-system results
- **Enterprise documents** → `onyx_search` for advanced document retrieval
- **Cited answers** → `onyx_answer_with_quote` for authoritative responses

### **Fallback Mechanisms**
```
Query → Agent Decision
├── Onyx Available? → Try Onyx tools first
│   ├── Success → Continue with Graphiti for synthesis
│   └── Failure → Fallback to Graphiti tools only
└── Graphiti Available? → Use vector + graph search
    ├── Vector + Graph Success → Multi-system synthesis
    ├── Vector Success + Graph Failure → Vector-only results
    └── Vector Failure + Graph Success → Graph-only results
```

### **Common CLI Commands**
```bash
/help     - Show all available commands and usage
/health   - Check connectivity to all systems (Onyx + Graphiti)
/status   - Show current session and system information
/clear    - Clear conversation history
/quit     - Exit the CLI gracefully
```

## 🐛 **Known Issues & Solutions**

### **Environment Setup**
- **Python Version**: Requires Python 3.11+ for Pydantic AI compatibility
- **Port Conflicts**: Default port 8058 - change `APP_PORT` in .env if needed
- **API Keys**: Google Gemini free tier: 15 RPM, 1M tokens/day

### **Database Requirements**
- **PostgreSQL**: Must have pgvector extension installed
- **Neo4j**: Can use local Neo4j Desktop or cloud AuraDB
- **Schema**: 768-dimensional embeddings for Gemini's embedding-001 model

### **Common Error Patterns**
- **"Tools used: 4" with Onyx failures**: Normal behavior with resilient fallback
- **"No answer on attempt 1/2/3"**: Onyx service slow - agent falls back automatically
- **Vector search fails**: Check PostgreSQL connection and pgvector extension

## 📊 **Current Status**
- ✅ **Documentation**: Unified and comprehensive
- ✅ **Code**: Production-ready and tested
- ✅ **Setup Scripts**: Working and verified
- ✅ **Quick Start**: Accurate and up-to-date
- ✅ **Architecture**: Fully documented and understood

## 🎯 **Next Development Steps**
1. **System Ready**: All documentation unified, quick start updated
2. **No Major Tasks Pending**: System is production-ready
3. **Optional Enhancements**: Could add more specialized tools or UI improvements
4. **Monitoring**: Consider adding more comprehensive logging/metrics

## 🔄 **For New GitHub Copilot Session**
When starting a new chat session, provide this context:

1. **Project Location**: `/Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph/`
2. **Main Files**: `README.md`, `quick_start.py`, `agent/agent.py`, `agent/tools.py`
3. **Current State**: Fully documented hybrid RAG system with Onyx + Graphiti integration
4. **Architecture**: 10 specialized tools, intelligent fallback, multi-system synthesis
5. **Status**: Production-ready, all documentation unified in single README.md

This document captures the complete development context and should allow any new GitHub Copilot session to assist with the same level of understanding.
