#!/usr/bin/env python3
"""
Simplified Multi-Tenant RAG Prototype API
Core functionality for testing 3-4 tenant architecture with minimal complexity.
"""

import logging
import sys
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI, HTTPException, status
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    from dotenv import load_dotenv
    import uvicorn
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    sys.exit(1)

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class TenantCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., description="Tenant email")
    max_documents: int = Field(100, ge=1, le=1000)


class TenantResponse(BaseModel):
    id: str
    name: str
    email: str
    status: str
    max_documents: int
    created_at: datetime
    api_key: str


class DocumentUploadRequest(BaseModel):
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")


class QueryRequest(BaseModel):
    query: str = Field(..., description="Query text")
    use_graph: bool = Field(True, description="Use graph search")


class QueryResponse(BaseModel):
    response: str
    tenant_id: str
    timestamp: str
    sources: List[str] = []


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]


# ============================================================================
# SIMPLIFIED TENANT STORE (In-Memory for Prototype)
# ============================================================================


class SimpleTenantStore:
    """In-memory tenant store for prototype testing."""

    def __init__(self):
        self.tenants: Dict[str, Dict[str, Any]] = {}
        self.tenant_documents: Dict[str, List[Dict[str, Any]]] = {}

    def create_tenant(
        self, name: str, email: str, max_documents: int
    ) -> Dict[str, Any]:
        """Create a new tenant."""
        tenant_id = str(uuid.uuid4())
        api_key = f"tk_{uuid.uuid4().hex[:32]}"

        tenant = {
            "id": tenant_id,
            "name": name,
            "email": email,
            "status": "active",
            "max_documents": max_documents,
            "created_at": datetime.now(),
            "api_key": api_key,
            "document_count": 0,
        }

        self.tenants[tenant_id] = tenant
        self.tenant_documents[tenant_id] = []

        logger.info(f"Created tenant: {name} ({tenant_id})")
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID."""
        return self.tenants.get(tenant_id)

    def list_tenants(self) -> List[Dict[str, Any]]:
        """List all tenants."""
        return list(self.tenants.values())

    def add_document(self, tenant_id: str, title: str, content: str) -> Dict[str, Any]:
        """Add document to tenant."""
        if tenant_id not in self.tenants:
            raise ValueError("Tenant not found")

        tenant = self.tenants[tenant_id]
        if tenant["document_count"] >= tenant["max_documents"]:
            raise ValueError("Document limit exceeded")

        doc_id = str(uuid.uuid4())
        document = {
            "id": doc_id,
            "title": title,
            "content": content,
            "created_at": datetime.now(),
            "chunks": len(content) // 500 + 1,  # Simple chunking estimate
        }

        self.tenant_documents[tenant_id].append(document)
        self.tenants[tenant_id]["document_count"] += 1

        logger.info(f"Added document {title} to tenant {tenant_id}")
        return document

    def search_documents(self, tenant_id: str, query: str) -> List[str]:
        """Simple document search for tenant."""
        if tenant_id not in self.tenant_documents:
            return []

        results = []
        query_lower = query.lower()
        for doc in self.tenant_documents[tenant_id]:
            # Check both title and content for matches
            if (
                query_lower in doc["content"].lower()
                or query_lower in doc["title"].lower()
                or any(word in doc["content"].lower() for word in query_lower.split())
            ):
                results.append(f"{doc['title']}: {doc['content'][:200]}...")

        return results[:5]  # Return top 5 matches


# ============================================================================
# API APPLICATION
# ============================================================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Multi-Tenant RAG Prototype",
        version="1.0.0",
        description="Simplified prototype for testing multi-tenant architecture",
    )

    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize tenant store
    tenant_store = SimpleTenantStore()

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            services={
                "api": "running",
                "tenants": str(len(tenant_store.tenants)),
                "database": "simulated",
                "graph": "simulated",
            },
        )

    @app.post("/api/v1/tenants", response_model=TenantResponse)
    async def create_tenant(request: TenantCreateRequest):
        """Create a new tenant."""
        try:
            tenant = tenant_store.create_tenant(
                name=request.name,
                email=request.email,
                max_documents=request.max_documents,
            )

            return TenantResponse(
                id=tenant["id"],
                name=tenant["name"],
                email=tenant["email"],
                status=tenant["status"],
                max_documents=tenant["max_documents"],
                created_at=tenant["created_at"],
                api_key=tenant["api_key"],
            )

        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create tenant: {str(e)}",
            )

    @app.get("/api/v1/tenants")
    async def list_tenants():
        """List all tenants."""
        try:
            tenants = tenant_store.list_tenants()
            return [
                {
                    "id": t["id"],
                    "name": t["name"],
                    "email": t["email"],
                    "status": t["status"],
                    "document_count": t["document_count"],
                    "created_at": t["created_at"].isoformat(),
                }
                for t in tenants
            ]
        except Exception as e:
            logger.error(f"Failed to list tenants: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list tenants: {str(e)}",
            )

    @app.get("/api/v1/tenants/{tenant_id}")
    async def get_tenant(tenant_id: str):
        """Get tenant by ID."""
        tenant = tenant_store.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
            )

        return {
            "id": tenant["id"],
            "name": tenant["name"],
            "email": tenant["email"],
            "status": tenant["status"],
            "document_count": tenant["document_count"],
            "max_documents": tenant["max_documents"],
            "created_at": tenant["created_at"].isoformat(),
        }

    @app.post("/api/v1/tenants/{tenant_id}/documents")
    async def upload_document(tenant_id: str, request: DocumentUploadRequest):
        """Upload document to tenant."""
        try:
            document = tenant_store.add_document(
                tenant_id=tenant_id, title=request.title, content=request.content
            )

            return {
                "id": document["id"],
                "title": document["title"],
                "chunks": document["chunks"],
                "created_at": document["created_at"].isoformat(),
                "message": "Document uploaded and processed successfully",
            }

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload document: {str(e)}",
            )

    @app.post("/api/v1/tenants/{tenant_id}/query", response_model=QueryResponse)
    async def query_tenant(tenant_id: str, request: QueryRequest):
        """Query tenant's knowledge base."""
        try:
            tenant = tenant_store.get_tenant(tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
                )

            # Simple search simulation
            sources = tenant_store.search_documents(tenant_id, request.query)

            # Generate simple response
            if sources:
                response = f"Based on your documents, here's what I found about '{request.query}': {sources[0][:200]}..."
            else:
                response = f"I couldn't find specific information about '{request.query}' in your documents. Please upload relevant documents first."

            return QueryResponse(
                response=response,
                tenant_id=tenant_id,
                timestamp=datetime.now().isoformat(),
                sources=sources,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process query: {str(e)}",
            )

    @app.get("/api/v1/tenants/{tenant_id}/stats")
    async def get_tenant_stats(tenant_id: str):
        """Get tenant statistics."""
        tenant = tenant_store.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
            )

        documents = tenant_store.tenant_documents.get(tenant_id, [])
        total_chunks = sum(doc.get("chunks", 0) for doc in documents)

        return {
            "tenant_id": tenant_id,
            "documents": len(documents),
            "chunks": total_chunks,
            "graph_entities": len(documents) * 3,  # Simulated
            "graph_relationships": len(documents) * 2,  # Simulated
            "timestamp": datetime.now().isoformat(),
        }

    return app


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
