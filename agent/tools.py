"""
Tools for the Pydantic AI agent.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .db_utils import (
    vector_search,
    hybrid_search,
    get_document,
    list_documents,
    get_document_chunks,
)# Your dual entity extraction strategy
# 1. Regex extraction (structured data)
entities = {
    "clients": ["TechCorp Inc"],
    "projects": ["MOBILE-APP-123"], 
    "team_members": ["John Smith"],
    "technologies": ["React Native", "PostgreSQL"]
}

# 2. Flattened for Graphiti context
flattened_metadata = {
    "entities_clients": "TechCorp Inc",
    "entities_projects": "MOBILE-APP-123",
    "entities_team_members": "John Smith",
    "entities_technologies": "React Native, PostgreSQL"
}

# 3. Graphiti's LLM enhancement
# Creates rich semantic understanding:
# - John Smith WORKS_ON MOBILE-APP-123 (relationship)
# - MOBILE-APP-123 HAS_CLIENT TechCorp Inc (business relationship)
# - MOBILE-APP-123 USES_TECHNOLOGY React Native (technical relationship)
# - All with temporal validity and confidence scores
from .graph_utils import search_knowledge_graph, get_entity_relationships, graph_client
from .models import ChunkResult, GraphSearchResult, DocumentMetadata

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using Gemini via Graphiti.

    Args:
        text: Text to embed

    Returns:
        Embedding vector
    """
    try:
        # Import here to avoid circular import issues
        from ingestion.embedder import gemini_embedder

        # Use Graphiti's GeminiEmbedder directly
        embedding = await gemini_embedder.create(text)
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


# Tool Input Models
class VectorSearchInput(BaseModel):
    """Input for vector search tool."""

    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")


class GraphSearchInput(BaseModel):
    """Input for graph search tool."""

    query: str = Field(..., description="Search query")


class HybridSearchInput(BaseModel):
    """Input for hybrid search tool."""

    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")
    text_weight: float = Field(
        default=0.3, description="Weight for text similarity (0-1)"
    )


class DocumentInput(BaseModel):
    """Input for document retrieval."""

    document_id: str = Field(..., description="Document ID to retrieve")


class DocumentListInput(BaseModel):
    """Input for listing documents."""

    limit: int = Field(default=20, description="Maximum number of documents")
    offset: int = Field(default=0, description="Number of documents to skip")


class EntityRelationshipInput(BaseModel):
    """Input for entity relationship query."""

    entity_name: str = Field(..., description="Name of the entity")
    depth: int = Field(default=2, description="Maximum traversal depth")


class EntityTimelineInput(BaseModel):
    """Input for entity timeline query."""

    entity_name: str = Field(..., description="Name of the entity")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")


class OnyxSearchInput(BaseModel):
    """Input for Onyx search tool."""

    query: str = Field(..., description="Search query")
    num_results: int = Field(default=5, description="Number of results to return (1-10)")
    search_type: str = Field(default="hybrid", description="Type of search: 'hybrid', 'semantic', or 'keyword'")


class OnyxAnswerInput(BaseModel):
    """Input for Onyx answer with quote tool."""

    query: str = Field(..., description="Question to answer")
    num_docs: int = Field(default=5, description="Number of documents to use for answering")
    include_quotes: bool = Field(default=True, description="Whether to include supporting quotes")
    search_type: str = Field(default="hybrid", description="Type of search: 'hybrid', 'semantic', or 'keyword'")

class ComprehensiveSearchInput(BaseModel):
    """Input for comprehensive search combining multiple systems."""

    query: str = Field(..., description="Search query")
    num_results: int = Field(default=5, description="Number of results per search type")
    include_onyx: bool = Field(default=True, description="Include Onyx cloud search")
    include_vector: bool = Field(default=True, description="Include vector search") 
    include_graph: bool = Field(default=True, description="Include knowledge graph search")
    search_type: str = Field(default="hybrid", description="Search type for compatible systems")


# Tool Implementation Functions
async def vector_search_tool(input_data: VectorSearchInput) -> List[ChunkResult]:
    """
    Perform vector similarity search.

    Args:
        input_data: Search parameters

    Returns:
        List of matching chunks
    """
    try:
        # Generate embedding for the query
        embedding = await generate_embedding(input_data.query)

        # Perform vector search
        results = await vector_search(embedding=embedding, limit=input_data.limit)

        # Convert to ChunkResult models
        return [
            ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["similarity"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"],
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []


async def graph_search_tool(input_data: GraphSearchInput) -> List[GraphSearchResult]:
    """
    Search the knowledge graph.

    Args:
        input_data: Search parameters

    Returns:
        List of graph search results
    """
    try:
        results = await search_knowledge_graph(query=input_data.query)

        # Convert to GraphSearchResult models
        return [
            GraphSearchResult(
                fact=r["fact"],
                uuid=r["uuid"],
                valid_at=r.get("valid_at"),
                invalid_at=r.get("invalid_at"),
                source_node_uuid=r.get("source_node_uuid"),
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        return []


async def hybrid_search_tool(input_data: HybridSearchInput) -> List[ChunkResult]:
    """
    Perform hybrid search (vector + keyword).

    Args:
        input_data: Search parameters

    Returns:
        List of matching chunks
    """
    try:
        # Generate embedding for the query
        embedding = await generate_embedding(input_data.query)

        # Perform hybrid search
        results = await hybrid_search(
            embedding=embedding,
            query_text=input_data.query,
            limit=input_data.limit,
            text_weight=input_data.text_weight,
        )

        # Convert to ChunkResult models
        return [
            ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["combined_score"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"],
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        return []


async def get_document_tool(input_data: DocumentInput) -> Optional[Dict[str, Any]]:
    """
    Retrieve a complete document.

    Args:
        input_data: Document retrieval parameters

    Returns:
        Document data or None
    """
    try:
        document = await get_document(input_data.document_id)

        if document:
            # Also get all chunks for the document
            chunks = await get_document_chunks(input_data.document_id)
            document["chunks"] = chunks

        return document

    except Exception as e:
        logger.error(f"Document retrieval failed: {e}")
        return None


async def list_documents_tool(input_data: DocumentListInput) -> List[DocumentMetadata]:
    """
    List available documents.

    Args:
        input_data: Listing parameters

    Returns:
        List of document metadata
    """
    try:
        documents = await list_documents(
            limit=input_data.limit, offset=input_data.offset
        )

        # Convert to DocumentMetadata models
        return [
            DocumentMetadata(
                id=d["id"],
                title=d["title"],
                source=d["source"],
                metadata=d["metadata"],
                created_at=datetime.fromisoformat(d["created_at"]),
                updated_at=datetime.fromisoformat(d["updated_at"]),
                chunk_count=d.get("chunk_count"),
            )
            for d in documents
        ]

    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        return []


async def get_entity_relationships_tool(
    input_data: EntityRelationshipInput,
) -> Dict[str, Any]:
    """
    Get relationships for an entity.

    Args:
        input_data: Entity relationship parameters

    Returns:
        Entity relationships
    """
    try:
        return await get_entity_relationships(
            entity=input_data.entity_name, depth=input_data.depth
        )

    except Exception as e:
        logger.error(f"Entity relationship query failed: {e}")
        return {
            "central_entity": input_data.entity_name,
            "related_entities": [],
            "relationships": [],
            "depth": input_data.depth,
            "error": str(e),
        }


async def get_entity_timeline_tool(
    input_data: EntityTimelineInput,
) -> List[Dict[str, Any]]:
    """
    Get timeline of facts for an entity.

    Args:
        input_data: Timeline query parameters

    Returns:
        Timeline of facts
    """
    try:
        # Parse dates if provided
        start_date = None
        end_date = None

        if input_data.start_date:
            start_date = datetime.fromisoformat(input_data.start_date)
        if input_data.end_date:
            end_date = datetime.fromisoformat(input_data.end_date)
        # Get timeline from graph
        timeline = await graph_client.get_entity_timeline(
            entity_name=input_data.entity_name, start_date=start_date, end_date=end_date
        )

        return timeline

    except Exception as e:
        logger.error(f"Entity timeline query failed: {e}")
        return []


# Combined search function for agent use
async def perform_comprehensive_search(
    query: str, use_vector: bool = True, use_graph: bool = True, limit: int = 10
) -> Dict[str, Any]:
    """
    Perform a comprehensive search using multiple methods.

    Args:
        query: Search query
        use_vector: Whether to use vector search
        use_graph: Whether to use graph search
        limit: Maximum results per search type (only applies to vector search)

    Returns:
        Combined search results
    """
    results = {
        "query": query,
        "vector_results": [],
        "graph_results": [],
        "total_results": 0,
    }

    tasks = []

    if use_vector:
        tasks.append(vector_search_tool(VectorSearchInput(query=query, limit=limit)))

    if use_graph:
        tasks.append(graph_search_tool(GraphSearchInput(query=query)))

    if tasks:
        search_results = await asyncio.gather(*tasks, return_exceptions=True)

        if use_vector and not isinstance(search_results[0], Exception):
            results["vector_results"] = search_results[0]

        if use_graph:
            graph_idx = 1 if use_vector else 0
            if not isinstance(search_results[graph_idx], Exception):
                results["graph_results"] = search_results[graph_idx]

    results["total_results"] = len(results["vector_results"]) + len(
        results["graph_results"]
    )

    return results


# Onyx Cloud Integration Tools
async def onyx_search_tool(input_data: OnyxSearchInput) -> Dict[str, Any]:
    """
    Search documents using Onyx Cloud's enterprise search capabilities.

    Args:
        input_data: Search parameters

    Returns:
        Dictionary containing search results with documents and metadata
    """
    try:
        # Import here to avoid circular import issues
        from onyx.service import OnyxService
        
        # Initialize Onyx service
        onyx_service = OnyxService()
        
        # Perform search using Onyx
        search_results = await asyncio.to_thread(
            onyx_service.search_documents,
            query=input_data.query,
            num_results=input_data.num_results,
            search_type=input_data.search_type
        )
        
        logger.debug(f"Onyx search returned {search_results.get('total_results', 0)} results for query: {input_data.query[:50]}...")
        
        return {
            "search_type": "onyx_search",
            "query": input_data.query,
            "results": search_results,
            "total_found": search_results.get('total_results', 0),
            "search_parameters": {
                "num_results": input_data.num_results,
                "search_type": input_data.search_type
            }
        }
    
    except Exception as e:
        logger.error(f"Onyx search failed: {e}")
        return {
            "search_type": "onyx_search",
            "query": input_data.query,
            "results": {"top_documents": [], "total_results": 0},
            "total_found": 0,
            "error": str(e)
        }


async def onyx_answer_with_quote_tool(input_data: OnyxAnswerInput) -> Dict[str, Any]:
    """
    Get answers with supporting quotes using Onyx Cloud's QA capabilities.

    Args:
        input_data: Question and answering parameters

    Returns:
        Dictionary containing answer, quotes, and source documents
    """
    try:
        # Import here to avoid circular import issues
        from onyx.service import OnyxService
        
        # Initialize Onyx service
        onyx_service = OnyxService()
        
        # Get answer with quotes using Onyx
        answer_response = await asyncio.to_thread(
            onyx_service.answer_with_quote,
            query=input_data.query,
            num_docs=input_data.num_docs,
            include_quotes=input_data.include_quotes,
            search_type=input_data.search_type
        )
        
        logger.debug(f"Onyx answered query: {input_data.query[:50]}... with {len(answer_response.get('quotes', []))} quotes")
        
        return {
            "search_type": "onyx_answer",
            "query": input_data.query,
            "answer": answer_response.get('answer', ''),
            "answer_citationless": answer_response.get('answer_citationless', ''),
            "quotes": answer_response.get('quotes', []),
            "top_documents": answer_response.get('top_documents', []),
            "contexts": answer_response.get('contexts', {}),
            "search_parameters": {
                "num_docs": input_data.num_docs,
                "include_quotes": input_data.include_quotes,
                "search_type": input_data.search_type
            }
        }
    
    except Exception as e:
        logger.error(f"Onyx answer with quote failed: {e}")
        return {
            "search_type": "onyx_answer",
            "query": input_data.query,
            "answer": f"Error: Unable to answer question due to {str(e)}",
            "answer_citationless": f"Error: Unable to answer question due to {str(e)}",
            "quotes": [],
            "top_documents": [],
            "contexts": {},
            "error": str(e)
        }


async def comprehensive_search_tool(input_data: ComprehensiveSearchInput) -> Dict[str, Any]:
    """
    Perform comprehensive search combining Onyx, vector, and knowledge graph systems.

    Args:
        input_data: Comprehensive search parameters

    Returns:
        Dictionary containing unified results from multiple search systems
    """
    try:
        results = {
            "search_type": "comprehensive_search",
            "query": input_data.query,
            "onyx_results": {},
            "vector_results": [],
            "graph_results": [],
            "combined_summary": "",
            "total_sources": 0
        }
        
        # Collect search tasks
        search_tasks = []
        
        # Add Onyx search if requested
        if input_data.include_onyx:
            onyx_input = OnyxSearchInput(
                query=input_data.query,
                num_results=input_data.num_results,
                search_type=input_data.search_type
            )
            search_tasks.append(("onyx", onyx_search_tool(onyx_input)))
        
        # Add vector search if requested
        if input_data.include_vector:
            vector_input = VectorSearchInput(
                query=input_data.query,
                limit=input_data.num_results
            )
            search_tasks.append(("vector", vector_search_tool(vector_input)))
        
        # Add graph search if requested
        if input_data.include_graph:
            graph_input = GraphSearchInput(query=input_data.query)
            search_tasks.append(("graph", graph_search_tool(graph_input)))
        
        # Execute all searches concurrently
        if search_tasks:
            search_results = await asyncio.gather(*[task[1] for task in search_tasks], return_exceptions=True)
            
            # Process results
            for i, (search_type, _) in enumerate(search_tasks):
                if not isinstance(search_results[i], Exception):
                    if search_type == "onyx":
                        results["onyx_results"] = search_results[i]
                        results["total_sources"] += search_results[i].get("total_found", 0)
                    elif search_type == "vector":
                        results["vector_results"] = search_results[i]
                        results["total_sources"] += len(search_results[i])
                    elif search_type == "graph":
                        results["graph_results"] = search_results[i]
                        results["total_sources"] += len(search_results[i])
        
        # Create combined summary
        summary_parts = []
        if results["onyx_results"] and results["onyx_results"].get("total_found", 0) > 0:
            summary_parts.append(f"Onyx: {results['onyx_results'].get('total_found', 0)} documents")
        if results["vector_results"]:
            summary_parts.append(f"Vector: {len(results['vector_results'])} chunks")
        if results["graph_results"]:
            summary_parts.append(f"Knowledge Graph: {len(results['graph_results'])} facts")
        
        results["combined_summary"] = f"Found information across {len(summary_parts)} systems: {', '.join(summary_parts)}"
        
        logger.debug(f"Comprehensive search completed for query: {input_data.query[:50]}... - {results['combined_summary']}")
        
        return results
    
    except Exception as e:
        logger.error(f"Comprehensive search failed: {e}")
        return {
            "search_type": "comprehensive_search",
            "query": input_data.query,
            "onyx_results": {},
            "vector_results": [],
            "graph_results": [],
            "combined_summary": f"Search failed due to error: {str(e)}",
            "total_sources": 0,
            "error": str(e)
        }
