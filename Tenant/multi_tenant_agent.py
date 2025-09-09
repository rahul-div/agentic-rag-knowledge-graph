"""
Multi-Tenant Pydantic AI Agent with Project-per-Tenant Architecture
Integrates with Neon PostgreSQL (project-per-tenant) and Graphiti (namespaced) for complete RAG capabilities.
Uses the same validated Pydantic AI agent structure as the single-tenant system.
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

# Add parent directory to path for agent imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import comprehensive system prompt for intelligent tool routing
from system_promt import SYSTEM_PROMPT

try:
    from pydantic_ai import Agent, RunContext

    # Import validated agent components from single-tenant system
    from agent.providers import get_llm_model
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

    PYDANTIC_AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Required dependencies not installed: {e}")
    print("Install with: pip install pydantic-ai")
    PYDANTIC_AI_AVAILABLE = False

    # Mock classes for development
    class Agent:
        def __init__(self, **kwargs):
            self.tools = []

        def tool(self, func):
            """Mock tool decorator"""
            self.tools.append(func)
            return func

        async def run_async(self, **kwargs):
            return type(
                "MockResult", (), {"data": "Mock response - Pydantic AI not available"}
            )()

    class RunContext:
        def __init__(self, **kwargs):
            self.deps = None

    def get_llm_model():
        return "gemini-2.0-flash-thinking-exp-1219"


from tenant_manager import TenantManager

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


@dataclass
class TenantAgentDependencies:
    """Dependencies for the multi-tenant RAG agent."""

    tenant_id: str
    session_id: str
    user_id: Optional[str] = None
    tenant_manager: Optional[Any] = None
    search_preferences: Dict[str, Any] = None

    def __post_init__(self):
        if self.search_preferences is None:
            self.search_preferences = {
                "use_vector": True,
                "use_graph": True,
                "default_limit": 10,
            }


class MultiTenantRAGAgent:
    """
    Multi-tenant Pydantic AI agent with complete tenant isolation.

    Uses the same validated agent structure as the single-tenant system,
    but with tenant-aware context and operations.
    """

    def __init__(
        self,
        tenant_manager: TenantManager,
        graphiti_client: Optional[Any] = None,
        model_name: str = "gemini-2.0-flash-thinking-exp-1219",
        system_prompt: str = None,
    ):
        self.tenant_manager = tenant_manager
        self.graphiti_client = graphiti_client
        self.model_name = model_name

        # Use the comprehensive system prompt for intelligent tool routing
        if system_prompt is None:
            system_prompt = SYSTEM_PROMPT
            logger.info(
                "Using comprehensive system prompt for intelligent tool routing"
            )

        # Initialize Pydantic AI agent with tenant-aware tools
        if PYDANTIC_AI_AVAILABLE:
            try:
                model = get_llm_model()
            except ImportError:
                model = model_name

            # Create the agent using the same pattern as single-tenant system
            self.agent = Agent(
                model, deps_type=TenantAgentDependencies, system_prompt=system_prompt
            )
            logger.info(f"Created multi-tenant agent with model: {model}")

            # Register tools using the same pattern as single-tenant system
            self._register_tools()
            logger.info("Successfully registered tenant-aware tools")
        else:
            # Fallback mock agent
            self.agent = Agent(model=model_name, system_prompt=system_prompt)
            logger.info(f"Created mock agent with model: {model_name}")

    def _register_tools(self):
        """Register tenant-aware versions of the validated tools."""

        # Check if we have the real Pydantic AI agent or mock
        if not PYDANTIC_AI_AVAILABLE or not hasattr(self.agent, "tool"):
            logger.warning("Agent does not support tool registration (using mock?)")
            return

        # Vector search tool
        @self.agent.tool
        async def tenant_vector_search(
            ctx: RunContext[TenantAgentDependencies], query: str, limit: int = 10
        ) -> List[Dict[str, Any]]:
            """
            Search for relevant information using semantic similarity.
            Automatically isolated to tenant's database.
            """
            try:
                tenant_id = ctx.deps.tenant_id
                logger.info(f"🔍 Vector search for tenant {tenant_id}: {query}")

                # Get tenant-specific database URL
                tenant_db_url = await self.tenant_manager.get_tenant_database_url(
                    tenant_id
                )

                # Use tenant-aware vector search from TenantDataIngestionService
                if hasattr(self.tenant_manager, "ingestion_service"):
                    results = await self.tenant_manager.ingestion_service.vector_search_for_tenant(
                        tenant_database_url=tenant_db_url, query=query, limit=limit
                    )
                else:
                    # Fallback to importing the service
                    from tenant_data_ingestion_service import TenantDataIngestionService

                    ingestion_service = TenantDataIngestionService(
                        tenant_manager=self.tenant_manager
                    )
                    results = await ingestion_service.vector_search_for_tenant(
                        tenant_database_url=tenant_db_url, query=query, limit=limit
                    )

                logger.info(
                    f"✅ Vector search returned {len(results)} results for tenant {tenant_id}"
                )

                # Results are already dictionaries from the ingestion service
                return [
                    {
                        "content": r.get("content", ""),
                        "score": r.get("similarity", 0),
                        "document_title": r.get("document_title", ""),
                        "document_source": r.get("document_source", ""),
                        "chunk_id": str(r.get("chunk_id", "")),
                        "metadata": r.get("metadata", {}),
                    }
                    for r in results
                ]
            except Exception as e:
                logger.error(
                    f"Vector search failed for tenant {ctx.deps.tenant_id}: {e}"
                )
                return []

        # Graph search tool
        @self.agent.tool
        async def tenant_graph_search(
            ctx: RunContext[TenantAgentDependencies], query: str
        ) -> List[Dict[str, Any]]:
            """
            Search the knowledge graph for facts and relationships.
            Automatically isolated to tenant's namespace.
            """
            try:
                tenant_id = ctx.deps.tenant_id
                logger.info(f"🔍 Graph search for tenant {tenant_id}: {query}")

                # Use tenant-aware graph search with proper namespace
                if self.tenant_manager.graphiti_client:
                    # Use the tenant-specific search method
                    results = (
                        await self.tenant_manager.graphiti_client.search_tenant_graph(
                            tenant_id=tenant_id, query=query, limit=10
                        )
                    )

                    logger.info(
                        f"✅ Graph search returned {len(results)} results for tenant {tenant_id}"
                    )

                    # Results are already formatted dictionaries from search_tenant_graph
                    return results
                else:
                    logger.warning(
                        f"No Graphiti client available for tenant {tenant_id}"
                    )
                    return []
            except Exception as e:
                logger.error(
                    f"Graph search failed for tenant {ctx.deps.tenant_id}: {e}"
                )
                return []

        # Hybrid search tool
        @self.agent.tool
        async def tenant_hybrid_search(
            ctx: RunContext[TenantAgentDependencies],
            query: str,
            limit: int = 10,
            text_weight: float = 0.3,
        ) -> List[Dict[str, Any]]:
            """
            Perform hybrid search combining vector and text search.
            Automatically isolated to tenant's database.
            """
            try:
                tenant_id = ctx.deps.tenant_id
                logger.info(f"🔍 Hybrid search for tenant {tenant_id}: {query}")

                # Get tenant-specific database URL
                tenant_db_url = await self.tenant_manager.get_tenant_database_url(
                    tenant_id
                )

                # Use tenant-aware hybrid search from TenantDataIngestionService
                if hasattr(self.tenant_manager, "ingestion_service"):
                    results = await self.tenant_manager.ingestion_service.hybrid_search_for_tenant(
                        tenant_database_url=tenant_db_url,
                        query=query,
                        limit=limit,
                        text_weight=text_weight,
                        vector_weight=1.0 - text_weight,
                    )
                else:
                    # Fallback to importing the service
                    from tenant_data_ingestion_service import TenantDataIngestionService

                    ingestion_service = TenantDataIngestionService(
                        tenant_manager=self.tenant_manager
                    )
                    results = await ingestion_service.hybrid_search_for_tenant(
                        tenant_database_url=tenant_db_url,
                        query=query,
                        limit=limit,
                        text_weight=text_weight,
                        vector_weight=1.0 - text_weight,
                    )

                logger.info(
                    f"✅ Hybrid search returned {len(results)} results for tenant {tenant_id}"
                )

                # Results are already dictionaries from the ingestion service
                return [
                    {
                        "content": r.get("content", ""),
                        "score": r.get("combined_score", 0),
                        "vector_similarity": r.get("vector_similarity", 0),
                        "text_similarity": r.get("text_similarity", 0),
                        "document_title": r.get("document_title", ""),
                        "document_source": r.get("document_source", ""),
                        "chunk_id": str(r.get("chunk_id", "")),
                        "metadata": r.get("metadata", {}),
                    }
                    for r in results
                ]
            except Exception as e:
                logger.error(
                    f"Hybrid search failed for tenant {ctx.deps.tenant_id}: {e}"
                )
                return []

        # Comprehensive search tool (combines all methods)
        @self.agent.tool
        async def tenant_comprehensive_search(
            ctx: RunContext[TenantAgentDependencies], query: str, limit: int = 10
        ) -> List[Dict[str, Any]]:
            """
            Comprehensive search using all available methods.
            Automatically isolated to tenant's resources.
            """
            try:
                tenant_id = ctx.deps.tenant_id
                logger.info(f"🔍 Comprehensive search for tenant {tenant_id}: {query}")

                # Perform all searches concurrently
                import asyncio

                vector_task = tenant_vector_search(ctx, query, limit)
                graph_task = tenant_graph_search(ctx, query)
                hybrid_task = tenant_hybrid_search(ctx, query, limit)

                vector_results, graph_results, hybrid_results = await asyncio.gather(
                    vector_task, graph_task, hybrid_task, return_exceptions=True
                )

                # Handle exceptions
                if isinstance(vector_results, Exception):
                    logger.warning(f"Vector search failed: {vector_results}")
                    vector_results = []
                if isinstance(graph_results, Exception):
                    logger.warning(f"Graph search failed: {graph_results}")
                    graph_results = []
                if isinstance(hybrid_results, Exception):
                    logger.warning(f"Hybrid search failed: {hybrid_results}")
                    hybrid_results = []

                # Combine and rank results
                all_results = []

                # Add hybrid results (highest priority due to combined scoring)
                for r in hybrid_results[: limit // 3]:
                    all_results.append(
                        {
                            "content": r["content"],
                            "score": r["score"],
                            "source": r["document_title"],
                            "type": "hybrid",
                            "metadata": r.get("metadata", {}),
                        }
                    )

                # Add vector results
                for r in vector_results[: limit // 3]:
                    all_results.append(
                        {
                            "content": r["content"],
                            "score": r["score"],
                            "source": r["document_title"],
                            "type": "vector",
                            "metadata": r.get("metadata", {}),
                        }
                    )

                # Add graph results
                for r in graph_results[: limit // 3]:
                    all_results.append(
                        {
                            "content": r["fact"],
                            "score": 1.0,
                            "source": "knowledge_graph",
                            "type": "graph",
                            "valid_at": r.get("valid_at"),
                        }
                    )

                logger.info(
                    f"✅ Comprehensive search returned {len(all_results)} combined results"
                )
                return all_results[:limit]

            except Exception as e:
                logger.error(
                    f"Comprehensive search failed for tenant {ctx.deps.tenant_id}: {e}"
                )
                return []

        # Default to local dual search tool as per system prompt
        @self.agent.tool
        async def local_dual_search(
            ctx: RunContext[TenantAgentDependencies], query: str, limit: int = 10
        ) -> List[Dict[str, Any]]:
            """
            Default LOCAL PATH: DUAL STORAGE search combining vector and graph.
            This is the primary tool as specified in the system prompt.
            Uses tenant-aware search methods for proper isolation.
            """
            try:
                tenant_id = ctx.deps.tenant_id
                logger.info(f"🔍 Local dual search for tenant {tenant_id}: {query}")

                # Perform tenant-aware vector search
                vector_results = await tenant_vector_search(ctx, query, limit)

                # Perform tenant-aware graph search
                graph_results = await tenant_graph_search(ctx, query)

                # Combine results
                combined = []

                # Add vector results
                for r in vector_results:
                    combined.append(
                        {
                            "content": r["content"],
                            "score": r["score"],
                            "source": r["document_title"],
                            "type": "vector",
                            "chunk_id": r.get("chunk_id"),
                        }
                    )

                # Add graph results (balance the results)
                for r in graph_results[: limit // 2]:
                    combined.append(
                        {
                            "content": r["fact"],
                            "score": 1.0,  # Graph facts get default high score
                            "source": r.get("source_node_uuid", "knowledge_graph"),
                            "type": "graph",
                            "valid_at": r.get("valid_at"),
                        }
                    )

                logger.info(
                    f"✅ Local dual search returned {len(combined)} combined results"
                )
                return combined[:limit]

            except Exception as e:
                logger.error(
                    f"Local dual search failed for tenant {ctx.deps.tenant_id}: {e}"
                )
                return []

    async def chat(
        self,
        message: str,
        context: TenantContext,
    ) -> Dict[str, Any]:
        """
        Process a chat message with tenant-aware context.
        Returns clean response with tool usage and source information.
        """
        try:
            # Log start of chat processing
            logger.info(f"🧠 Starting chat processing for tenant {context.tenant_id}")
            logger.info(
                f"📝 User query: {message[:100]}{'...' if len(message) > 100 else ''}"
            )

            # Create dependencies for the agent
            deps = TenantAgentDependencies(
                tenant_id=context.tenant_id,
                session_id=context.session_id or "default",
                user_id=context.user_id,
                tenant_manager=self.tenant_manager,
            )

            # Track tools used for response
            tools_used = []
            sources_found = []

            # Execute query with agent
            logger.info(f"🤖 Running agent with model {self.model_name}")
            result = await self.agent.run(message, deps=deps)
            logger.info(f"✅ Agent completed processing for tenant {context.tenant_id}")

            # Extract response content - handle Pydantic AI result properly
            if hasattr(result, "data"):
                response_text = str(result.data)
            else:
                response_text = str(result)

            # Extract tool usage information if available
            if hasattr(result, "all_messages"):
                logger.debug("🔍 Extracting tool usage from agent messages")
                for msg in result.all_messages():
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        logger.debug(
                            f"Found {len(msg.tool_calls)} tool calls in message"
                        )
                        for tool_call in msg.tool_calls:
                            if hasattr(tool_call, "function"):
                                tool_name = tool_call.function.name
                            else:
                                tool_name = getattr(tool_call, "name", "Unknown")

                            logger.debug(f"Processing tool call: {tool_name}")

                            # Map tool names to user-friendly descriptions
                            if "tenant_vector_search" in tool_name:
                                tools_used.append("Vector Search")
                                logger.info("🔧 Used Vector Search tool")
                            elif "tenant_graph_search" in tool_name:
                                tools_used.append("Knowledge Graph Search")
                                logger.info("🔧 Used Knowledge Graph Search tool")
                            elif "tenant_hybrid_search" in tool_name:
                                tools_used.append("Hybrid Search")
                                logger.info("🔧 Used Hybrid Search tool")
                            elif "tenant_comprehensive_search" in tool_name:
                                tools_used.append("Comprehensive Search")
                                logger.info("🔧 Used Comprehensive Search tool")
                            elif "tenant_local_dual_search" in tool_name:
                                tools_used.append("Dual Storage Search")
                                logger.info("🔧 Used Dual Storage Search tool")
                            elif "vector" in tool_name.lower():
                                tools_used.append("Vector Search")
                                logger.info("🔧 Used Vector Search tool")
                            elif "graph" in tool_name.lower():
                                tools_used.append("Knowledge Graph Search")
                                logger.info("🔧 Used Knowledge Graph Search tool")
                            elif "hybrid" in tool_name.lower():
                                tools_used.append("Hybrid Search")
                                logger.info("🔧 Used Hybrid Search tool")
                            elif "dual" in tool_name.lower():
                                tools_used.append("Dual Storage Search")
                                logger.info("🔧 Used Dual Storage Search tool")
                            else:
                                tools_used.append(f"Tool: {tool_name}")
                                logger.info(f"🔧 Used tool: {tool_name}")

                    # Also check for tool results to extract sources
                    if hasattr(msg, "tool_result") and msg.tool_result:
                        # Extract source information from tool results
                        tool_result = msg.tool_result
                        if isinstance(tool_result, list):
                            for item in tool_result[:3]:  # Top 3 sources
                                if isinstance(item, dict):
                                    source_info = {
                                        "source": item.get(
                                            "source",
                                            item.get("document_title", "Unknown"),
                                        ),
                                        "score": item.get("score", 0),
                                        "type": item.get("type", "unknown"),
                                    }
                                    sources_found.append(source_info)

                logger.info(
                    f"📊 Extracted {len(tools_used)} tools and {len(sources_found)} sources"
                )
            else:
                logger.debug("No tool usage information available in agent result")

            # Remove duplicates and ensure we have something
            tools_used = (
                list(set(tools_used)) if tools_used else ["Dual Storage Search"]
            )

            return {
                "response": response_text,
                "tenant_id": context.tenant_id,
                "timestamp": datetime.now().isoformat(),
                "tools_used": tools_used,
                "sources": sources_found,
                "metadata": {
                    "model": self.model_name,
                    "session_id": context.session_id,
                    "execution_mode": "tenant_isolated",
                },
                "agent_result": result,  # Include full result for CLI processing
            }

        except Exception as e:
            logger.error(f"Chat failed for tenant {context.tenant_id}: {e}")
            return {
                "response": f"I'm sorry, I encountered an error while processing your request: {str(e)}",
                "tenant_id": context.tenant_id,
                "timestamp": datetime.now().isoformat(),
                "tools_used": [],
                "sources": [],
                "metadata": {
                    "error": str(e),
                    "model": self.model_name,
                    "session_id": context.session_id,
                },
            }
