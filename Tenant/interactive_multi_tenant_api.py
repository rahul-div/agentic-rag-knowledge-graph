"""
Interactive Multi-Tenant FastAPI for Hybrid RAG System
Provides authenticated endpoints for multi-tenant RAG with comprehensive agent integration.
"""

import logging
import os
import sys
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Add parent directory to path for agent imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi import FastAPI, HTTPException, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    from jose import JWTError
    import uvicorn
except ImportError:
    print(
        "Warning: FastAPI dependencies not installed. Install with: pip install fastapi uvicorn[standard] python-jose[cryptography]"
    )
    sys.exit(1)

from tenant_manager import TenantManager
from auth_middleware import TenantContext, JWTAuthenticator
from multi_tenant_agent import MultiTenantRAGAgent

# Import validated agent from parent directory
try:
    from agent.tools import (
        vector_search_tool,
        graph_search_tool,
        hybrid_search_tool,
        comprehensive_search_tool,
        VectorSearchInput,
        GraphSearchInput,
        HybridSearchInput,
        ComprehensiveSearchInput,
    )
except ImportError as e:
    print(f"Error importing agent modules: {e}")
    print("Please ensure the agent folder is properly configured")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("interactive_multi_tenant_api.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Global state
tenant_manager = None
jwt_authenticator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global tenant_manager, jwt_authenticator

    logger.info("Starting Multi-Tenant RAG API...")

    try:
        # Initialize tenant manager with required parameters
        neon_api_key = os.getenv("NEON_API_KEY")
        catalog_db_url = os.getenv("CATALOG_DB_URL") or os.getenv("POSTGRES_URL")

        if not neon_api_key:
            logger.warning("NEON_API_KEY not found in environment variables")
        if not catalog_db_url:
            logger.warning(
                "CATALOG_DB_URL or POSTGRES_URL not found in environment variables"
            )

        # Initialize with environment variables or fallback values for testing
        tenant_manager = TenantManager(
            neon_api_key=neon_api_key or "test_neon_api_key",
            catalog_db_url=catalog_db_url or "postgresql://localhost:5432/test_catalog",
            default_region="aws-us-east-1",
            neo4j_uri=os.getenv("NEO4J_URI"),
            neo4j_user=os.getenv("NEO4J_USERNAME"),
            neo4j_password=os.getenv("NEO4J_PASSWORD"),
        )
        logger.info("Tenant manager initialized")

        # Initialize JWT authenticator
        jwt_authenticator = JWTAuthenticator()
        logger.info("JWT authenticator initialized")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise
    finally:
        logger.info("Shutting down Multi-Tenant RAG API...")


# Initialize FastAPI app
app = FastAPI(
    title="Interactive Multi-Tenant RAG API",
    description="Authenticated FastAPI for multi-tenant hybrid RAG with knowledge graphs",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class AuthRequest(BaseModel):
    """Authentication request model."""

    tenant_id: str
    user_id: Optional[str] = None
    api_key: Optional[str] = None


class AuthResponse(BaseModel):
    """Authentication response model."""

    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    expires_in: int


class SearchRequest(BaseModel):
    """Search request model."""

    query: str
    search_type: str = Field(
        default="comprehensive",
        description="Type of search: vector, graph, hybrid, comprehensive",
    )
    limit: int = Field(default=10, ge=1, le=50)
    text_weight: Optional[float] = Field(default=0.3, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    """Search result model."""

    content: str
    score: Optional[float] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Search response model."""

    results: List[SearchResult]
    total_results: int
    search_type: str
    query: str
    tenant_id: str
    execution_time: float


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    session_id: Optional[str] = None
    search_preferences: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    session_id: str
    tenant_id: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time: float


class TenantInfo(BaseModel):
    """Tenant information model."""

    tenant_id: str
    status: str
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    version: str
    tenant_count: int


# Dependency to get current tenant context
async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TenantContext:
    """Extract tenant context from JWT token."""
    try:
        # Decode JWT token
        payload = jwt_authenticator.decode_token(credentials.credentials)

        # Extract tenant context
        tenant_context = TenantContext(
            tenant_id=payload.get("tenant_id"),
            user_id=payload.get("user_id"),
            permissions=payload.get("permissions", ["read"]),
            metadata=payload.get("metadata", {}),
            session_id=payload.get("session_id"),
        )

        # Validate tenant exists
        if not await tenant_manager.tenant_exists(tenant_context.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_context.tenant_id} not found",
            )

        return tenant_context

    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


# API Endpoints


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Count active tenants
        tenant_count = len(await tenant_manager.list_tenants()) if tenant_manager else 0

        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            tenant_count=tenant_count,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service unhealthy",
        )


@app.post("/auth/login", response_model=AuthResponse)
async def login(auth_request: AuthRequest):
    """Authenticate and get access token."""
    try:
        # Validate tenant exists
        if not await tenant_manager.tenant_exists(auth_request.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {auth_request.tenant_id} not found",
            )

        # For demonstration, we'll use simple API key validation
        # In production, this would integrate with your auth provider
        expected_api_key = f"api_key_{auth_request.tenant_id}"
        if auth_request.api_key != expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
            )

        # Generate JWT token
        token_data = {
            "tenant_id": auth_request.tenant_id,
            "user_id": auth_request.user_id or "anonymous",
            "permissions": ["read", "write"],  # Default permissions
            "session_id": str(uuid.uuid4()),
            "exp": datetime.utcnow() + timedelta(hours=24),
        }

        access_token = jwt_authenticator.create_token(token_data)

        return AuthResponse(
            access_token=access_token,
            tenant_id=auth_request.tenant_id,
            expires_in=24 * 3600,  # 24 hours
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


@app.get("/tenants/info", response_model=TenantInfo)
async def get_tenant_info(tenant_context: TenantContext = Depends(get_current_tenant)):
    """Get current tenant information."""
    try:
        tenant_data = await tenant_manager.get_tenant(tenant_context.tenant_id)

        return TenantInfo(
            tenant_id=tenant_data["tenant_id"],
            status=tenant_data.get("status", "active"),
            created_at=tenant_data.get("created_at", datetime.utcnow()),
            metadata=tenant_data.get("metadata", {}),
        )

    except Exception as e:
        logger.error(f"Error getting tenant info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenant information",
        )


@app.post("/search", response_model=SearchResponse)
async def search(
    search_request: SearchRequest,
    tenant_context: TenantContext = Depends(get_current_tenant),
):
    """Perform multi-modal search based on type."""
    start_time = datetime.utcnow()

    try:
        results = []

        if search_request.search_type == "vector":
            # Vector search
            input_data = VectorSearchInput(
                query=search_request.query, limit=search_request.limit
            )
            vector_results = await vector_search_tool(input_data)

            results = [
                SearchResult(
                    content=r.content,
                    score=r.score,
                    source=r.document_source,
                    metadata={
                        "document_title": r.document_title,
                        "chunk_id": r.chunk_id,
                    },
                )
                for r in vector_results
            ]

        elif search_request.search_type == "graph":
            # Graph search
            input_data = GraphSearchInput(query=search_request.query)
            graph_results = await graph_search_tool(input_data)

            results = [
                SearchResult(
                    content=r.fact,
                    source="knowledge_graph",
                    metadata={
                        "uuid": r.uuid,
                        "valid_at": r.valid_at,
                        "invalid_at": r.invalid_at,
                        "source_node_uuid": r.source_node_uuid,
                    },
                )
                for r in graph_results
            ]

        elif search_request.search_type == "hybrid":
            # Hybrid search
            input_data = HybridSearchInput(
                query=search_request.query,
                limit=search_request.limit,
                text_weight=search_request.text_weight,
            )
            hybrid_results = await hybrid_search_tool(input_data)

            results = [
                SearchResult(
                    content=r.content,
                    score=r.score,
                    source=r.source,
                    metadata=r.metadata,
                )
                for r in hybrid_results
            ]

        elif search_request.search_type == "comprehensive":
            # Comprehensive search using all methods
            input_data = ComprehensiveSearchInput(
                query=search_request.query, limit=search_request.limit
            )
            comp_results = await comprehensive_search_tool(input_data)

            results = [
                SearchResult(
                    content=r.content,
                    score=r.score,
                    source=r.source,
                    metadata=r.metadata,
                )
                for r in comp_results
            ]

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid search type: {search_request.search_type}",
            )

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type=search_request.search_type,
            query=search_request.query,
            tenant_id=tenant_context.tenant_id,
            execution_time=execution_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error for tenant {tenant_context.tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search service error",
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    tenant_context: TenantContext = Depends(get_current_tenant),
):
    """Interactive chat with the RAG agent."""
    start_time = datetime.utcnow()

    try:
        # Initialize multi-tenant agent
        agent = MultiTenantRAGAgent(tenant_context.tenant_id)

        # Create tenant context for agent
        agent_context = TenantContext(
            tenant_id=tenant_context.tenant_id,
            user_id=tenant_context.user_id,
            session_id=chat_request.session_id or str(uuid.uuid4()),
            metadata=chat_request.search_preferences or {},
        )

        # Get response from agent
        response = await agent.chat(message=chat_request.message, context=agent_context)

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        return ChatResponse(
            response=response.get("response", ""),
            session_id=agent_context.session_id,
            tenant_id=tenant_context.tenant_id,
            sources=response.get("sources", []),
            execution_time=execution_time,
        )

    except Exception as e:
        logger.error(f"Chat error for tenant {tenant_context.tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat service error",
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Interactive Multi-Tenant RAG API",
        "version": "1.0.0",
        "description": "Authenticated FastAPI for multi-tenant hybrid RAG with knowledge graphs",
        "endpoints": {
            "health": "/health",
            "auth": "/auth/login",
            "tenant_info": "/tenants/info",
            "search": "/search",
            "chat": "/chat",
        },
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Interactive Multi-Tenant RAG API")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    logger.info(f"Starting Interactive Multi-Tenant RAG API on {args.host}:{args.port}")

    uvicorn.run(
        "interactive_multi_tenant_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )
