"""
Multi-Tenant Pydantic AI Agent with Tenant-Aware Tools
Integrates with both Neon PostgreSQL and Graphiti for complete RAG capabilities.
"""

import asyncio
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


from .tenant_manager import TenantManager, Document, Chunk
from .multi_tenant_graphiti import TenantGraphitiClient, GraphEpisode, GraphRelationship

logger = logging.getLogger(__name__)


@dataclass
class TenantContext:
    """Context information for tenant operations."""

    tenant_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    permissions: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ["read", "write"]
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RAGResult:
    """Result from RAG operations."""

    query: str
    tenant_id: str
    vector_results: List[Dict[str, Any]]
    graph_results: List[Dict[str, Any]]
    combined_context: str
    confidence_score: float
    sources: List[str]
    timestamp: datetime

    def __post_init__(self):
        if not hasattr(self, "timestamp") or self.timestamp is None:
            self.timestamp = datetime.now()


class MultiTenantRAGAgent:
    """
    Multi-tenant RAG agent with complete data isolation.

    Combines vector search (Neon PostgreSQL + pgvector) with
    knowledge graph capabilities (Neo4j + Graphiti) while ensuring
    complete tenant isolation.
    """

    def __init__(
        self,
        tenant_manager: TenantManager,
        graphiti_client: TenantGraphitiClient,
        model_name: str = "gpt-4",
        system_prompt: Optional[str] = None,
    ):
        """Initialize multi-tenant RAG agent."""
        self.tenant_manager = tenant_manager
        self.graphiti_client = graphiti_client
        self.model_name = model_name

        # Default system prompt with tenant awareness
        self.system_prompt = (
            system_prompt
            or """
        You are an intelligent RAG assistant with access to tenant-specific documents and knowledge graphs.
        
        IMPORTANT: You can only access data that belongs to the current tenant. All operations are 
        automatically filtered by tenant_id to ensure complete data isolation.
        
        Use the available tools to:
        1. Search vector embeddings for relevant document chunks
        2. Query the knowledge graph for entity relationships
        3. Combine information from both sources for comprehensive answers
        4. Ingest new documents when requested
        
        Always cite your sources and indicate which tenant context you're operating in.
        """
        )

        # Initialize Pydantic AI agent with tenant-aware tools
        self.agent = Agent(
            model=model_name,
            system_prompt=self.system_prompt,
            tools=[
                self._vector_search_tool,
                self._graph_search_tool,
                self._hybrid_search_tool,
                self._ingest_document_tool,
                self._get_entity_relationships_tool,
                self._add_manual_relationship_tool,
                self._get_tenant_stats_tool,
            ],
        )

    async def initialize(self) -> None:
        """Initialize all components."""
        if not self.tenant_manager.pool:
            await self.tenant_manager.initialize()

        if not self.graphiti_client._initialized:
            await self.graphiti_client.initialize()

        logger.info("MultiTenantRAGAgent initialized successfully")

    async def close(self) -> None:
        """Close all connections."""
        await self.tenant_manager.close()
        await self.graphiti_client.close()

    # Core RAG Methods

    async def query(
        self,
        query: str,
        tenant_context: TenantContext,
        use_vector: bool = True,
        use_graph: bool = True,
        max_results: int = 10,
    ) -> str:
        """
        Process a query with tenant isolation.

        Args:
            query: User query
            tenant_context: Tenant context information
            use_vector: Whether to use vector search
            use_graph: Whether to use graph search
            max_results: Maximum results to return

        Returns:
            Agent response
        """
        try:
            # Run the agent with tenant context
            result = await self.agent.run_async(
                query,
                context={
                    "tenant_context": tenant_context,
                    "use_vector": use_vector,
                    "use_graph": use_graph,
                    "max_results": max_results,
                },
            )

            return result.data if hasattr(result, "data") else str(result)

        except Exception as e:
            logger.error(
                f"Failed to process query for tenant {tenant_context.tenant_id}: {e}"
            )
            return f"I apologize, but I encountered an error processing your query: {str(e)}"

    async def ingest_document(
        self,
        document: Document,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        add_to_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest a document into both vector store and knowledge graph.

        Args:
            document: Document to ingest
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            add_to_graph: Whether to add to knowledge graph

        Returns:
            Ingestion results
        """
        try:
            # Create document in database
            doc_id = await self.tenant_manager.create_document(document)

            # Create chunks (simplified chunking - replace with proper chunker)
            chunks = []
            content = document.content

            for i in range(0, len(content), chunk_size - chunk_overlap):
                chunk_content = content[i : i + chunk_size]
                if chunk_content.strip():
                    chunk = Chunk(
                        tenant_id=document.tenant_id,
                        document_id=doc_id,
                        content=chunk_content,
                        chunk_index=len(chunks),
                        token_count=len(chunk_content.split()),
                        metadata={"source": document.source, "title": document.title},
                    )
                    chunks.append(chunk)

            # Store chunks (embeddings would be generated here)
            chunk_ids = await self.tenant_manager.create_chunks(chunks)

            results = {
                "document_id": doc_id,
                "chunk_count": len(chunk_ids),
                "tenant_id": document.tenant_id,
                "graph_added": False,
            }

            # Add to knowledge graph
            if add_to_graph:
                episode = GraphEpisode(
                    tenant_id=document.tenant_id,
                    name=f"Document: {document.title}",
                    content=document.content,
                    source_description=f"Document from {document.source}",
                )

                graph_success = await self.graphiti_client.add_episode_for_tenant(
                    episode
                )
                results["graph_added"] = graph_success

            logger.info(f"Ingested document {doc_id} for tenant {document.tenant_id}")
            return results

        except Exception as e:
            logger.error(
                f"Failed to ingest document for tenant {document.tenant_id}: {e}"
            )
            raise

    # Pydantic AI Tools (Tenant-Aware)

    @tool
    async def _vector_search_tool(
        self, ctx: RunContext, query: str, limit: int = 10, threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search vector embeddings within tenant context.

        Args:
            query: Search query
            limit: Maximum results
            threshold: Similarity threshold

        Returns:
            List of relevant chunks
        """
        tenant_context = ctx.get("tenant_context")
        if not tenant_context:
            return []

        try:
            # Mock embedding generation (replace with actual embedding model)
            query_embedding = [0.1] * 768  # Placeholder

            results = await self.tenant_manager.vector_search(
                tenant_id=tenant_context.tenant_id,
                query_embedding=query_embedding,
                limit=limit,
                threshold=threshold,
            )

            return results

        except Exception as e:
            logger.error(
                f"Vector search failed for tenant {tenant_context.tenant_id}: {e}"
            )
            return []

    @tool
    async def _graph_search_tool(
        self, ctx: RunContext, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge graph within tenant context.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of relevant graph entities
        """
        tenant_context = ctx.get("tenant_context")
        if not tenant_context:
            return []

        try:
            results = await self.graphiti_client.search_tenant_graph(
                tenant_id=tenant_context.tenant_id, query=query, limit=limit
            )

            return results

        except Exception as e:
            logger.error(
                f"Graph search failed for tenant {tenant_context.tenant_id}: {e}"
            )
            return []

    @tool
    async def _hybrid_search_tool(
        self,
        ctx: RunContext,
        query: str,
        vector_limit: int = 5,
        graph_limit: int = 5,
        threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining vector and graph results.

        Args:
            query: Search query
            vector_limit: Max vector results
            graph_limit: Max graph results
            threshold: Similarity threshold

        Returns:
            Combined search results
        """
        tenant_context = ctx.get("tenant_context")
        if not tenant_context:
            return {"vector_results": [], "graph_results": [], "combined_context": ""}

        try:
            # Get vector results
            vector_results = await self._vector_search_tool(
                ctx, query, vector_limit, threshold
            )

            # Get graph results
            graph_results = await self._graph_search_tool(ctx, query, graph_limit)

            # Combine contexts
            vector_context = " ".join([r.get("content", "") for r in vector_results])
            graph_context = " ".join([str(r.get("result", "")) for r in graph_results])

            combined_context = (
                f"Vector Context: {vector_context}\n\nGraph Context: {graph_context}"
            )

            return {
                "vector_results": vector_results,
                "graph_results": graph_results,
                "combined_context": combined_context,
                "tenant_id": tenant_context.tenant_id,
            }

        except Exception as e:
            logger.error(
                f"Hybrid search failed for tenant {tenant_context.tenant_id}: {e}"
            )
            return {"vector_results": [], "graph_results": [], "combined_context": ""}

    @tool
    async def _ingest_document_tool(
        self,
        ctx: RunContext,
        title: str,
        content: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest a new document into the tenant's knowledge base.

        Args:
            title: Document title
            content: Document content
            source: Document source
            metadata: Additional metadata

        Returns:
            Ingestion results
        """
        tenant_context = ctx.get("tenant_context")
        if not tenant_context:
            return {"error": "No tenant context provided"}

        try:
            document = Document(
                tenant_id=tenant_context.tenant_id,
                title=title,
                source=source,
                content=content,
                metadata=metadata or {},
            )

            results = await self.ingest_document(document)
            return results

        except Exception as e:
            logger.error(
                f"Document ingestion failed for tenant {tenant_context.tenant_id}: {e}"
            )
            return {"error": str(e)}

    @tool
    async def _get_entity_relationships_tool(
        self, ctx: RunContext, entity_name: str, depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get relationships for an entity within tenant context.

        Args:
            entity_name: Name of entity
            depth: Relationship depth

        Returns:
            Entity relationships
        """
        tenant_context = ctx.get("tenant_context")
        if not tenant_context:
            return {}

        try:
            relationships = await self.graphiti_client.get_tenant_entity_relationships(
                tenant_id=tenant_context.tenant_id, entity_name=entity_name, depth=depth
            )

            return relationships

        except Exception as e:
            logger.error(
                f"Failed to get relationships for tenant {tenant_context.tenant_id}: {e}"
            )
            return {"error": str(e)}

    @tool
    async def _add_manual_relationship_tool(
        self,
        ctx: RunContext,
        source_entity: str,
        target_entity: str,
        relationship_type: str,
        description: str,
    ) -> bool:
        """
        Manually add a relationship to the knowledge graph.

        Args:
            source_entity: Source entity name
            target_entity: Target entity name
            relationship_type: Type of relationship
            description: Description of relationship

        Returns:
            Success status
        """
        tenant_context = ctx.get("tenant_context")
        if not tenant_context:
            return False

        try:
            relationship = GraphRelationship(
                tenant_id=tenant_context.tenant_id,
                source_entity=source_entity,
                target_entity=target_entity,
                relationship_type=relationship_type,
                description=description,
            )

            success = await self.graphiti_client.add_manual_fact_for_tenant(
                relationship
            )
            return success

        except Exception as e:
            logger.error(
                f"Failed to add relationship for tenant {tenant_context.tenant_id}: {e}"
            )
            return False

    @tool
    async def _get_tenant_stats_tool(self, ctx: RunContext) -> Dict[str, Any]:
        """
        Get comprehensive tenant statistics.

        Returns:
            Tenant statistics
        """
        tenant_context = ctx.get("tenant_context")
        if not tenant_context:
            return {}

        try:
            # Get database stats
            db_stats = await self.tenant_manager.get_tenant_stats(
                tenant_context.tenant_id
            )

            # Get graph stats
            graph_stats = await self.graphiti_client.get_tenant_graph_stats(
                tenant_context.tenant_id
            )

            combined_stats = {
                "tenant_id": tenant_context.tenant_id,
                "database": db_stats,
                "graph": graph_stats,
                "timestamp": datetime.now().isoformat(),
            }

            return combined_stats

        except Exception as e:
            logger.error(
                f"Failed to get stats for tenant {tenant_context.tenant_id}: {e}"
            )
            return {"error": str(e)}

    # Convenience Methods

    async def quick_search(
        self, tenant_id: str, query: str, search_type: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Quick search interface for tenant.

        Args:
            tenant_id: Tenant identifier
            query: Search query
            search_type: Type of search ("vector", "graph", "hybrid")

        Returns:
            Search results
        """
        tenant_context = TenantContext(tenant_id=tenant_id)

        if search_type == "vector":
            return await self._vector_search_tool(
                RunContext(tenant_context=tenant_context), query
            )
        elif search_type == "graph":
            return await self._graph_search_tool(
                RunContext(tenant_context=tenant_context), query
            )
        else:  # hybrid
            return await self._hybrid_search_tool(
                RunContext(tenant_context=tenant_context), query
            )

    async def validate_tenant_isolation(self, tenant_id: str) -> Dict[str, Any]:
        """
        Validate tenant isolation across both stores.

        Args:
            tenant_id: Tenant to validate

        Returns:
            Validation results
        """
        try:
            # Validate database isolation
            db_stats = await self.tenant_manager.get_tenant_stats(tenant_id)

            # Validate graph isolation
            graph_validation = await self.graphiti_client.validate_tenant_isolation(
                tenant_id
            )

            return {
                "tenant_id": tenant_id,
                "database_isolation": {
                    "valid": bool(db_stats.get("tenant_id") == tenant_id),
                    "stats": db_stats,
                },
                "graph_isolation": graph_validation,
                "overall_status": "PASS"
                if db_stats and graph_validation.get("isolation_valid")
                else "FAIL",
                "validation_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to validate isolation for tenant {tenant_id}: {e}")
            return {"tenant_id": tenant_id, "overall_status": "ERROR", "error": str(e)}


# Example usage and testing
async def example_usage():
    """Example usage of MultiTenantRAGAgent."""
    # Initialize components (mock connections for example)
    tenant_manager = TenantManager("postgresql://user:pass@localhost/db")
    graphiti_client = TenantGraphitiClient(
        "neo4j://localhost:7687", "neo4j", "password"
    )

    # Initialize agent
    agent = MultiTenantRAGAgent(tenant_manager, graphiti_client)
    await agent.initialize()

    try:
        # Create tenant context
        tenant_context = TenantContext(
            tenant_id="demo_corp",
            user_id="user_123",
            permissions=["read", "write", "admin"],
        )

        # Query the agent
        response = await agent.query(
            query="What are the main project requirements?",
            tenant_context=tenant_context,
        )
        print(f"Agent response: {response}")

        # Ingest a document
        document = Document(
            tenant_id="demo_corp",
            title="API Documentation",
            source="docs/api.md",
            content="The API provides endpoints for document management and search...",
        )

        ingest_results = await agent.ingest_document(document)
        print(f"Ingestion results: {ingest_results}")

        # Validate isolation
        validation = await agent.validate_tenant_isolation("demo_corp")
        print(f"Isolation validation: {validation}")

    finally:
        await agent.close()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
