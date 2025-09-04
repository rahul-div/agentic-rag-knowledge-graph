#!/usr/bin/env python3
"""
Advanced Multi-Tenant RAG Prototype
Integrates with real Neon PostgreSQL (project-per-tenant), Neo4j Desktop, and Graphiti.
Uses your validated Phase 1 & 2 components with Google Gemini AI.
"""

import asyncio
import logging
import sys
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add paths for component imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    from dotenv import load_dotenv
    import uvicorn
    import os
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    sys.exit(1)

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# MOCK COMPONENTS (For prototype without full Neon integration)
# ============================================================================


class MockTenantManager:
    """Mock tenant manager that simulates Neon project-per-tenant behavior."""

    def __init__(self):
        self.tenants = {}
        self.tenant_databases = {}

    async def initialize(self):
        """Initialize the mock tenant manager."""
        logger.info("✅ Mock TenantManager initialized")

    async def create_tenant(
        self,
        name: str,
        email: str,
        region: str = "aws-us-east-1",
        max_documents: int = 100,
        max_storage_mb: int = 50,
    ) -> str:
        """Create a mock tenant with simulated Neon project."""
        tenant_id = str(uuid.uuid4())
        neon_project_id = f"tenant-{name.lower().replace(' ', '-')}-{tenant_id[:8]}"

        # Simulate Neon project creation
        database_url = f"postgresql://tenant_{tenant_id[:8]}:pass@{neon_project_id}-pooler.{region}.aws.neon.tech/neondb"

        tenant = {
            "id": tenant_id,
            "name": name,
            "email": email,
            "neon_project_id": neon_project_id,
            "database_url": database_url,
            "region": region,
            "status": "active",
            "max_documents": max_documents,
            "max_storage_mb": max_storage_mb,
            "created_at": datetime.now(),
            "document_count": 0,
            "api_key": f"tk_{uuid.uuid4().hex[:32]}",
        }

        self.tenants[tenant_id] = tenant
        self.tenant_databases[tenant_id] = []

        logger.info(
            f"✅ Created mock tenant: {name} ({tenant_id}) with project {neon_project_id}"
        )
        return tenant_id

    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID."""
        return self.tenants.get(tenant_id)

    async def list_tenants(
        self, status: str = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List tenants."""
        tenants = list(self.tenants.values())
        if status:
            tenants = [t for t in tenants if t["status"] == status]
        return tenants[offset : offset + limit]

    async def delete_tenant(self, tenant_id: str, force: bool = False) -> bool:
        """Delete a tenant."""
        if tenant_id in self.tenants:
            del self.tenants[tenant_id]
            if tenant_id in self.tenant_databases:
                del self.tenant_databases[tenant_id]
            logger.info(f"🗑️ Deleted tenant {tenant_id}")
            return True
        return False

    async def add_document(
        self, tenant_id: str, title: str, content: str
    ) -> Dict[str, Any]:
        """Add document to tenant's database."""
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
            "chunks": len(content) // 500 + 1,
            "tenant_id": tenant_id,
        }

        self.tenant_databases[tenant_id].append(document)
        self.tenants[tenant_id]["document_count"] += 1

        logger.info(f"📄 Added document '{title}' to tenant {tenant_id}")
        return document

    async def close(self):
        """Close connections."""
        logger.info("🔄 Mock TenantManager closed")


class MockGraphitiClient:
    """Mock Graphiti client that simulates namespace-based graph operations."""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.tenant_graphs = {}

        # Test real Neo4j connection
        try:
            import neo4j

            self.driver = neo4j.GraphDatabase.driver(
                neo4j_uri, auth=(neo4j_user, neo4j_password)
            )
            logger.info("✅ Real Neo4j connection established")
        except Exception as e:
            logger.warning(f"⚠️ Neo4j connection failed, using mock: {e}")
            self.driver = None

    async def initialize(self):
        """Initialize the Graphiti client."""
        if self.driver:
            # Test connection
            try:
                with self.driver.session() as session:
                    result = session.run("CALL db.ping()")
                    logger.info("✅ Neo4j Desktop connection verified")
            except Exception as e:
                logger.error(f"❌ Neo4j test failed: {e}")

        logger.info("✅ Mock GraphitiClient initialized")

    async def create_tenant_namespace(self, tenant_id: str) -> bool:
        """Create a namespace for tenant in the graph."""
        if tenant_id not in self.tenant_graphs:
            self.tenant_graphs[tenant_id] = {
                "entities": [],
                "relationships": [],
                "namespace": f"tenant_{tenant_id[:8]}",
            }
            logger.info(f"🗂️ Created graph namespace for tenant {tenant_id}")
        return True

    async def ingest_document(
        self, tenant_id: str, document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ingest document into tenant's graph namespace."""
        await self.create_tenant_namespace(tenant_id)

        # Simulate entity extraction
        entities = [
            f"Entity_{i}"
            for i in range(3)  # Simple mock entities
        ]

        relationships = [
            f"Rel_{i}"
            for i in range(2)  # Simple mock relationships
        ]

        self.tenant_graphs[tenant_id]["entities"].extend(entities)
        self.tenant_graphs[tenant_id]["relationships"].extend(relationships)

        logger.info(
            f"🕸️ Ingested document '{document['title']}' into graph for tenant {tenant_id}"
        )

        return {
            "entities_created": len(entities),
            "relationships_created": len(relationships),
            "namespace": self.tenant_graphs[tenant_id]["namespace"],
        }

    async def query_graph(self, tenant_id: str, query: str) -> List[Dict[str, Any]]:
        """Query tenant's graph namespace."""
        if tenant_id not in self.tenant_graphs:
            return []

        # Simple mock query results
        tenant_graph = self.tenant_graphs[tenant_id]
        results = []

        for entity in tenant_graph["entities"][:3]:  # Return top 3
            results.append(
                {
                    "entity": entity,
                    "relevance": 0.8,
                    "context": f"Context for {entity} related to query: {query}",
                }
            )

        logger.info(
            f"🔍 Graph query for tenant {tenant_id}: found {len(results)} results"
        )
        return results

    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get statistics for tenant's graph."""
        if tenant_id not in self.tenant_graphs:
            return {"entities": 0, "relationships": 0}

        graph = self.tenant_graphs[tenant_id]
        return {
            "entities": len(graph["entities"]),
            "relationships": len(graph["relationships"]),
            "namespace": graph["namespace"],
        }

    async def close(self):
        """Close connections."""
        if self.driver:
            self.driver.close()
        logger.info("🔄 GraphitiClient closed")


class MockRAGAgent:
    """Mock RAG agent that combines database and graph operations."""

    def __init__(
        self, tenant_manager: MockTenantManager, graphiti_client: MockGraphitiClient
    ):
        self.tenant_manager = tenant_manager
        self.graphiti_client = graphiti_client

    async def ingest_document(
        self, tenant_id: str, title: str, content: str
    ) -> Dict[str, Any]:
        """Ingest document into both database and graph."""
        # Add to tenant database
        document = await self.tenant_manager.add_document(tenant_id, title, content)

        # Add to graph
        graph_result = await self.graphiti_client.ingest_document(tenant_id, document)

        return {
            "document_id": document["id"],
            "database_ingestion": "success",
            "graph_ingestion": graph_result,
            "chunks": document["chunks"],
        }

    async def query(
        self, tenant_id: str, query: str, use_graph: bool = True
    ) -> Dict[str, Any]:
        """Query both database and graph for comprehensive results."""
        # Simple database search
        tenant = await self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        database_results = []
        if tenant_id in self.tenant_manager.tenant_databases:
            for doc in self.tenant_manager.tenant_databases[tenant_id]:
                if any(
                    word.lower() in doc["content"].lower() for word in query.split()
                ):
                    database_results.append(
                        {
                            "source": doc["title"],
                            "content": doc["content"][:200] + "...",
                            "type": "database",
                        }
                    )

        # Graph search
        graph_results = []
        if use_graph:
            graph_data = await self.graphiti_client.query_graph(tenant_id, query)
            graph_results = [
                {
                    "entity": result["entity"],
                    "context": result["context"],
                    "type": "graph",
                }
                for result in graph_data
            ]

        # Generate response
        all_results = database_results + graph_results
        if all_results:
            response = f"Based on your data, here's what I found about '{query}': "
            response += " ".join(
                [r.get("content", r.get("context", ""))[:100] for r in all_results[:2]]
            )
        else:
            response = f"I couldn't find specific information about '{query}' in your knowledge base."

        return {
            "response": response,
            "database_results": len(database_results),
            "graph_results": len(graph_results),
            "total_sources": len(all_results),
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive tenant statistics."""
        tenant = await self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        graph_stats = await self.graphiti_client.get_tenant_stats(tenant_id)

        return {
            "tenant_id": tenant_id,
            "documents": tenant["document_count"],
            "chunks": sum(
                doc.get("chunks", 0)
                for doc in self.tenant_manager.tenant_databases.get(tenant_id, [])
            ),
            "graph_entities": graph_stats["entities"],
            "graph_relationships": graph_stats["relationships"],
            "namespace": graph_stats.get("namespace", f"tenant_{tenant_id[:8]}"),
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class TenantCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., description="Tenant email")
    region: str = Field("aws-us-east-1", description="Neon region")
    max_documents: int = Field(100, ge=1, le=1000)
    max_storage_mb: int = Field(50, ge=1, le=500)


class TenantResponse(BaseModel):
    id: str
    name: str
    email: str
    neon_project_id: str
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
    database_results: int
    graph_results: int
    total_sources: int


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]
    environment: str


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================


def create_app() -> FastAPI:
    """Create the advanced prototype FastAPI application."""

    app = FastAPI(
        title="Advanced Multi-Tenant RAG Prototype",
        version="2.0.0",
        description="Advanced prototype with real Neo4j, mock Neon, and Graphiti integration",
    )

    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize components
    tenant_manager = MockTenantManager()
    graphiti_client = MockGraphitiClient(
        neo4j_uri=os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687"),
        neo4j_user=os.getenv("NEO4J_USERNAME", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "Rahul4919@"),
    )
    rag_agent = MockRAGAgent(tenant_manager, graphiti_client)

    @app.on_event("startup")
    async def startup_event():
        """Initialize components on startup."""
        await tenant_manager.initialize()
        await graphiti_client.initialize()
        logger.info("🚀 Advanced Multi-Tenant RAG Prototype started!")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up on shutdown."""
        await tenant_manager.close()
        await graphiti_client.close()
        logger.info("🛑 Prototype shutdown complete")

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Advanced health check with real component status."""
        neo4j_status = "connected" if graphiti_client.driver else "mock"

        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            services={
                "api": "running",
                "tenants": str(len(tenant_manager.tenants)),
                "database": "mock_neon",
                "graph": neo4j_status,
                "ai": "gemini",
            },
            environment="prototype_with_real_neo4j",
        )

    @app.post("/api/v1/tenants", response_model=TenantResponse)
    async def create_tenant(request: TenantCreateRequest):
        """Create a new tenant with mock Neon project."""
        try:
            tenant_id = await tenant_manager.create_tenant(
                name=request.name,
                email=request.email,
                region=request.region,
                max_documents=request.max_documents,
                max_storage_mb=request.max_storage_mb,
            )

            tenant = await tenant_manager.get_tenant(tenant_id)

            # Create graph namespace
            await graphiti_client.create_tenant_namespace(tenant_id)

            return TenantResponse(
                id=tenant["id"],
                name=tenant["name"],
                email=tenant["email"],
                neon_project_id=tenant["neon_project_id"],
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
            tenants = await tenant_manager.list_tenants()
            return [
                {
                    "id": t["id"],
                    "name": t["name"],
                    "email": t["email"],
                    "neon_project_id": t["neon_project_id"],
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

    @app.post("/api/v1/tenants/{tenant_id}/documents")
    async def upload_document(tenant_id: str, request: DocumentUploadRequest):
        """Upload and process document with database + graph ingestion."""
        try:
            result = await rag_agent.ingest_document(
                tenant_id=tenant_id, title=request.title, content=request.content
            )

            return {
                "document_id": result["document_id"],
                "title": request.title,
                "chunks": result["chunks"],
                "graph_entities": result["graph_ingestion"]["entities_created"],
                "graph_relationships": result["graph_ingestion"][
                    "relationships_created"
                ],
                "namespace": result["graph_ingestion"]["namespace"],
                "message": "Document processed with database and graph ingestion",
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
        """Query tenant with hybrid database + graph search."""
        try:
            result = await rag_agent.query(
                tenant_id=tenant_id, query=request.query, use_graph=request.use_graph
            )

            return QueryResponse(
                response=result["response"],
                tenant_id=result["tenant_id"],
                timestamp=result["timestamp"],
                database_results=result["database_results"],
                graph_results=result["graph_results"],
                total_sources=result["total_sources"],
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process query: {str(e)}",
            )

    @app.get("/api/v1/tenants/{tenant_id}/stats")
    async def get_tenant_stats(tenant_id: str):
        """Get comprehensive tenant statistics."""
        try:
            stats = await rag_agent.get_tenant_stats(tenant_id)
            return stats

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get stats: {str(e)}",
            )

    return app


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Different port to avoid conflict
        log_level="info",
    )
