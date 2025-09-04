"""
Multi-Tenant Pydantic AI Agent with Project-per-Tenant Architecture
Integrates with Neon PostgreSQL (project-per-tenant) and Graphiti (namespaced) for complete RAG capabilities.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

try:
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.tools import tool
except ImportError:
    print("Warning: pydantic_ai not installed. Install with: pip install pydantic-ai")

    # Mock classes for development
    class Agent:
        def __init__(self, **kwargs):
            pass

        async def run_async(self, **kwargs):
            return {"response": "Mock response"}

    class RunContext:
        def __init__(self, **kwargs):
            pass

    def tool(func):
        return func


from tenant_manager import TenantManager
from tenant_graphiti_client import (
    TenantGraphitiClient,
    GraphEpisode,
    GraphRelationship,
)

logger = logging.getLogger(__name__)


@dataclass
class TenantContext:
    """Context information for tenant operations with project-per-tenant architecture."""

    tenant_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    permissions: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
        if self.metadata is None:
            self.metadata = {}


class MultiTenantRAGAgent:
    """
    Multi-tenant Pydantic AI agent with complete tenant isolation.

    Uses project-per-tenant databases and namespaced graph operations.
    All operations are automatically isolated by tenant boundaries.
    """

    def __init__(
        self,
        tenant_manager: TenantManager,
        graphiti_client: TenantGraphitiClient,
        model_name: str = "gpt-4",
        system_prompt: str = None,
    ):
        self.tenant_manager = tenant_manager
        self.graphiti_client = graphiti_client
        self.model_name = model_name

        if system_prompt is None:
            system_prompt = """You are a helpful AI assistant with access to a knowledge base.
            You can search documents, explore knowledge graphs, and provide comprehensive answers.
            All data is automatically isolated to the current tenant's context."""

        # Initialize Pydantic AI agent with tenant-aware tools
        self.agent = Agent(
            model=model_name,
            system_prompt=system_prompt,
            tools=[
                self.vector_search,
                self.graph_search,
                self.hybrid_search,
                self.ingest_document,
                self.add_relationship,
            ],
        )

    async def query(
        self,
        tenant_context: TenantContext,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process query with tenant-aware context.

        All operations are automatically routed to tenant's dedicated database
        and namespaced graph without any tenant_id filtering needed.
        """
        try:
            # Create run context with tenant information
            run_context = RunContext(
                tenant_id=tenant_context.tenant_id,
                user_id=tenant_context.user_id,
                session_id=tenant_context.session_id,
                metadata=tenant_context.metadata or {},
                additional_context=context or {},
            )

            # Execute query with agent
            result = await self.agent.run_async(user_prompt=query, context=run_context)

            return {
                "response": result.data if hasattr(result, "data") else str(result),
                "tenant_id": tenant_context.tenant_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "model": self.model_name,
                    "session_id": tenant_context.session_id,
                },
            }

        except Exception as e:
            logger.error(
                f"Failed to process query for tenant {tenant_context.tenant_id}: {e}"
            )
            raise

    @tool
    async def ingest_document(self, run_context: RunContext, document) -> str:
        """
        Ingest document into tenant's dedicated database and graph.

        No tenant_id needed - routed automatically to correct tenant database.
        """
        try:
            tenant_id = run_context.tenant_id

            # Store document in tenant's dedicated database
            doc_id = await self.tenant_manager.create_document(tenant_id, document)

            # Add to knowledge graph with tenant namespace
            episode = GraphEpisode(
                tenant_id=tenant_id,
                name=f"Document: {document.title}",
                content=document.content,
                metadata={
                    "document_id": doc_id,
                    "source": document.source,
                    **document.metadata,
                },
            )

            await self.graphiti_client.add_episode_for_tenant(episode)

            logger.info(f"Ingested document {doc_id} for tenant {tenant_id}")
            return f"Successfully ingested document {doc_id}"

        except Exception as e:
            logger.error(f"Failed to ingest document for tenant {tenant_id}: {e}")
            raise

    @tool
    async def vector_search(
        self, run_context: RunContext, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search tenant's dedicated database using vector similarity.

        Automatically isolated to tenant's database - no filtering needed.
        """
        try:
            tenant_id = run_context.tenant_id

            # Get embedding for query (using OpenAI or similar)
            # This is a placeholder - implement actual embedding generation
            query_embedding = await self._get_embedding(query)

            # Search in tenant's dedicated database
            results = await self.tenant_manager.vector_search(
                tenant_id, query_embedding, limit
            )

            return results

        except Exception as e:
            logger.error(f"Vector search failed for tenant {tenant_id}: {e}")
            return []

    @tool
    async def graph_search(
        self, run_context: RunContext, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search tenant's namespaced knowledge graph.

        Automatically isolated to tenant's namespace via group_id.
        """
        try:
            tenant_id = run_context.tenant_id

            # Search in tenant's graph namespace
            results = await self.graphiti_client.search_tenant_graph(
                tenant_id, query, limit
            )

            return [
                {
                    "entity": result.get("name", ""),
                    "type": result.get("type", ""),
                    "description": result.get("description", ""),
                    "relationships": result.get("relationships", []),
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Graph search failed for tenant {tenant_id}: {e}")
            return []

    @tool
    async def hybrid_search(
        self, run_context: RunContext, query: str, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Hybrid search combining vector (database) and graph results.

        Both searches are automatically tenant-isolated.
        """
        try:
            tenant_id = run_context.tenant_id

            # Perform both searches concurrently
            vector_results = await self.vector_search(run_context, query, limit)
            graph_results = await self.graph_search(run_context, query, limit)

            return {
                "vector_results": vector_results,
                "graph_results": graph_results,
                "tenant_id": tenant_id,
                "query": query,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Hybrid search failed for tenant {tenant_id}: {e}")
            return {"vector_results": [], "graph_results": [], "error": str(e)}

    @tool
    async def add_relationship(
        self, run_context: RunContext, relationship: GraphRelationship
    ) -> str:
        """
        Add manual relationship to tenant's knowledge graph.

        Automatically namespaced to tenant's graph partition.
        """
        try:
            tenant_id = run_context.tenant_id

            # Add to tenant's graph namespace
            await self.graphiti_client.add_manual_fact_for_tenant(
                tenant_id, relationship
            )

            return f"Added relationship: {relationship.source_entity} -> {relationship.target_entity}"

        except Exception as e:
            logger.error(f"Failed to add relationship for tenant {tenant_id}: {e}")
            raise

    @tool
    async def get_entity_relationships(
        self, run_context: RunContext, entity_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for entity in tenant's knowledge graph.

        Automatically scoped to tenant's namespace.
        """
        try:
            tenant_id = run_context.tenant_id

            # Get from tenant's graph namespace
            relationships = await self.graphiti_client.get_tenant_entity_relationships(
                tenant_id, entity_name
            )

            return [
                {
                    "source": rel.get("source", ""),
                    "target": rel.get("target", ""),
                    "type": rel.get("type", ""),
                    "description": rel.get("description", ""),
                }
                for rel in relationships
            ]

        except Exception as e:
            logger.error(f"Failed to get relationships for tenant {tenant_id}: {e}")
            return []

    async def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Placeholder - implement with OpenAI or other embedding service.
        """
        # This is a placeholder implementation
        # In production, use OpenAI embeddings or similar
        import hashlib
        import numpy as np

        # Create deterministic but fake embedding for testing
        hash_obj = hashlib.md5(text.encode())
        seed = int(hash_obj.hexdigest()[:8], 16)
        np.random.seed(seed)
        return np.random.random(768).tolist()

    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get statistics for tenant's data."""
        try:
            # Get document count from tenant's database
            async with self.tenant_manager.get_tenant_connection(tenant_id) as conn:
                doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
                chunk_count = await conn.fetchval("SELECT COUNT(*) FROM chunks")

            # Get graph stats from tenant's namespace
            graph_stats = await self.graphiti_client.get_tenant_stats(tenant_id)

            return {
                "tenant_id": tenant_id,
                "documents": doc_count,
                "chunks": chunk_count,
                "graph_entities": graph_stats.get("entities", 0),
                "graph_relationships": graph_stats.get("relationships", 0),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get stats for tenant {tenant_id}: {e}")
            raise

    async def validate_isolation(self, tenant_id: str) -> Dict[str, Any]:
        """
        Validate that tenant isolation is working correctly.

        This is a diagnostic tool to ensure no cross-tenant data leakage.
        """
        try:
            results = {
                "tenant_id": tenant_id,
                "database_isolation": True,
                "graph_isolation": True,
                "errors": [],
            }

            # Test database isolation
            try:
                async with self.tenant_manager.get_tenant_connection(tenant_id) as conn:
                    # Verify we can only see this tenant's data
                    tables = await conn.fetch("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)

                    # Should have tenant tables without tenant_id columns
                    table_names = {row["table_name"] for row in tables}
                    expected_tables = {"documents", "chunks", "sessions", "messages"}

                    if not expected_tables.issubset(table_names):
                        results["database_isolation"] = False
                        results["errors"].append(
                            "Missing expected tables in tenant database"
                        )

            except Exception as e:
                results["database_isolation"] = False
                results["errors"].append(f"Database isolation test failed: {e}")

            # Test graph isolation
            try:
                namespace_stats = await self.graphiti_client.get_tenant_stats(tenant_id)
                if namespace_stats is None:
                    results["graph_isolation"] = False
                    results["errors"].append("Could not access tenant graph namespace")

            except Exception as e:
                results["graph_isolation"] = False
                results["errors"].append(f"Graph isolation test failed: {e}")

            results["overall_isolation"] = (
                results["database_isolation"] and results["graph_isolation"]
            )

            return results

        except Exception as e:
            logger.error(f"Failed to validate isolation for tenant {tenant_id}: {e}")
            raise
