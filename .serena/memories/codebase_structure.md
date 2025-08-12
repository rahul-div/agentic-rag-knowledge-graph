# Codebase Structure and Organization

## Directory Layout
```
agentic-rag-knowledge-graph/
├── agent/                  # AI agent and API layer
│   ├── agent.py           # Main Pydantic AI agent with tools
│   ├── api.py             # FastAPI application with streaming
│   ├── providers.py       # LLM provider abstraction
│   ├── models.py          # Pydantic data models
│   ├── db_utils.py        # PostgreSQL utilities
│   ├── graph_utils.py     # Neo4j/Graphiti utilities
│   ├── tools.py           # Agent tool implementations
│   └── prompts.py         # System prompts
├── ingestion/             # Document processing pipeline
│   ├── ingest.py         # Main ingestion script
│   ├── chunker.py        # Semantic chunking
│   ├── embedder.py       # Embedding generation
│   ├── graph_builder.py  # Knowledge graph construction
│   └── cleaner.py        # Database cleanup utilities
├── sql/                   # Database schema
│   └── schema.sql        # PostgreSQL schema with pgvector
├── tests/                # Comprehensive test suite
│   ├── conftest.py       # Test fixtures and configuration
│   ├── agent/           # Agent-related tests
│   └── ingestion/       # Ingestion pipeline tests
├── documents/           # Markdown files for processing (gitignored)
├── cli.py               # Interactive command-line interface
├── quick_start.py       # Setup status and quick start guide
├── PLANNING.md          # Detailed architecture documentation
├── TASK.md              # Task tracking and project status
├── CLAUDE.md            # Development guidelines
└── README.md            # User documentation
```

## Key File Purposes

### Agent System
- **agent.py**: Main Pydantic AI agent with tool decorators and AgentDependencies dataclass
- **api.py**: FastAPI app with streaming SSE endpoints and CORS configuration
- **tools.py**: Vector search, graph search, hybrid search, and entity relationship tools
- **models.py**: Pydantic models for ChunkResult, DocumentResult, ToolCall tracking

### Ingestion Pipeline  
- **ingest.py**: DocumentIngestionPipeline class with Gemini integration validation
- **chunker.py**: Semantic chunking algorithms optimized for different models
- **embedder.py**: Embedding generation with batch processing and caching
- **graph_builder.py**: Entity extraction and relationship building for Graphiti

### Configuration Files
- **requirements.txt**: Gemini-optimized dependencies with graphiti-core[google-genai]
- **.env**: Environment variables (gitignored, needs manual setup)
- **sql/schema.sql**: PostgreSQL schema with vector(768) for Gemini embeddings

## Architecture Patterns
- **Separation of Concerns**: Clear boundaries between agent, ingestion, and API layers
- **Async Architecture**: AsyncPG for database, aiohttp for HTTP, async/await throughout
- **Dependency Injection**: AgentDependencies dataclass for clean parameter passing
- **Tool-based Agent**: Pydantic AI agent with decorated tool functions
- **Streaming Interface**: SSE for real-time responses with tool usage tracking