# 🤖 Hybrid Agentic RAG Knowledge Graph System

A comprehensive **hybrid RAG system** that intelligently combines **Onyx Cloud enterprise search**, **Graphiti vector similarity search**, and **Graphiti knowledge graph search** into a unified intelligent agent platform. This system provides deep insights and relationship analysis across multiple data sources with automatic tool selection and fallback mechanisms.

## 🚀 **System Architecture Overview**

This hybrid system seamlessly integrates three powerful search technologies:

- **🔍 Onyx Cloud**: Enterprise-grade document search with advanced semantic understanding and citation capabilities
- **🧠 Graphiti Vector**: High-performance semantic similarity search using Google Gemini embeddings (768 dimensions)
- **🕸️ Graphiti Knowledge Graph**: Temporal relationship discovery and entity analysis powered by Neo4j
- **🤖 Intelligent Agent**: Pydantic AI agent that automatically selects optimal tools and provides fallback resilience

### **Key Features:**
- **🎯 Intelligent Tool Selection**: Agent automatically chooses the best search strategy for each query
- **🔄 Comprehensive Fallback Logic**: Graceful degradation when individual systems are unavailable  
- **⚡ Real-time Streaming**: Live response generation with full tool usage transparency
- **📊 Multi-System Synthesis**: Combines results from all available systems for comprehensive answers
- **🛡️ Enterprise Ready**: Robust error handling, retry logic, and production-grade logging

## 🔧 Quick Start (Recommended)

### Option 1: Automated Scripts (Fastest)

**Terminal 1 - Start API Server:**
```bash
cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph
./start_api.sh
```

**Terminal 2 - Start CLI Client:**
```bash
cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph
./start_cli.sh
```

### Option 2: Manual Setup

**Terminal 1 - API Server:**
```bash
cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph
source .venv/bin/activate  # or venv/bin/activate
python comprehensive_agent_api.py
```

**Terminal 2 - CLI Client:**
```bash
cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph
source .venv/bin/activate  # or venv/bin/activate
python comprehensive_agent_cli.py
```

## 🎯 Technology Stack

- **🤖 Pydantic AI** - Agent framework with tool orchestration
- **⚡ FastAPI** - High-performance API backend with streaming support
- **🔍 Onyx Cloud** - Enterprise document search and retrieval
- **🧠 Google Gemini** - LLM and embedding generation (cost-effective, high-quality)
- **🕸️ Graphiti** - Knowledge graph and vector search capabilities
- **🗄️ PostgreSQL + pgvector** - Vector database for similarity search
- **📊 Neo4j** - Graph database for relationship discovery
- **🖥️ Rich Terminal UI** - Beautiful CLI with real-time progress and colored output

## 📋 Prerequisites

### System Requirements
- **Python 3.11+** (Pydantic AI compatibility)
- **PostgreSQL** with pgvector extension
- **Neo4j** database (local or cloud)
- **Port 8058** available for FastAPI server

### Required API Keys
- **Google Gemini API Key** ([Get it here](https://aistudio.google.com/))
- **Onyx Cloud API Key** (for enterprise document search)

### Virtual Environment
```bash
# Ensure you have a virtual environment set up
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows
pip install -r requirements_final.txt
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following configuration:

```env
# Google Gemini Configuration (Required)
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini
LLM_CHOICE=gemini-2.0-flash-thinking-exp-1219
EMBEDDING_MODEL=embedding-001

# Onyx Cloud Configuration (Required for enterprise search)
ONYX_API_KEY=your_onyx_api_key_here
ONYX_BASE_URL=https://cloud.onyx.app

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Application Configuration
APP_ENV=development
APP_PORT=8058
LOG_LEVEL=INFO
```

### Alternative LLM Providers (Optional)

```env
# OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-key
LLM_CHOICE=gpt-4o-mini

# Ollama (Local)
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_CHOICE=qwen2.5:14b-instruct

# OpenRouter
LLM_PROVIDER=openrouter
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_CHOICE=anthropic/claude-3-5-sonnet
```

## 🗄️ Database Setup

### PostgreSQL with pgvector

```bash
# Install pgvector extension
# Execute sql/schema.sql to create tables
psql -d "$DATABASE_URL" -f sql/schema.sql
```

**Important**: The schema script sets embedding dimensions to **768** for Gemini's `embedding-001` model. If using other embedding models, update the dimensions in the schema file.

### Neo4j Setup

#### Option A: Local Neo4j Desktop (Recommended)

1. Download [Neo4j Desktop](https://neo4j.com/download/)
2. Create a new project and local DBMS
3. Set password and start the database
4. Note connection details for `.env` configuration

#### Option B: Neo4j Cloud (AuraDB)

1. Create account at [Neo4j Aura](https://neo4j.com/cloud/aura/)
2. Create a free AuraDB instance
3. Download connection credentials
4. Update `.env` with cloud connection details

## 📄 Document Ingestion Pipeline

### Prepare Your Documents

Add your documents to the `documents/` folder:

```bash
mkdir -p documents
# Add your documentation files
# Supported formats: .md, .txt files
```

**Document Types That Work Best:**
- Project requirements and specifications
- Meeting notes and decision records
- Technical architecture documents
- Stakeholder analysis and communication logs
- Status reports and project updates
- Risk assessments and mitigation plans

### Run Document Ingestion

**Important**: You must run ingestion first to populate the databases before the agent can provide meaningful responses.

```bash
# Standard ingestion with Graphiti knowledge graph
python -m ingestion.ingest

# Clean existing data and re-ingest
python -m ingestion.ingest --clean

# Faster processing without knowledge graph
python -m ingestion.ingest --no-semantic --verbose
```

The ingestion process will:
- Parse and semantically chunk your documents using Google Gemini
- Generate embeddings for vector search (768-dimensional)
- Extract entities and relationships for knowledge graph
- Store everything in PostgreSQL and Neo4j databases

**Note**: Knowledge graph creation can be computationally intensive and may take considerable time for large document sets.

## 🤖 Intelligent Agent System

### Core Agent Features

The hybrid agent (`agent/agent.py`) includes 10 specialized tools:

#### **Onyx Cloud Tools** (Enterprise Search)
1. **`onyx_search`** - Advanced document search with relevance scoring
2. **`onyx_answer_with_quote`** - QA with citations and supporting quotes

#### **Graphiti Tools** (Vector & Knowledge Graph)
3. **`vector_search`** - Semantic similarity search across document chunks
4. **`graph_search`** - Knowledge graph queries for facts and relationships
5. **`hybrid_search`** - Combined vector and keyword search
6. **`get_document`** - Retrieve complete document content
7. **`list_documents`** - Browse available documents with metadata
8. **`get_entity_relationships`** - Explore entity connections in knowledge graph
9. **`get_entity_timeline`** - Timeline analysis for specific entities
10. **`comprehensive_search`** - Multi-system search with intelligent synthesis

### Tool Selection Intelligence

The agent automatically selects optimal tools based on query characteristics:

- **Simple factual queries** → `graph_search` for precise facts
- **Document similarity** → `vector_search` for semantic matching
- **Complex analysis** → `comprehensive_search` for multi-system results
- **Enterprise documents** → `onyx_search` for advanced document retrieval
- **Cited answers** → `onyx_answer_with_quote` for authoritative responses with sources

### Fallback and Resilience

The system includes robust fallback mechanisms:

```
Query → Agent Decision
├── Onyx Available? → Try Onyx tools first
│   ├── Success → Continue with Graphiti for synthesis
│   └── Failure → Fallback to Graphiti tools only
└── Graphiti Available? → Use vector + graph search
    ├── Vector Success + Graph Success → Multi-system synthesis
    ├── Vector Success + Graph Failure → Vector-only results
    └── Vector Failure + Graph Success → Graph-only results
```

## 🎮 Usage & Examples

### Interactive CLI Experience

The CLI provides the best development experience with real-time feedback:

```bash
# Start CLI (after API server is running)
python comprehensive_agent_cli.py
```

#### CLI Features

- **🔄 Real-time streaming**: Watch the agent's response generate in real-time
- **🛠️ Tool transparency**: See exactly which tools the agent uses for each query
- **📊 System status**: Monitor health of all integrated systems
- **💬 Session management**: Conversation continuity across interactions
- **🎨 Rich terminal UI**: Color-coded output and formatted responses

#### CLI Commands

```text
/help     - Show all available commands and usage
/health   - Check connectivity to all systems (Onyx + Graphiti)
/status   - Show current session and system information
/clear    - Clear conversation history
/quit     - Exit the CLI gracefully
```

#### Example CLI Session

```text
🤖 Hybrid RAG Agent CLI
============================================================
Connected to API: http://localhost:8058

You: What are the main technical modules in our financial system?

🤖 Assistant:
Based on comprehensive search across all systems, the financial system consists of several key technical modules...

🛠️ Tools Used: 4
  1. onyx_search - Found 31 enterprise documents
  2. vector_search - Retrieved 5 semantically similar chunks  
  3. graph_search - Discovered entity relationships
  4. comprehensive_search - Multi-system synthesis

📊 Response generated in 12.4s using Onyx + Graphiti synthesis
────────────────────────────────────────────────────────────

You: Show me the timeline of authentication decisions

🤖 Assistant:
Here's the chronological timeline of authentication-related decisions...

🛠️ Tools Used: 2
  1. get_entity_timeline - Temporal analysis for "authentication"
  2. get_entity_relationships - Related system dependencies

📊 Response generated in 3.2s using Knowledge Graph only
────────────────────────────────────────────────────────────
```

### Common Query Patterns

The system excels at different types of queries:

**📋 Document Discovery**
```text
"What documents are available about user authentication?"
→ Uses: list_documents, vector_search
```

**🔍 Factual Questions**
```text
"What is the status of the payment gateway integration?"
→ Uses: onyx_search, graph_search for comprehensive facts
```

**🕸️ Relationship Analysis**
```text
"How do the authentication and authorization modules interact?"
→ Uses: get_entity_relationships, comprehensive_search
```

**📈 Temporal Analysis**
```text
"Show me how the security requirements evolved over time"
→ Uses: get_entity_timeline, onyx_answer_with_quote
```

**🎯 Comprehensive Research**
```text
"Give me a complete analysis of the financial reporting system"
→ Uses: comprehensive_search (all tools in intelligent sequence)
```

## 🌐 API Documentation

### Health Check

```bash
curl http://localhost:8058/health
```

**Response:**
```json
{
  "status": "healthy",
  "systems": {
    "database": "connected",
    "neo4j": "connected", 
    "onyx": "connected",
    "gemini": "connected"
  }
}
```

### Chat Endpoint (Non-streaming)

```bash
curl -X POST "http://localhost:8058/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key technical dependencies?",
    "session_id": "my_session_123"
  }'
```

### Streaming Chat (Recommended)

```bash
curl -X POST "http://localhost:8058/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze the system architecture decisions",
    "session_id": "my_session_123"
  }'
```

**Interactive API Documentation**: Visit `http://localhost:8058/docs` when the server is running.

## 🏗️ System Architecture Deep Dive

### How the Hybrid RAG System Works

This system represents a **next-generation RAG architecture** that combines the best of multiple search paradigms:

#### **1. Onyx Cloud Integration (Enterprise Layer)**
- **Advanced Document Search**: Sophisticated semantic understanding with enterprise-grade relevance scoring
- **Citation-Based QA**: Generates authoritative answers with proper source citations
- **Document Set Management**: Organized document collections with metadata and access control
- **Fallback Resilience**: Graceful degradation when cloud services are unavailable

#### **2. Graphiti Vector Database (Semantic Layer)**  
- **High-Performance Similarity Search**: 768-dimensional Google Gemini embeddings with pgvector optimization
- **Semantic Chunking**: Intelligent document splitting using LLM analysis for optimal context preservation
- **Fast Retrieval**: Sub-second search across large document collections
- **Contextual Relevance**: Returns semantically related content regardless of keyword matching

#### **3. Graphiti Knowledge Graph (Relationship Layer)**
- **Temporal Entity Tracking**: Understands how information and relationships evolve over time
- **Graph Traversal**: Discovers hidden connections between entities, concepts, and decisions
- **Relationship Discovery**: Maps complex interdependencies between system components
- **Timeline Analysis**: Tracks the evolution of requirements, decisions, and system changes

#### **4. Intelligent Agent Orchestration (Decision Layer)**
- **Automatic Tool Selection**: Chooses optimal search strategy based on query characteristics and system availability
- **Multi-System Synthesis**: Combines results from all available systems for comprehensive responses
- **Fallback Chains**: Maintains service availability even when individual components fail
- **Response Optimization**: Balances speed, accuracy, and comprehensiveness based on query complexity

### Why This Architecture is Powerful

1. **🎯 Complementary Strengths**: Each system excels at different types of queries
   - **Onyx**: Best for enterprise document search and authoritative answers
   - **Vector Search**: Excellent for semantic similarity and fuzzy matching  
   - **Knowledge Graph**: Perfect for relationship discovery and temporal analysis

2. **🔄 Intelligent Orchestration**: The agent automatically chooses the best approach
   - Simple facts → Knowledge graph for precision
   - Document similarity → Vector search for semantic matching
   - Complex analysis → Multi-system comprehensive search
   - Enterprise queries → Onyx cloud for advanced capabilities

3. **🛡️ Resilient Design**: System remains functional even with partial failures
   - Onyx unavailable → Falls back to Graphiti systems
   - Vector search fails → Uses knowledge graph only
   - Knowledge graph unavailable → Relies on vector similarity

4. **📈 Scalable Performance**: Each component optimized for its strengths
   - Onyx handles enterprise-scale document collections
   - PostgreSQL + pgvector provides fast similarity search
   - Neo4j enables complex graph traversals
   - Pydantic AI manages intelligent tool coordination

## 📁 Project Structure

```
agentic-rag-knowledge-graph/
├── 🤖 Agent System
│   ├── comprehensive_agent_api.py     # FastAPI backend server
│   ├── comprehensive_agent_cli.py     # Interactive CLI client  
│   ├── agent/
│   │   ├── agent.py                   # Main Pydantic AI agent
│   │   ├── tools.py                   # 10 specialized search tools
│   │   ├── prompts.py                 # System prompts and instructions
│   │   ├── providers.py               # LLM provider abstraction
│   │   ├── models.py                  # Pydantic data models
│   │   ├── db_utils.py                # Vector database utilities
│   │   └── graph_utils.py             # Knowledge graph utilities
│
├── 🔍 Onyx Integration
│   ├── onyx/
│   │   ├── service.py                 # Onyx Cloud API client
│   │   ├── interface.py               # Service interface definition
│   │   └── config.py                  # Configuration management
│
├── 📄 Document Processing
│   ├── ingestion/
│   │   ├── ingest.py                  # Main ingestion pipeline
│   │   ├── chunker.py                 # Semantic document chunking
│   │   ├── embedder.py                # Google Gemini embeddings
│   │   └── graph_builder.py           # Knowledge graph construction
│
├── 🗄️ Database & Configuration
│   ├── sql/schema.sql                 # PostgreSQL + pgvector schema
│   ├── documents/                     # Your input documents
│   ├── requirements_final.txt         # Python dependencies
│   ├── .env                          # Environment configuration
│   ├── start_api.sh                  # Automated API startup
│   └── start_cli.sh                  # Automated CLI startup
│
└── 📚 Documentation
    ├── README.md                      # This comprehensive guide
    ├── SETUP_AND_RUN_GUIDE.md        # Detailed setup instructions
    ├── FINAL_LAUNCH_INSTRUCTIONS.md  # Quick launch guide
    └── Implementation/                # Technical implementation docs
```

## 🧪 Testing & Development

### Health Monitoring

The system provides comprehensive health monitoring:

```bash
# Check all systems
curl http://localhost:8058/health

# CLI health command
/health
```

**Health Check Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-26T10:30:00Z",
  "systems": {
    "database": {"status": "connected", "latency_ms": 12},
    "neo4j": {"status": "connected", "nodes": 1247, "relationships": 892},
    "onyx": {"status": "connected", "document_sets": 3},
    "gemini": {"status": "connected", "model": "gemini-2.0-flash-thinking-exp-1219"}
  },
  "agent": {
    "tools_available": 10,
    "fallback_ready": true
  }
}
```

### Development Features

- **📊 Comprehensive Logging**: Detailed logs for debugging and monitoring
- **🔄 Hot Reloading**: FastAPI auto-reloads on code changes
- **🛠️ Tool Introspection**: See exactly which tools the agent uses and why
- **📈 Performance Metrics**: Response times, tool usage, and system performance
- **🚨 Error Handling**: Graceful error recovery with detailed error reporting

## 🚨 Troubleshooting

### Common Setup Issues

#### **Virtual Environment Problems**
```bash
# Recreate virtual environment if corrupted
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_final.txt
```

#### **Port Conflicts (8058 in use)**
```bash
# Check what's using port 8058
lsof -i :8058

# Kill the process if needed
kill -9 [PID]

# Or change port in .env
APP_PORT=8059
```

#### **Database Connection Issues**
```bash
# Test PostgreSQL connection
psql -d "$DATABASE_URL" -c "SELECT 1;"

# Test Neo4j connection (adjust credentials)
curl -u neo4j:password http://localhost:7474/db/data/
```

#### **API Key Issues**
- **Google Gemini**: Verify key at [Google AI Studio](https://aistudio.google.com/)
- **Onyx Cloud**: Check key validity in Onyx admin console
- **Rate Limits**: Gemini free tier: 15 RPM, 1M tokens/day

### System Health Diagnostics

#### **Check All Systems**
```bash
# CLI health command (when connected)
/health

# Direct API health check
curl http://localhost:8058/health
```

#### **Component-Specific Issues**

**Onyx Cloud Unavailable:**
- System automatically falls back to Graphiti-only mode
- Agent will use `vector_search` + `graph_search` tools
- Check Onyx API key and network connectivity

**Vector Search Fails:**
- Verify PostgreSQL connection and pgvector extension
- Check embedding model configuration
- Ensure documents have been ingested

**Knowledge Graph Issues:**
- Verify Neo4j service is running
- Check database credentials in `.env`
- Confirm knowledge graph was built during ingestion

**No Results from Agent:**
- Ensure document ingestion completed successfully
- Check if documents exist in `documents/` folder
- Verify both databases contain data

### Performance Optimization

#### **For Large Document Sets**
```bash
# Use faster ingestion (no knowledge graph)
python -m ingestion.ingest --no-semantic --verbose

# Or optimize chunk size
python -m ingestion.ingest --chunk-size 1000
```

#### **For Limited API Quotas**
- **Gemini Free Tier**: 15 requests/minute, 1M tokens/day
- **Rate Limiting**: Agent automatically handles rate limits
- **Cost Control**: Use smaller chunk sizes and limit document scope

### Logs and Debugging

#### **Main Log Files**
- **API Server**: `comprehensive_agent_api.log`
- **Console Output**: Real-time in terminal
- **Component Logs**: Individual module logging

#### **Enable Debug Logging**
```env
# Add to .env for detailed debugging
LOG_LEVEL=DEBUG
APP_ENV=development
```

#### **Common Error Patterns**

**"Tools used: 4" with Onyx failures:**
- Normal behavior: Agent tries multiple Onyx tools, falls back to Graphiti
- System working correctly with resilient fallback

**"No answer on attempt 1/2/3":**
- Onyx service may be slow or unavailable
- Agent will automatically fallback to other tools

**"Unexpected error in answer with quote":**
- Onyx API response format issue
- Agent falls back to alternative search methods

## 🎯 Best Practices

### Document Preparation
- **Format**: Use markdown (.md) or plain text (.txt) files
- **Structure**: Clear headings and sections improve extraction
- **Size**: Aim for 1-10 MB per document for optimal processing
- **Quality**: Well-structured documents produce better knowledge graphs

### Query Optimization
- **Specific Questions**: "What are the authentication requirements?" vs "Tell me about auth"
- **Entity Names**: Use proper names of people, systems, or concepts
- **Temporal Queries**: Include time references for timeline analysis
- **Comprehensive Research**: Ask for "complete analysis" to trigger multi-system search

### System Monitoring
- **Regular Health Checks**: Use `/health` command to monitor all systems
- **Performance Tracking**: Monitor response times and tool usage patterns
- **Resource Management**: Watch API quota usage and database storage

---

## 🏆 Built With Excellence

**🤖 Core Technologies:**
- **Pydantic AI** - Advanced agent framework with tool orchestration
- **FastAPI** - High-performance async web framework
- **Google Gemini** - Cost-effective, high-quality LLM and embeddings
- **Onyx Cloud** - Enterprise-grade document search and retrieval

**🗄️ Data Layer:**
- **PostgreSQL + pgvector** - High-performance vector similarity search
- **Neo4j + Graphiti** - Temporal knowledge graph with relationship discovery

**🎨 User Experience:**
- **Rich Terminal UI** - Beautiful CLI with real-time progress indicators
- **Streaming Responses** - Live response generation for immediate feedback
- **Intelligent Fallbacks** - Graceful degradation ensuring system availability

**💼 Enterprise Ready:**
- **Production Logging** - Comprehensive monitoring and debugging
- **Error Resilience** - Robust error handling and recovery mechanisms
- **Scalable Architecture** - Designed for growth and high availability

---

*Building the future of intelligent document analysis with hybrid RAG technology.* 🚀
