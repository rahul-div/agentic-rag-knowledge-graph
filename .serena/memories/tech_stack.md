# Technology Stack

## Core Technologies
- **Python 3.11+**: Primary language
- **Pydantic AI**: Agent framework for building conversational AI agents
- **FastAPI**: API framework for streaming endpoints
- **PostgreSQL + pgvector**: Vector database for semantic search
- **Neo4j + Graphiti**: Knowledge graph for temporal relationships
- **Google Gemini**: Currently optimized for Gemini API (cost-effective with generous free tier)

## Key Libraries
- **asyncpg**: PostgreSQL async driver
- **httpx**: Async HTTP client
- **python-dotenv**: Environment management
- **pytest + pytest-asyncio**: Testing framework
- **rich**: CLI formatting and colors
- **aiohttp**: Async HTTP for CLI client
- **graphiti-core**: Knowledge graph operations
- **google-genai**: Google Gemini integration

## Database Schema
- **documents**: Store document metadata (UUID, title, source, content, metadata, timestamps)
- **chunks**: Store document chunks with embeddings (vector(768) for Gemini embeddings)
- **sessions**: Manage conversation sessions
- **messages**: Store conversation history

## Flexible Provider Support
The system supports multiple LLM providers through environment configuration:
- OpenAI
- Ollama (local)
- OpenRouter
- Google Gemini (currently optimized)

## Development Tools
- **pytest**: Available for testing (58 tests passing)
- **black**: Code formatting (not currently installed)
- **ruff**: Code linting (not currently installed)
- **Virtual environment**: Uses venv for dependency isolation