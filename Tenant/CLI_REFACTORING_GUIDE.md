# Multi-Tenant CLI Refactoring: Direct Service Calls vs HTTP API Endpoints

## Overview

This document explains the refactoring of the interactive multi-tenant CLI from using direct service calls to HTTP API endpoints with JWT authentication.

## Architecture Comparison

### Before: Direct Service Calls (`interactive_multi_tenant_cli.py`)

```python
# Direct imports and initialization
from tenant_manager import TenantManager
from auth_middleware import TenantContext, JWTAuthenticator
from multi_tenant_agent import MultiTenantRAGAgent

class MultiTenantCLI:
    def __init__(self):
        self.tenant_manager = TenantManager(...)
        self.jwt_authenticator = JWTAuthenticator()
        self.agent = MultiTenantRAGAgent(...)

    async def search(self):
        # Direct method calls
        results = await self.tenant_manager.ingestion_service.vector_search_for_tenant(...)
        graph_results = await self.tenant_manager.graphiti_client.search_tenant_graph(...)
```

**Characteristics:**
- Direct in-process method calls
- Shared memory and resources
- Tight coupling between CLI and services
- No network overhead
- Requires all dependencies to be installed locally

### After: HTTP API Endpoints (`interactive_multi_tenant_cli_http.py`)

```python
# HTTP client approach
import httpx

class HTTPMultiTenantCLI:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.jwt_token = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search(self):
        # HTTP API calls
        response = await self.client.post(f"{self.api_base_url}/search", json=search_data)
        results = response.json()
```

**Characteristics:**
- HTTP-based communication
- Standard REST API pattern
- JWT authentication for security
- Loose coupling between CLI and services
- Network-based, supports remote API servers
- Standard web architecture

## Key Differences

| Aspect | Direct Service Calls | HTTP API Endpoints |
|--------|---------------------|-------------------|
| **Communication** | In-process method calls | HTTP requests/responses |
| **Authentication** | Direct object creation | JWT tokens |
| **Coupling** | Tight (direct imports) | Loose (HTTP interface) |
| **Deployment** | Single process | Separate client/server |
| **Scalability** | Limited to single machine | Distributed architecture |
| **Security** | Process-level | HTTP + JWT tokens |
| **Error Handling** | Direct exceptions | HTTP status codes |
| **Logging** | Shared logging context | Separate client/server logs |

## Refactoring Changes

### 1. Authentication Flow

**Before (Direct):**
```python
async def authenticate(self):
    # Direct context creation
    self.current_tenant = TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        permissions=["read", "write"],
        session_id=str(uuid.uuid4()),
    )
```

**After (HTTP):**
```python
async def authenticate(self):
    # API authentication
    auth_data = {"tenant_id": tenant_id, "api_key": api_key, "user_id": user_id}
    response = await self.client.post(f"{self.api_base_url}/auth/login", json=auth_data)
    
    if response.status_code == 200:
        auth_result = response.json()
        self.jwt_token = auth_result["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self.jwt_token}"})
```

### 2. Search Operations

**Before (Direct):**
```python
async def _perform_search(self, search_type: str, query: str, limit: int, text_weight: float):
    tenant_id = self.current_tenant.tenant_id
    
    if search_type == "vector":
        tenant_db_url = await self.tenant_manager.get_tenant_database_url(tenant_id)
        return await self.tenant_manager.ingestion_service.vector_search_for_tenant(
            tenant_database_url=tenant_db_url, query=query, limit=limit
        )
```

**After (HTTP):**
```python
async def _perform_search_api(self, search_type: str, query: str, limit: int, text_weight: float):
    search_data = {
        "query": query,
        "search_type": search_type,
        "limit": limit,
        "text_weight": text_weight
    }
    
    response = await self.client.post(f"{self.api_base_url}/search", json=search_data)
    return response.json()
```

### 3. Chat Mode

**Before (Direct):**
```python
async def chat_mode(self):
    agent_result = await self.agent.chat(
        message=message,
        context=TenantContext(
            tenant_id=self.current_tenant.tenant_id,
            user_id=self.current_tenant.user_id,
            session_id=session_id,
        ),
    )
```

**After (HTTP):**
```python
async def chat_mode(self):
    chat_data = {"message": message, "session_id": session_id}
    response = await self.client.post(f"{self.api_base_url}/chat", json=chat_data)
    chat_result = response.json()
```

## API Endpoints Used

The HTTP-based CLI interacts with these API endpoints:

1. **`POST /auth/login`** - User authentication and JWT token generation
2. **`GET /tenants/info`** - Retrieve current tenant information
3. **`POST /search`** - Perform search operations (vector, graph, hybrid, comprehensive)
4. **`POST /chat`** - Interactive chat with the RAG agent
5. **`GET /health`** - API server health check

## Sample Workflow

### 1. Start the API Server

```bash
cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph/Tenant
./start_interactive_api.sh
```

Expected output:
```
2024-01-20 10:30:00 - INFO - Starting Multi-Tenant RAG API...
2024-01-20 10:30:01 - INFO - Tenant manager initialized
2024-01-20 10:30:01 - INFO - JWT authenticator initialized
2024-01-20 10:30:01 - INFO - 🎯 Multi-Tenant RAG API ready
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
```

### 2. Start the HTTP-based CLI

```bash
cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph/Tenant
./start_http_cli.sh
```

Expected output:
```
🚀 Starting HTTP-based Multi-Tenant CLI...
📡 Connecting to API server at: http://localhost:8000

🚀 Multi-Tenant RAG CLI (HTTP API)
Interactive command-line interface using HTTP API endpoints
Supports JWT authentication, vector search, graph search, hybrid search, and chat mode
API Server: http://localhost:8000

🔍 Checking API server health...
✅ API Server: healthy (v1.0.0)
   📊 Active tenants: 2

🏠 Multi-Tenant RAG CLI (HTTP) - Not authenticated

Select an option:
  1. 🔐 Authenticate
  2. ℹ️  Show tenant info
  3. 🔍 Search
  4. 💬 Chat mode
  5. 📋 Tenant info
  6. 🏥 API Health Check
  7. 🚪 Exit
```

### 3. Authentication Workflow

**CLI Input:**
```
Enter choice: 1

🔐 Authentication Required
Enter tenant ID: tenant-001
Enter API key: [hidden] api_key_tenant-001
Enter user ID (optional) [cli_user]: john_doe
```

**HTTP Request:**
```http
POST http://localhost:8000/auth/login
Content-Type: application/json

{
  "tenant_id": "tenant-001",
  "api_key": "api_key_tenant-001",
  "user_id": "john_doe"
}
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2024-01-20T18:30:00"
}
```

**CLI Output:**
```
✅ Successfully authenticated as john_doe for tenant tenant-001
Token expires: 2024-01-20T18:30:00
```

### 4. Search Workflow

**CLI Input:**
```
Enter choice: 3

🔍 Search Options
  1. Vector Search - Semantic similarity
  2. Graph Search - Facts and relationships
  3. Hybrid Search - Combined vector and graph
  4. Comprehensive Search - All methods

Select search type: 4
Enter your search query: machine learning applications
Enter result limit [10]: 5
```

**HTTP Request:**
```http
POST http://localhost:8000/search
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "query": "machine learning applications",
  "search_type": "comprehensive",
  "limit": 5,
  "text_weight": 0.3
}
```

**Expected Response:**
```json
{
  "results": [
    {
      "content": "Machine learning is transforming healthcare through...",
      "score": 0.85,
      "source": "healthcare_ml_doc.pdf",
      "metadata": {"document_title": "ML in Healthcare", "page": 3}
    }
  ],
  "total_results": 5,
  "search_type": "comprehensive",
  "query": "machine learning applications",
  "tenant_id": "tenant-001",
  "execution_time": 0.45
}
```

### 5. Chat Workflow

**CLI Input:**
```
Enter choice: 4

💬 Chat Mode - Type 'exit' to quit
Ask questions about your documents and knowledge base.

🧑 You: What are the main applications of machine learning in healthcare?
```

**HTTP Request:**
```http
POST http://localhost:8000/chat
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "message": "What are the main applications of machine learning in healthcare?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Expected Response:**
```json
{
  "response": "Based on your documents, machine learning has several key applications in healthcare: 1) Medical imaging and diagnostics...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "tenant-001",
  "sources": [
    {"source": "healthcare_ml_doc.pdf", "relevance": 0.92},
    {"source": "medical_ai_research.pdf", "relevance": 0.87}
  ],
  "execution_time": 1.23
}
```

**CLI Output:**
```
🤖 Assistant: Based on your documents, machine learning has several key applications in healthcare: 1) Medical imaging and diagnostics...

   ⏱️ API: 1.23s, Total: 1.35s
   📚 Found 2 relevant sources
      1. healthcare_ml_doc.pdf
      2. medical_ai_research.pdf
```

## Benefits of HTTP API Approach

### 1. **Standard Architecture**
- Follows REST API conventions
- Compatible with any HTTP client
- Enables web dashboard development
- API documentation with OpenAPI/Swagger

### 2. **Better Security**
- JWT tokens with expiration
- Stateless authentication
- Standard HTTP security practices
- Token-based session management

### 3. **Scalability**
- API server can be deployed separately
- Multiple CLI clients can connect
- Load balancing possible
- Microservices architecture ready

### 4. **Development Benefits**
- Clear separation of concerns
- Independent CLI and API development
- API testing with tools like Postman
- Standard HTTP debugging tools

### 5. **Deployment Flexibility**
- CLI can connect to remote APIs
- API server can be containerized
- Cloud deployment ready
- Multiple client types (CLI, web, mobile)

## Running Both Versions

### Original Direct Service CLI
```bash
cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph/Tenant
python3 interactive_multi_tenant_cli.py
```

### New HTTP API CLI
```bash
cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph/Tenant
./start_http_cli.sh

# Or with custom API URL
python3 interactive_multi_tenant_cli_http.py --api-url http://localhost:8000

# Or with pre-authentication
python3 interactive_multi_tenant_cli_http.py --tenant-id tenant-001 --api-key api_key_tenant-001
```

## Conclusion

The refactoring from direct service calls to HTTP API endpoints represents a significant architectural improvement:

1. **Maintains Full Functionality**: All original CLI features are preserved
2. **Improves Architecture**: Standard client-server separation
3. **Enhances Security**: JWT-based authentication
4. **Enables Scalability**: Distributed deployment options
5. **Follows Best Practices**: REST API conventions

The HTTP-based CLI provides the same user experience while offering a more robust, secure, and scalable foundation for multi-tenant RAG operations.
