# Multi-Client Project Intelligence System

**🚀 Now optimized for Google Gemini API!** This hybrid RAG system has been migrated from OpenAI to use Google Gemini for all LLM and embedding tasks, providing cost-effective and high-quality AI capabilities.

**Multi-Client Project Intelligence Platform** that combines traditional RAG (vector search) with temporal knowledge graph capabilities to provide deep insights and relationship analysis for client projects. This system serves as a secondary research tool, enabling teams to quickly understand complex project contexts, stakeholder relationships, and historical decisions across multiple concurrent client engagements.

## 🎯 **Primary Use Case: Client Project Intelligence**

This system is designed for **consulting/services companies** managing multiple client projects simultaneously:

- **Project-Specific Knowledge Isolation:** Each client project has its dedicated hybrid RAG instance
- **Team Collaboration:** Multiple team members access project-specific insights with role-based permissions  
- **Rapid Context Acquisition:** New team members get up to speed 70% faster through intelligent querying
- **Deep Relationship Discovery:** Uncover hidden connections between stakeholders, requirements, and decisions
- **Historical Intelligence:** Preserve and leverage institutional knowledge across project lifecycles

### **Target Users:**
- **Project Managers** - Understanding dependencies, risks, and stakeholder concerns
- **Business Analysts** - Identifying patterns and insights from complex project documentation  
- **Consultants** - Quick context acquisition for client engagements
- **New Team Members** - Rapid onboarding with comprehensive project understanding
- **Technical Teams** - Understanding system architectures and technical decision rationale

## 🔧 Quick Setup (Gemini Edition)

1. **Get your Gemini API key**: Visit [Google AI Studio](https://aistudio.google.com/) and create an API key
2. **Run the setup script**: `python3 setup_api_keys.py` (interactive setup)
3. **Or manually edit `.env`**: Replace placeholder values with your real API key
4. **Start ingestion**: `python3 ingestion/ingest.py`
5. **Check status**: `python3 quick_start.py`

## 🎯 Gemini Integration Features

- **Cost-effective**: Gemini offers generous free tier (15 RPM, 1M tokens/day)
- **High-quality embeddings**: Using `embedding-001` model (768 dimensions)
- **Optimized chunking**: Chunk sizes optimized for Gemini's context window
- **Enhanced entity extraction**: Includes Gemini-specific terms and patterns
- **Comprehensive error handling**: Detailed logging and validation

Built with:

- **Google Gemini** for LLM and Embeddings (NEW!)
- Pydantic AI for the AI Agent Framework
- Graphiti for the Knowledge Graph
- Postgres with PGVector for the Vector Database
- Neo4j for the Knowledge Graph Engine (Graphiti connects to this)
- FastAPI for the Agent API
- Claude Code for the AI Coding Assistant (See `CLAUDE.md`, `PLANNING.md`, and `TASK.md`)

## Overview

This system includes three main components:

1. **Document Ingestion Pipeline**: Processes markdown documents using semantic chunking and builds both vector embeddings and knowledge graph relationships
2. **AI Agent Interface**: A conversational agent powered by Pydantic AI that can search across both vector database and knowledge graph
3. **Streaming API**: FastAPI backend with real-time streaming responses and comprehensive search capabilities

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database (such as Neon)
- Neo4j database (for knowledge graph)
- LLM Provider API key (OpenAI, Ollama, Gemini, etc.)

## Installation

### 1. Set up a virtual environment

```bash
# Create and activate virtual environment
python -m venv venv       # python3 on Linux
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate     # On Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up required tables in Postgres

Execute the SQL in `sql/schema.sql` to create all necessary tables, indexes, and functions.

Be sure to change the embedding dimensions on lines 31, 67, and 100 based on your embedding model. OpenAI's text-embedding-3-small is 1536 and nomic-embed-text from Ollama is 768 dimensions, for reference.

Note that this script will drop all tables before creating/recreating!

### 4. Set up Neo4j

You have a couple easy options for setting up Neo4j:

#### Option A: Using Local-AI-Packaged (Simplified setup - Recommended)
1. Clone the repository: `git clone https://github.com/coleam00/local-ai-packaged`
2. Follow the installation instructions to set up Neo4j through the package
3. Note the username and password you set in .env and the URI will be bolt://localhost:7687

#### Option B: Using Neo4j Desktop
1. Download and install [Neo4j Desktop](https://neo4j.com/download/)
2. Create a new project and add a local DBMS
3. Start the DBMS and set a password
4. Note the connection details (URI, username, password)

### 5. Configure environment variables

Create a `.env` file in the project root:

```bash
# Database Configuration (example Neon connection string)
DATABASE_URL=postgresql://username:password@ep-example-12345.us-east-2.aws.neon.tech/neondb

# Neo4j Configuration  
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# LLM Provider Configuration (choose one)
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key
LLM_CHOICE=gpt-4.1-mini

# Embedding Configuration
EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-your-api-key
EMBEDDING_MODEL=text-embedding-3-small

# Ingestion Configuration
INGESTION_LLM_CHOICE=gpt-4.1-nano  # Faster model for processing

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
APP_PORT=8058
```

For other LLM providers:
```bash
# Ollama (Local)
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_CHOICE=qwen2.5:14b-instruct

# OpenRouter
LLM_PROVIDER=openrouter
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=your-openrouter-key
LLM_CHOICE=anthropic/claude-3-5-sonnet

# Gemini
LLM_PROVIDER=gemini
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta
LLM_API_KEY=your-gemini-key
LLM_CHOICE=gemini-2.5-flash
```

## Quick Start

### 1. Prepare Your Project Documents

Add your client project documents to the `documents/` folder:

```bash
mkdir -p documents
# Add your project documentation files
# Example: documents/project_requirements.md
#          documents/stakeholder_analysis.md
#          documents/technical_decisions.md
#          documents/meeting_notes.md
```

**Typical Project Documents Include:**
- Requirements documents and specifications
- Stakeholder analysis and communication logs  
- Meeting notes and decision records
- Technical architecture documents
- Status reports and project updates
- Risk assessments and mitigation plans
- Change requests and scope modifications

**Note**: The system will extract entities like projects, stakeholders, requirements, and decisions, then build relationships between them for intelligent querying.

### 2. Run Document Ingestion

**Important**: You must run ingestion first to populate the databases before the agent can provide meaningful responses.

```bash
# Basic ingestion with semantic chunking
python -m ingestion.ingest

# Clean existing data and re-ingest everything
python -m ingestion.ingest --clean

# Custom settings for faster processing (no knowledge graph)
python -m ingestion.ingest --chunk-size 800 --no-semantic --verbose
```

The ingestion process will:
- Parse and semantically chunk your project documents
- Generate embeddings for vector search
- Extract project entities (stakeholders, requirements, decisions, deliverables)
- Build relationship graphs between project components
- Store everything in PostgreSQL and Neo4j

NOTE that this can take a while because knowledge graphs are very computationally expensive!

### 3. Configure Agent Behavior (Optional)

Before running the API server, you can customize when the agent uses different tools by modifying the system prompt in `agent/prompts.py`. The system prompt controls:
- When to use vector search vs knowledge graph search
- How to combine results from different sources
- The agent's reasoning strategy for tool selection

### 4. Start the API Server (Terminal 1)

```bash
# Start the FastAPI server
python -m agent.api

# Server will be available at http://localhost:8058
```

### 5. Use the Command Line Interface (Terminal 2)

The CLI provides an interactive way to chat with the agent and see which tools it uses for each query.

```bash
# Start the CLI in a separate terminal from the API (connects to default API at http://localhost:8058)
python cli.py

# Connect to a different URL
python cli.py --url http://localhost:8058

# Connect to a specific port
python cli.py --port 8080
```

#### CLI Features

- **Real-time streaming responses** - See the agent's response as it's generated
- **Tool usage visibility** - Understand which tools the agent used:
  - `vector_search` - Semantic similarity search
  - `graph_search` - Knowledge graph queries
  - `hybrid_search` - Combined search approach
- **Session management** - Maintains conversation context
- **Color-coded output** - Easy to read responses and tool information

#### Example CLI Session

```
🤖 Agentic RAG with Knowledge Graph CLI
============================================================
Connected to: http://localhost:8058

You: What are the key dependencies for the Q2 delivery milestone?

🤖 Assistant:
Based on the project documentation, the Q2 delivery milestone has several critical dependencies...

🛠 Tools Used:
  1. vector_search (query='Q2 delivery dependencies', limit=10)
  2. graph_search (query='milestone dependencies requirements')

────────────────────────────────────────────────────────────

You: Which stakeholders have raised concerns about the authentication module?

🤖 Assistant:
Several stakeholders have expressed concerns about the authentication module...

🛠 Tools Used:
  1. hybrid_search (query='authentication stakeholder concerns', limit=10)
  2. get_entity_relationships (entity='Authentication Module')
```

#### CLI Commands

- `help` - Show available commands
- `health` - Check API connection status
- `clear` - Clear current session
- `exit` or `quit` - Exit the CLI

### 6. Test the System

#### Health Check
```bash
curl http://localhost:8058/health
```

#### Chat with the Agent (Non-streaming)
```bash
curl -X POST "http://localhost:8058/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main risks identified for this project?"
  }'
```

#### Streaming Chat
```bash
curl -X POST "http://localhost:8058/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me the timeline of major technical decisions made",
  }'
```

## How It Works

### The Power of Hybrid RAG + Knowledge Graph for Project Intelligence

This system combines the best of both worlds for comprehensive project understanding:

**Vector Database (PostgreSQL + pgvector)**:
- Semantic similarity search across project document chunks
- Fast retrieval of contextually relevant project information
- Excellent for finding similar requirements, decisions, or issues

**Knowledge Graph (Neo4j + Graphiti)**:
- Temporal relationships between project entities (stakeholders, requirements, decisions)
- Graph traversal for discovering hidden project dependencies
- Perfect for understanding stakeholder influence, requirement evolution, and decision impacts

**Intelligent Agent**:
- Automatically chooses the best search strategy for project queries
- Combines results from both databases for comprehensive answers
- Provides context-aware responses with source citations from project documents

### Example Project Queries

The system excels at project queries that benefit from both semantic search and relationship understanding:

**Stakeholder Analysis**: "Which stakeholders have decision-making authority on the payment module?" 
  - Uses vector search to find relevant stakeholder documents and graph search to understand influence relationships

**Requirement Dependencies**: "What requirements are blocking the user authentication feature?"
  - Uses knowledge graph to traverse requirement dependencies and find blocking relationships

**Decision History**: "Show me the timeline of technical architecture decisions"
  - Leverages Graphiti's temporal capabilities to track decision evolution over time

**Risk Assessment**: "What are the interconnected risks for the Q3 delivery milestone?"
  - Combines vector search for risk documentation with graph traversal for dependency analysis

### Why This Architecture Works So Well for Project Management

1. **Complementary Strengths**: Vector search finds semantically similar project content while knowledge graphs reveal hidden project dependencies

2. **Temporal Intelligence**: Graphiti tracks how project decisions and requirements evolve over time, perfect for understanding project history

3. **Multi-Client Architecture**: Each client project operates in isolation while sharing the same powerful intelligence framework

4. **Team Collaboration**: Multiple team members can query the same project knowledge base with role-appropriate access

## API Documentation

Visit http://localhost:8058/docs for interactive API documentation once the server is running.

## Key Features

- **Hybrid Search**: Seamlessly combines vector similarity and graph traversal
- **Temporal Knowledge**: Tracks how information changes over time
- **Streaming Responses**: Real-time AI responses with Server-Sent Events
- **Flexible Providers**: Support for multiple LLM and embedding providers
- **Semantic Chunking**: Intelligent document splitting using LLM analysis
- **Production Ready**: Comprehensive testing, logging, and error handling

## Project Structure

```
agentic-rag-knowledge-graph/
├── agent/                  # AI agent and API
│   ├── agent.py           # Main Pydantic AI agent
│   ├── api.py             # FastAPI application
│   ├── providers.py       # LLM provider abstraction
│   └── models.py          # Data models
├── ingestion/             # Document processing
│   ├── ingest.py         # Main ingestion pipeline
│   ├── chunker.py        # Semantic chunking
│   └── embedder.py       # Embedding generation
├── sql/                   # Database schema
├── documents/             # Your markdown files
└── tests/                # Comprehensive test suite
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agent --cov=ingestion --cov-report=html

# Run specific test categories
pytest tests/agent/
pytest tests/ingestion/
```

## Troubleshooting

### Common Issues

**Database Connection**: Ensure your DATABASE_URL is correct and the database is accessible
```bash
# Test your connection
psql -d "$DATABASE_URL" -c "SELECT 1;"
```

**Neo4j Connection**: Verify your Neo4j instance is running and credentials are correct
```bash
# Check if Neo4j is accessible (adjust URL as needed)
curl -u neo4j:password http://localhost:7474/db/data/
```

**No Results from Agent**: Make sure you've run the ingestion pipeline first
```bash
python -m ingestion.ingest --verbose
```

**LLM API Issues**: Check your API key and provider configuration in `.env`

---

Built with ❤️ using Pydantic AI, FastAPI, PostgreSQL, and Neo4j.