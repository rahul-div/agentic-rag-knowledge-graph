"""
Multi-Tenant FastAPI with JWT Authentication and Tenant Isolation
Provides RESTful endpoints for the multi-tenant RAG system.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    from jose import jwt  # python-jose for JWT handling
except ImportError:
    print(
        "Warning: FastAPI dependencies not installed. Install with: pip install fastapi uvicorn[standard] python-jose[cryptography]"
    )

    # Mock classes for development
    class FastAPI:
        def __init__(self, **kwargs):
            pass

        def add_middleware(self, *args, **kwargs):
            pass

        def get(self, *args, **kwargs):
            return lambda f: f

        def post(self, *args, **kwargs):
            return lambda f: f

        def put(self, *args, **kwargs):
            return lambda f: f

        def delete(self, *args, **kwargs):
            return lambda f: f

    class HTTPException(Exception):
        pass

    class HTTPBearer:
        pass

    class CORSMiddleware:
        pass

    class BaseModel:
        pass

    class Field:
        pass

    def Depends(func):
        return None

    status = type(
        "Status",
        (),
        {
            "HTTP_401_UNAUTHORIZED": 401,
            "HTTP_403_FORBIDDEN": 403,
            "HTTP_404_NOT_FOUND": 404,
            "HTTP_400_BAD_REQUEST": 400,
            "HTTP_500_INTERNAL_SERVER_ERROR": 500,
        },
    )()
    jwt = type(
        "JWT",
        (),
        {
            "encode": lambda *args, **kwargs: "mock_token",
            "decode": lambda *args, **kwargs: {"tenant_id": "mock"},
            "PyJWTError": Exception,
        },
    )()

from .tenant_manager import TenantManager, Document
from .multi_tenant_graphiti import TenantGraphitiClient
from .multi_tenant_agent import MultiTenantRAGAgent, TenantContext

logger = logging.getLogger(__name__)

# Pydantic Models


class TenantCreate(BaseModel):
    """Model for creating a new tenant."""

    id: str = Field(..., description="Unique tenant identifier")
    name: str = Field(..., description="Tenant name")
    email: str = Field(..., description="Tenant email")
    max_documents: int = Field(1000, description="Maximum documents allowed")
    max_storage_mb: int = Field(500, description="Maximum storage in MB")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TenantResponse(BaseModel):
    """Model for tenant response."""

    id: str
    name: str
    email: str
    status: str
    max_documents: int
    max_storage_mb: int
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DocumentCreate(BaseModel):
    """Model for creating a document."""

    title: str = Field(..., description="Document title")
    source: str = Field(..., description="Document source")
    content: str = Field(..., description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DocumentResponse(BaseModel):
    """Model for document response."""

    id: str
    tenant_id: str
    title: str
    source: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class QueryRequest(BaseModel):
    """Model for query requests."""

    query: str = Field(..., description="Search query")
    use_vector: bool = Field(True, description="Use vector search")
    use_graph: bool = Field(True, description="Use graph search")
    max_results: int = Field(10, description="Maximum results to return")


class QueryResponse(BaseModel):
    """Model for query responses."""

    query: str
    response: str
    tenant_id: str
    sources: List[str]
    timestamp: datetime


class SearchRequest(BaseModel):
    """Model for search requests."""

    query: str = Field(..., description="Search query")
    search_type: str = Field(
        "hybrid", description="Type of search: vector, graph, or hybrid"
    )
    limit: int = Field(10, description="Maximum results")
    threshold: float = Field(0.7, description="Similarity threshold for vector search")


class RelationshipCreate(BaseModel):
    """Model for creating relationships."""

    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")
    relationship_type: str = Field(..., description="Type of relationship")
    description: str = Field(..., description="Description of relationship")


class AuthToken(BaseModel):
    """Model for authentication tokens."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Model for JWT token payload."""

    tenant_id: str
    user_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=lambda: ["read"])
    exp: Optional[int] = None


# Authentication and Authorization


class TenantAuth:
    """JWT-based tenant authentication."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.security = HTTPBearer()

    def create_access_token(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)

        to_encode = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "permissions": permissions or ["read"],
            "exp": expire,
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def get_current_tenant(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> TenantContext:
        """Extract tenant context from JWT token."""
        try:
            payload = jwt.decode(
                credentials.credentials, self.secret_key, algorithms=[self.algorithm]
            )

            tenant_id = payload.get("tenant_id")
            if tenant_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )

            return TenantContext(
                tenant_id=tenant_id,
                user_id=payload.get("user_id"),
                permissions=payload.get("permissions", ["read"]),
                metadata=payload.get("metadata", {}),
            )

        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )


# Application Factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting multi-tenant RAG API")

    # Initialize components
    tenant_manager = app.state.tenant_manager
    graphiti_client = app.state.graphiti_client

    await tenant_manager.initialize()
    await graphiti_client.initialize()

    # Initialize agent
    app.state.rag_agent = MultiTenantRAGAgent(tenant_manager, graphiti_client)
    await app.state.rag_agent.initialize()

    logger.info("Multi-tenant RAG API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down multi-tenant RAG API")
    await app.state.rag_agent.close()
    logger.info("Multi-tenant RAG API shutdown complete")


def create_app(
    neon_connection_string: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    jwt_secret_key: str,
    title: str = "Multi-Tenant RAG API",
    version: str = "1.0.0",
) -> FastAPI:
    """Create FastAPI application with multi-tenant configuration."""

    app = FastAPI(
        title=title,
        version=version,
        description="Multi-tenant RAG system with complete data isolation",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize components
    app.state.tenant_manager = TenantManager(neon_connection_string)
    app.state.graphiti_client = TenantGraphitiClient(
        neo4j_uri, neo4j_user, neo4j_password
    )
    app.state.auth = TenantAuth(jwt_secret_key)

    # Routes

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        try:
            # Check database health
            db_health = await app.state.tenant_manager.health_check()

            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": version,
                "database": db_health,
                "components": {
                    "tenant_manager": bool(app.state.tenant_manager.pool),
                    "graphiti_client": app.state.graphiti_client._initialized,
                    "rag_agent": hasattr(app.state, "rag_agent"),
                },
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # Authentication Routes

    @app.post("/auth/token", response_model=AuthToken)
    async def create_token(tenant_id: str, user_id: Optional[str] = None):
        """Create authentication token for tenant."""
        try:
            # Verify tenant exists
            tenant = await app.state.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
                )

            # Create token
            access_token = app.state.auth.create_access_token(
                tenant_id=tenant_id,
                user_id=user_id,
                permissions=["read", "write"],  # Default permissions
            )

            return AuthToken(
                access_token=access_token,
                token_type="bearer",
                expires_in=86400,  # 24 hours
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create authentication token",
            )

    # Tenant Management Routes

    @app.post("/tenants", response_model=TenantResponse)
    async def create_tenant(tenant_data: TenantCreate):
        """Create a new tenant."""
        try:
            tenant = await app.state.tenant_manager.create_tenant(
                tenant_id=tenant_data.id,
                name=tenant_data.name,
                email=tenant_data.email,
                max_documents=tenant_data.max_documents,
                max_storage_mb=tenant_data.max_storage_mb,
                metadata=tenant_data.metadata or {},
            )

            return TenantResponse(
                id=tenant.id,
                name=tenant.name,
                email=tenant.email,
                status=tenant.status,
                max_documents=tenant.max_documents,
                max_storage_mb=tenant.max_storage_mb,
                metadata=tenant.metadata,
                created_at=tenant.created_at,
                updated_at=tenant.updated_at,
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create tenant",
            )

    @app.get("/tenants", response_model=List[TenantResponse])
    async def list_tenants(status_filter: Optional[str] = None):
        """List all tenants."""
        try:
            tenants = await app.state.tenant_manager.list_tenants(status_filter)

            return [
                TenantResponse(
                    id=t.id,
                    name=t.name,
                    email=t.email,
                    status=t.status,
                    max_documents=t.max_documents,
                    max_storage_mb=t.max_storage_mb,
                    metadata=t.metadata,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in tenants
            ]

        except Exception as e:
            logger.error(f"Failed to list tenants: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list tenants",
            )

    @app.get("/tenants/{tenant_id}", response_model=TenantResponse)
    async def get_tenant(tenant_id: str):
        """Get tenant by ID."""
        try:
            tenant = await app.state.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
                )

            return TenantResponse(
                id=tenant.id,
                name=tenant.name,
                email=tenant.email,
                status=tenant.status,
                max_documents=tenant.max_documents,
                max_storage_mb=tenant.max_storage_mb,
                metadata=tenant.metadata,
                created_at=tenant.created_at,
                updated_at=tenant.updated_at,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get tenant",
            )

    @app.delete("/tenants/{tenant_id}")
    async def delete_tenant(tenant_id: str, force: bool = False):
        """Delete a tenant."""
        try:
            success = await app.state.tenant_manager.delete_tenant(
                tenant_id, force=force
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to delete tenant. Use force=true if tenant has data.",
                )

            return {"message": f"Tenant {tenant_id} deleted successfully"}

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete tenant",
            )

    # Document Management Routes

    @app.post("/documents", response_model=Dict[str, Any])
    async def create_document(
        document_data: DocumentCreate,
        tenant_context: TenantContext = Depends(app.state.auth.get_current_tenant),
    ):
        """Create a new document."""
        try:
            # Check permissions
            if "write" not in tenant_context.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to create documents",
                )

            document = Document(
                tenant_id=tenant_context.tenant_id,
                title=document_data.title,
                source=document_data.source,
                content=document_data.content,
                metadata=document_data.metadata or {},
            )

            # Ingest document using the RAG agent
            results = await app.state.rag_agent.ingest_document(document)

            return {
                "message": "Document created successfully",
                "document_id": results["document_id"],
                "chunk_count": results["chunk_count"],
                "graph_added": results["graph_added"],
                "tenant_id": tenant_context.tenant_id,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to create document for tenant {tenant_context.tenant_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create document",
            )

    @app.get("/documents", response_model=List[DocumentResponse])
    async def list_documents(
        limit: int = 100,
        offset: int = 0,
        tenant_context: TenantContext = Depends(app.state.auth.get_current_tenant),
    ):
        """List documents for current tenant."""
        try:
            documents = await app.state.tenant_manager.list_documents(
                tenant_context.tenant_id, limit, offset
            )

            return [
                DocumentResponse(
                    id=d.id,
                    tenant_id=d.tenant_id,
                    title=d.title,
                    source=d.source,
                    content=d.content,
                    metadata=d.metadata,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                )
                for d in documents
            ]

        except Exception as e:
            logger.error(
                f"Failed to list documents for tenant {tenant_context.tenant_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list documents",
            )

    @app.get("/documents/{document_id}", response_model=DocumentResponse)
    async def get_document(
        document_id: str,
        tenant_context: TenantContext = Depends(app.state.auth.get_current_tenant),
    ):
        """Get document by ID."""
        try:
            document = await app.state.tenant_manager.get_document(
                tenant_context.tenant_id, document_id
            )

            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            return DocumentResponse(
                id=document.id,
                tenant_id=document.tenant_id,
                title=document.title,
                source=document.source,
                content=document.content,
                metadata=document.metadata,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to get document {document_id} for tenant {tenant_context.tenant_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get document",
            )

    # RAG and Search Routes

    @app.post("/query", response_model=QueryResponse)
    async def query_rag(
        query_request: QueryRequest,
        tenant_context: TenantContext = Depends(app.state.auth.get_current_tenant),
    ):
        """Query the RAG system."""
        try:
            response = await app.state.rag_agent.query(
                query=query_request.query,
                tenant_context=tenant_context,
                use_vector=query_request.use_vector,
                use_graph=query_request.use_graph,
                max_results=query_request.max_results,
            )

            return QueryResponse(
                query=query_request.query,
                response=response,
                tenant_id=tenant_context.tenant_id,
                sources=[],  # Would be populated from actual search results
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(
                f"Failed to process query for tenant {tenant_context.tenant_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process query",
            )

    @app.post("/search")
    async def search_knowledge_base(
        search_request: SearchRequest,
        tenant_context: TenantContext = Depends(app.state.auth.get_current_tenant),
    ):
        """Search the knowledge base."""
        try:
            results = await app.state.rag_agent.quick_search(
                tenant_id=tenant_context.tenant_id,
                query=search_request.query,
                search_type=search_request.search_type,
            )

            return {
                "query": search_request.query,
                "search_type": search_request.search_type,
                "tenant_id": tenant_context.tenant_id,
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to search for tenant {tenant_context.tenant_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search knowledge base",
            )

    # Knowledge Graph Routes

    @app.post("/relationships")
    async def create_relationship(
        relationship_data: RelationshipCreate,
        tenant_context: TenantContext = Depends(app.state.auth.get_current_tenant),
    ):
        """Create a manual relationship in the knowledge graph."""
        try:
            # Check permissions
            if "write" not in tenant_context.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to create relationships",
                )

            success = await app.state.rag_agent._add_manual_relationship_tool(
                ctx=type(
                    "Context",
                    (),
                    {
                        "get": lambda self, key: tenant_context
                        if key == "tenant_context"
                        else None
                    },
                )(),
                source_entity=relationship_data.source_entity,
                target_entity=relationship_data.target_entity,
                relationship_type=relationship_data.relationship_type,
                description=relationship_data.description,
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create relationship",
                )

            return {
                "message": "Relationship created successfully",
                "tenant_id": tenant_context.tenant_id,
                "relationship": {
                    "source": relationship_data.source_entity,
                    "target": relationship_data.target_entity,
                    "type": relationship_data.relationship_type,
                },
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to create relationship for tenant {tenant_context.tenant_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create relationship",
            )

    @app.get("/entities/{entity_name}/relationships")
    async def get_entity_relationships(
        entity_name: str,
        depth: int = 2,
        tenant_context: TenantContext = Depends(app.state.auth.get_current_tenant),
    ):
        """Get relationships for an entity."""
        try:
            relationships = await app.state.rag_agent._get_entity_relationships_tool(
                ctx=type(
                    "Context",
                    (),
                    {
                        "get": lambda self, key: tenant_context
                        if key == "tenant_context"
                        else None
                    },
                )(),
                entity_name=entity_name,
                depth=depth,
            )

            return {
                "entity_name": entity_name,
                "tenant_id": tenant_context.tenant_id,
                "relationships": relationships,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Failed to get relationships for tenant {tenant_context.tenant_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get entity relationships",
            )

    # Analytics and Monitoring Routes

    @app.get("/stats")
    async def get_tenant_stats(
        tenant_context: TenantContext = Depends(app.state.auth.get_current_tenant),
    ):
        """Get comprehensive tenant statistics."""
        try:
            stats = await app.state.rag_agent._get_tenant_stats_tool(
                ctx=type(
                    "Context",
                    (),
                    {
                        "get": lambda self, key: tenant_context
                        if key == "tenant_context"
                        else None
                    },
                )()
            )

            return stats

        except Exception as e:
            logger.error(
                f"Failed to get stats for tenant {tenant_context.tenant_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get tenant statistics",
            )

    @app.get("/validate-isolation")
    async def validate_isolation(
        tenant_context: TenantContext = Depends(app.state.auth.get_current_tenant),
    ):
        """Validate tenant data isolation."""
        try:
            validation = await app.state.rag_agent.validate_tenant_isolation(
                tenant_context.tenant_id
            )
            return validation

        except Exception as e:
            logger.error(
                f"Failed to validate isolation for tenant {tenant_context.tenant_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate tenant isolation",
            )

    return app


# Development server
if __name__ == "__main__":
    import uvicorn

    # Configuration for development
    app = create_app(
        neon_connection_string="postgresql://user:pass@localhost/rag_db",
        neo4j_uri="neo4j://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        jwt_secret_key="your-secret-key-change-in-production",
    )

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="info")
