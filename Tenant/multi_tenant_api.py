"""
Multi-Tenant FastAPI with JWT Authentication and Project-per-Tenant Isolation
Provides RESTful endpoints for the multi-tenant RAG system using official Neon best practices.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException, Depends, status, Request
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    from jose import jwt, JWTError
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
            "JWTError": Exception,
        },
    )()

    JWTError = Exception

from tenant_manager import TenantManager
from tenant_graphiti_client import TenantGraphitiClient
from multi_tenant_agent import MultiTenantRAGAgent, TenantContext


# Document model for tenant operations (defined here for direct script execution)
class Document(BaseModel):
    """Document model for tenant operations."""

    id: Optional[str] = None
    title: str
    source: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


logger = logging.getLogger(__name__)

# Pydantic Models for API


class TenantCreateRequest(BaseModel):
    """Model for creating a new tenant."""

    name: str = Field(..., description="Tenant name")
    email: str = Field(..., description="Tenant email")
    region: str = Field("aws-us-east-1", description="Neon region")
    plan: str = Field("basic", description="Tenant plan")
    max_documents: int = Field(1000, description="Maximum documents allowed")
    max_storage_mb: int = Field(500, description="Maximum storage in MB")


class TenantResponse(BaseModel):
    """Model for tenant information."""

    id: str
    name: str
    email: str
    neon_project_id: str
    region: str
    status: str
    plan: str
    max_documents: int
    max_storage_mb: int
    created_at: datetime
    updated_at: datetime


class DocumentCreateRequest(BaseModel):
    """Model for creating a document."""

    title: str = Field(..., description="Document title")
    source: str = Field(..., description="Document source")
    content: str = Field(..., description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DocumentResponse(BaseModel):
    """Model for document information."""

    id: str
    title: str
    source: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None


class QueryRequest(BaseModel):
    """Model for RAG queries."""

    query: str = Field(..., description="Query text")
    use_vector: bool = Field(True, description="Use vector search")
    use_graph: bool = Field(True, description="Use graph search")
    max_results: int = Field(10, description="Maximum results")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class QueryResponse(BaseModel):
    """Model for query responses."""

    response: str
    tenant_id: str
    timestamp: str
    metadata: Dict[str, Any]


class RelationshipRequest(BaseModel):
    """Model for creating relationships."""

    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")
    relationship_type: str = Field(..., description="Relationship type")
    description: Optional[str] = Field(None, description="Relationship description")


class HealthResponse(BaseModel):
    """Model for health check response."""

    status: str
    timestamp: str
    version: str
    tenant_count: int
    database_status: str
    graph_status: str


class StatsResponse(BaseModel):
    """Model for tenant statistics."""

    tenant_id: str
    documents: int
    chunks: int
    graph_entities: int
    graph_relationships: int
    timestamp: str


# Security
security = HTTPBearer()


class JWTManager:
    """JWT token management for tenant authentication."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(self, tenant_id: str, user_id: Optional[str] = None) -> str:
        """Create JWT token with tenant context."""
        payload = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )


# Global variables (will be set in create_app)
tenant_manager: Optional[TenantManager] = None
jwt_manager: Optional[JWTManager] = None
rag_agent: Optional[MultiTenantRAGAgent] = None


async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TenantContext:
    """Extract tenant context from JWT token."""
    try:
        payload = jwt_manager.verify_token(credentials.credentials)
        tenant_id = payload.get("tenant_id")
        user_id = payload.get("user_id")

        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing tenant_id",
            )

        # Verify tenant exists
        tenant = await tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
            )

        if tenant.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Tenant is not active"
            )

        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            permissions=["read", "write"],  # Simplified permissions
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def create_app(
    neon_api_key: str,
    catalog_database_url: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    jwt_secret_key: str,
    openai_api_key: str,
    default_region: str = "aws-us-east-1",
    title: str = "Multi-Tenant RAG API",
    version: str = "2.0.0",
    description: str = "Multi-tenant RAG system with project-per-tenant architecture",
) -> FastAPI:
    """Create FastAPI application with project-per-tenant architecture."""

    global tenant_manager, jwt_manager, rag_agent

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan management."""
        # Initialize components
        global tenant_manager, jwt_manager, rag_agent

        # Initialize tenant manager
        tenant_manager = TenantManager(
            neon_api_key=neon_api_key,
            catalog_database_url=catalog_database_url,
            default_region=default_region,
        )
        await tenant_manager.initialize()

        # Initialize Graphiti client
        graphiti_client = TenantGraphitiClient(
            neo4j_uri=neo4j_uri, neo4j_user=neo4j_user, neo4j_password=neo4j_password
        )
        await graphiti_client.initialize()

        # Initialize RAG agent
        rag_agent = MultiTenantRAGAgent(
            tenant_manager=tenant_manager,
            graphiti_client=graphiti_client,
            model_name="gpt-4",
        )

        # Initialize JWT manager
        jwt_manager = JWTManager(secret_key=jwt_secret_key)

        logger.info("Multi-tenant RAG API started successfully")
        yield

        # Cleanup
        await tenant_manager.close()
        await graphiti_client.close()
        logger.info("Multi-tenant RAG API shutdown complete")

    # Create FastAPI app
    app = FastAPI(
        title=title, version=version, description=description, lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        try:
            # Check tenant count
            tenants = await tenant_manager.list_tenants(limit=1)
            tenant_count = len(tenants)

            return HealthResponse(
                status="healthy",
                timestamp=datetime.now().isoformat(),
                version=version,
                tenant_count=tenant_count,
                database_status="connected",
                graph_status="connected",
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthResponse(
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                version=version,
                tenant_count=0,
                database_status="error",
                graph_status="error",
            )

    # Tenant Management Endpoints

    @app.post("/tenants", response_model=TenantResponse)
    async def create_tenant(request: TenantCreateRequest):
        """Create new tenant with dedicated Neon project."""
        try:
            tenant_id = await tenant_manager.create_tenant(
                name=request.name,
                email=request.email,
                region=request.region,
                plan=request.plan,
                max_documents=request.max_documents,
                max_storage_mb=request.max_storage_mb,
            )

            tenant = await tenant_manager.get_tenant(tenant_id)
            return TenantResponse(
                id=tenant.id,
                name=tenant.name,
                email=tenant.email,
                neon_project_id=tenant.neon_project_id,
                region=tenant.region,
                status=tenant.status,
                plan=tenant.plan,
                max_documents=tenant.max_documents,
                max_storage_mb=tenant.max_storage_mb,
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
    async def list_tenants(
        status_filter: Optional[str] = None, limit: int = 100, offset: int = 0
    ):
        """List tenants."""
        try:
            tenants = await tenant_manager.list_tenants(
                status=status_filter, limit=limit, offset=offset
            )

            return [
                TenantResponse(
                    id=tenant.id,
                    name=tenant.name,
                    email=tenant.email,
                    neon_project_id=tenant.neon_project_id,
                    region=tenant.region,
                    status=tenant.status,
                    plan=tenant.plan,
                    max_documents=tenant.max_documents,
                    max_storage_mb=tenant.max_storage_mb,
                    created_at=tenant.created_at,
                    updated_at=tenant.updated_at,
                )
                for tenant in tenants
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
            tenant = await tenant_manager.get_tenant(tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
                )

            return TenantResponse(
                id=tenant.id,
                name=tenant.name,
                email=tenant.email,
                neon_project_id=tenant.neon_project_id,
                region=tenant.region,
                status=tenant.status,
                plan=tenant.plan,
                max_documents=tenant.max_documents,
                max_storage_mb=tenant.max_storage_mb,
                created_at=tenant.created_at,
                updated_at=tenant.updated_at,
            )

        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get tenant",
            )

    @app.delete("/tenants/{tenant_id}")
    async def delete_tenant(tenant_id: str, force: bool = False):
        """Delete tenant and their Neon project."""
        try:
            success = await tenant_manager.delete_tenant(tenant_id, force=force)
            if success:
                return {"message": f"Tenant {tenant_id} deleted successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
                )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete tenant",
            )

    # Authentication Endpoints

    @app.post("/auth/token")
    async def create_auth_token(tenant_id: str, user_id: Optional[str] = None):
        """Create authentication token for tenant."""
        try:
            # Verify tenant exists
            tenant = await tenant_manager.get_tenant(tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
                )

            token = jwt_manager.create_token(tenant_id, user_id)
            return {"access_token": token, "token_type": "bearer"}

        except Exception as e:
            logger.error(f"Failed to create token for tenant {tenant_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create token",
            )

    # Document Management Endpoints

    @app.post("/documents", response_model=DocumentResponse)
    async def create_document(
        request: DocumentCreateRequest,
        tenant_context: TenantContext = Depends(get_current_tenant),
    ):
        """Create and ingest document into tenant's dedicated database."""
        try:
            document = Document(
                title=request.title,
                source=request.source,
                content=request.content,
                metadata=request.metadata or {},
            )

            # Ingest through RAG agent (handles both database and graph)
            await rag_agent.ingest_document(
                tenant_context=tenant_context, document=document
            )

            # Get the created document
            created_doc = await tenant_manager.get_document(
                tenant_context.tenant_id, document.id
            )

            return DocumentResponse(
                id=created_doc.id,
                title=created_doc.title,
                source=created_doc.source,
                content=created_doc.content,
                metadata=created_doc.metadata,
                created_at=created_doc.created_at,
                updated_at=created_doc.updated_at,
            )

        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create document",
            )

    @app.get("/documents/{document_id}", response_model=DocumentResponse)
    async def get_document(
        document_id: str, tenant_context: TenantContext = Depends(get_current_tenant)
    ):
        """Get document from tenant's dedicated database."""
        try:
            document = await tenant_manager.get_document(
                tenant_context.tenant_id, document_id
            )

            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            return DocumentResponse(
                id=document.id,
                title=document.title,
                source=document.source,
                content=document.content,
                metadata=document.metadata,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )

        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get document",
            )

    # RAG Operation Endpoints

    @app.post("/query", response_model=QueryResponse)
    async def query_rag_system(
        request: QueryRequest,
        tenant_context: TenantContext = Depends(get_current_tenant),
    ):
        """Query the RAG system with tenant isolation."""
        try:
            result = await rag_agent.query(
                tenant_context=tenant_context,
                query=request.query,
                context=request.context,
            )

            return QueryResponse(
                response=result["response"],
                tenant_id=result["tenant_id"],
                timestamp=result["timestamp"],
                metadata=result["metadata"],
            )

        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process query",
            )

    @app.post("/search")
    async def search_knowledge_base(
        query: str,
        limit: int = 10,
        tenant_context: TenantContext = Depends(get_current_tenant),
    ):
        """Search tenant's knowledge base."""
        try:
            # Use hybrid search for comprehensive results
            results = await rag_agent.hybrid_search(
                tenant_context=tenant_context, query=query, limit=limit
            )

            return results

        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search knowledge base",
            )

    @app.get("/stats", response_model=StatsResponse)
    async def get_tenant_stats(
        tenant_context: TenantContext = Depends(get_current_tenant),
    ):
        """Get statistics for tenant's data."""
        try:
            stats = await rag_agent.get_tenant_stats(tenant_context.tenant_id)

            return StatsResponse(
                tenant_id=stats["tenant_id"],
                documents=stats["documents"],
                chunks=stats["chunks"],
                graph_entities=stats["graph_entities"],
                graph_relationships=stats["graph_relationships"],
                timestamp=stats["timestamp"],
            )

        except Exception as e:
            logger.error(f"Failed to get tenant stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get tenant stats",
            )

    @app.get("/validate-isolation")
    async def validate_tenant_isolation(
        tenant_context: TenantContext = Depends(get_current_tenant),
    ):
        """Validate tenant isolation is working correctly."""
        try:
            results = await rag_agent.validate_isolation(tenant_context.tenant_id)
            return results

        except Exception as e:
            logger.error(f"Failed to validate isolation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate isolation",
            )

    return app
