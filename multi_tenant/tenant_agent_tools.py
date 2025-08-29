"""
Tenant-aware Pydantic AI tools for multi-tenant Local Path: Dual Storage system.

All tools enforce tenant isolation and provide intelligent search synthesis
combining Neon PostgreSQL + pgvector with Neo4j + Graphiti knowledge graphs.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .tenant_models import (
    VectorSearchInput, GraphSearchInput, LocalDualSearchInput,
    SearchResult, TenantAware
)
from .neon_tenant_isolation import NeonTenantManager
from .neo4j_graphiti_tenant_isolation import Neo4jGraphitiTenantManager

logger = logging.getLogger(__name__)


class AgentDependencies(BaseModel):
    """Dependencies for tenant-aware AI agent."""
    neon_manager: NeonTenantManager
    neo4j_manager: Neo4jGraphitiTenantManager
    embedder: Any  # Embedding service (OpenAI, Gemini, etc.)
    session_id: Optional[str] = None
    tenant_id: str
    user_id: str = "api_user"
    
    class Config:
        arbitrary_types_allowed = True


# Initialize tenant-aware agent
rag_agent = Agent(
    model="gemini-1.5-pro",  # Default model, configurable
    deps_type=AgentDependencies,
    system_prompt="""You are an intelligent AI assistant with advanced Local Path: Dual Storage capabilities. 
    You have access to tenant-isolated search systems:

    🔍 **NEON POSTGRESQL + PGVECTOR**: Fast semantic similarity search across document chunks
    🔗 **NEO4J + GRAPHITI**: Knowledge graph for entity relationships and hidden insights

    ## 🎯 INTELLIGENT TOOL ROUTING STRATEGY

    **For Semantic Similarity & Content Discovery** → Use vector_search_tool:
    - "Find similar content to..."
    - "What documents discuss..."
    - "Search for related concepts..."

    **For Relationship Discovery & Entity Analysis** → Use graph_search_tool:
    - "How are X and Y connected?"
    - "What relationships exist between...?"
    - "Show me the dependencies..."
    - "Find connections between entities..."

    **For SMART Combined Analysis (DEFAULT)** → Use local_dual_search_tool:
    - "What's the relationship between X and similar content?"
    - "Find semantic matches AND show connections..."
    - "Comprehensive analysis of..."
    - "Combined insights from content and relationships..."

    ## 🔄 TENANT ISOLATION RULES

    - ALL operations are automatically scoped to the authenticated tenant
    - NO cross-tenant data access is possible
    - Source citations MUST include tenant validation
    - Response confidence based on tenant-specific data quality

    ## 📋 RESPONSE QUALITY GUIDELINES

    **Always Provide**:
    - Clear, accurate answers based on tenant data
    - Source citations with document/entity references  
    - Confidence indicators for data availability
    - Transparent tool usage information

    **Response Structure**:
    1. **Direct Answer**: Lead with most relevant tenant-specific information
    2. **Supporting Evidence**: Quote sources and provide context
    3. **Additional Context**: Related information from tenant's knowledge base
    4. **Source Attribution**: Clear citation of tenant documents/entities

    Remember: You operate within complete tenant isolation. All searches, analysis, and responses are scoped exclusively to the authenticated tenant's data."""
)


# Core Search Tools with Tenant Isolation

@rag_agent.tool
async def vector_search_tool(
    ctx: RunContext[AgentDependencies],
    query: str,
    limit: int = 10,
    threshold: float = 0.7,
    include_metadata: bool = True
) -> str:
    """
    Semantic vector search within tenant boundary using Neon PostgreSQL + pgvector.
    
    Performs similarity search across document chunks using vector embeddings
    with complete tenant isolation.
    
    Args:
        query: Search query text
        limit: Maximum results to return (1-50)
        threshold: Similarity threshold (0.0-1.0)
        include_metadata: Include chunk metadata
    
    Returns:
        Formatted search results with source citations
    """
    try:
        # Validate input
        search_input = VectorSearchInput(
            tenant_id=ctx.deps.tenant_id,
            query=query,
            limit=min(limit, 50),
            threshold=max(0.0, min(1.0, threshold)),
            include_metadata=include_metadata
        )
        
        # Generate embedding for query
        embedding = await ctx.deps.embedder.embed_text(search_input.query)
        
        # Perform tenant-isolated vector search
        results = await ctx.deps.neon_manager.vector_search(
            embedding=embedding,
            tenant_id=search_input.tenant_id,
            threshold=search_input.threshold,
            limit=search_input.limit
        )
        
        if not results:
            return f"🔍 **Vector Search Results**: No relevant documents found for query '{query}' in your knowledge base.\n\n*Try adjusting your search terms or lowering the similarity threshold.*"
        
        # Format results with tenant validation
        formatted_results = []
        total_score = 0.0
        
        for i, result in enumerate(results, 1):
            # Verify tenant isolation
            if result.get('tenant_id') != search_input.tenant_id:
                logger.error(f"Tenant isolation violation in vector search: {result.get('tenant_id')} != {search_input.tenant_id}")
                continue
            
            score = result.get('similarity', 0.0)
            total_score += score
            
            result_text = f"""**{i}. {result.get('document_title', 'Untitled')}** (Similarity: {score:.3f})
   📄 *Source*: {result.get('document_source', 'Unknown')}
   📝 *Content*: {result.get('content', '')[:200]}{'...' if len(result.get('content', '')) > 200 else ''}"""
            
            if include_metadata and result.get('metadata'):
                metadata_str = ', '.join([f"{k}: {v}" for k, v in result['metadata'].items() if v])
                if metadata_str:
                    result_text += f"\n   🏷️  *Metadata*: {metadata_str}"
            
            formatted_results.append(result_text)
        
        # Calculate average confidence
        avg_confidence = total_score / len(results) if results else 0.0
        confidence_indicator = "🟢 High" if avg_confidence > 0.8 else "🟡 Medium" if avg_confidence > 0.6 else "🔴 Low"
        
        response = f"""🔍 **Vector Search Results** ({len(results)} documents found)

**Query**: {query}
**Confidence**: {confidence_indicator} ({avg_confidence:.2f})
**Search Scope**: Tenant-isolated document collection

{chr(10).join(formatted_results)}

💡 *Results are semantically similar to your query and sourced exclusively from your tenant's knowledge base.*"""
        
        logger.info(f"Vector search completed for tenant {search_input.tenant_id}: {len(results)} results")
        return response
        
    except Exception as e:
        logger.error(f"Vector search error for tenant {ctx.deps.tenant_id}: {e}")
        return f"❌ **Vector Search Error**: Failed to search documents. Please try again or contact support.\n\n*Error details: {str(e)[:100]}*"


@rag_agent.tool  
async def graph_search_tool(
    ctx: RunContext[AgentDependencies],
    query: str,
    limit: int = 10,
    search_type: str = "similarity",
    include_relationships: bool = True
) -> str:
    """
    Knowledge graph search within tenant boundary using Neo4j + Graphiti.
    
    Discovers entities, relationships, and facts from the tenant's knowledge graph
    with complete tenant isolation.
    
    Args:
        query: Search query text
        limit: Maximum results to return (1-20)
        search_type: Type of search ("similarity", "entities", "facts")
        include_relationships: Include relationship information
    
    Returns:
        Formatted graph search results with entity/relationship details
    """
    try:
        # Validate input
        search_input = GraphSearchInput(
            tenant_id=ctx.deps.tenant_id,
            query=query,
            limit=min(limit, 20),
            search_type=search_type,
            include_relationships=include_relationships
        )
        
        # Perform tenant-isolated graph search
        results = await ctx.deps.neo4j_manager.graph_search(
            tenant_id=search_input.tenant_id,
            query=search_input.query,
            search_type=search_input.search_type,
            limit=search_input.limit
        )
        
        if not results:
            return f"🔗 **Knowledge Graph Results**: No relevant entities or relationships found for query '{query}' in your knowledge base.\n\n*Try different search terms or check if related content has been ingested.*"
        
        # Format results with tenant validation
        formatted_results = []
        entities_found = 0
        relationships_found = 0
        facts_found = 0
        
        for i, result in enumerate(results, 1):
            result_data = result.get('data', result) if isinstance(result, dict) else result
            
            # Verify tenant isolation
            if hasattr(result_data, 'tenant_id') and result_data.tenant_id != search_input.tenant_id:
                logger.error(f"Tenant isolation violation in graph search: {result_data.tenant_id} != {search_input.tenant_id}")
                continue
            elif isinstance(result_data, dict) and result_data.get('tenant_id') != search_input.tenant_id:
                logger.error(f"Tenant isolation violation in graph search: {result_data.get('tenant_id')} != {search_input.tenant_id}")
                continue
            
            # Format different result types
            if result.get('type') == 'entity' or hasattr(result_data, 'name'):
                entities_found += 1
                entity_name = getattr(result_data, 'name', result_data.get('name', 'Unknown Entity'))
                entity_type = getattr(result_data, 'entity_type', result_data.get('entity_type', 'Unknown'))
                
                result_text = f"**🎯 {entity_name}** ({entity_type})"
                
                # Add entity summary if available
                summary = getattr(result_data, 'summary', result_data.get('summary'))
                if summary:
                    result_text += f"\n   📋 {summary}"
                
                # Add properties if available
                properties = getattr(result_data, 'properties', result_data.get('properties', {}))
                if properties and isinstance(properties, dict):
                    prop_items = [f"{k}: {v}" for k, v in properties.items() if v][:3]  # Limit to 3 properties
                    if prop_items:
                        result_text += f"\n   🏷️  {', '.join(prop_items)}"
                
                formatted_results.append(result_text)
                
            elif result.get('type') == 'fact' or 'fact' in result_data:
                facts_found += 1
                fact_text = result_data.get('fact', str(result_data))
                result_text = f"**📋 Fact {i}**: {fact_text}"
                
                # Add validity information if available
                valid_at = result_data.get('valid_at')
                if valid_at:
                    result_text += f"\n   📅 Valid from: {valid_at}"
                
                formatted_results.append(result_text)
                
            else:
                # Generic result formatting
                result_text = f"**{i}. {str(result_data)[:100]}{'...' if len(str(result_data)) > 100 else ''}**"
                formatted_results.append(result_text)
        
        # Add relationship information if requested
        if include_relationships and entities_found > 0:
            try:
                # Get relationships for first few entities
                relationship_summary = "🔗 **Key Relationships Found**:\n"
                rel_count = 0
                
                for result in results[:3]:  # Limit to first 3 entities
                    result_data = result.get('data', result)
                    if hasattr(result_data, 'uuid'):
                        entity_uuid = result_data.uuid
                        entity_name = getattr(result_data, 'name', 'Unknown')
                        
                        relationships = await ctx.deps.neo4j_manager.get_entity_relationships(
                            tenant_id=search_input.tenant_id,
                            entity_uuid=entity_uuid,
                            limit=3
                        )
                        
                        for rel in relationships[:2]:  # Limit to 2 relationships per entity
                            rel_type = rel.get('relationship_type', 'RELATED_TO')
                            target_name = rel.get('target_entity', {}).get('name', 'Unknown')
                            relationship_summary += f"   • {entity_name} → {rel_type} → {target_name}\n"
                            rel_count += 1
                
                if rel_count > 0:
                    formatted_results.append(relationship_summary.rstrip())
                    relationships_found = rel_count
                    
            except Exception as rel_error:
                logger.warning(f"Could not fetch relationships: {rel_error}")
        
        # Build summary statistics
        stats_summary = []
        if entities_found > 0:
            stats_summary.append(f"{entities_found} entities")
        if facts_found > 0:
            stats_summary.append(f"{facts_found} facts")
        if relationships_found > 0:
            stats_summary.append(f"{relationships_found} relationships")
        
        stats_text = ", ".join(stats_summary) if stats_summary else "mixed results"
        
        response = f"""🔗 **Knowledge Graph Results** ({stats_text} found)

**Query**: {query}
**Search Type**: {search_type}
**Search Scope**: Tenant-isolated knowledge graph

{chr(10).join(formatted_results)}

🧠 *Results reveal entity relationships and hidden connections from your tenant's knowledge base.*"""
        
        logger.info(f"Graph search completed for tenant {search_input.tenant_id}: {len(results)} results")
        return response
        
    except Exception as e:
        logger.error(f"Graph search error for tenant {ctx.deps.tenant_id}: {e}")
        return f"❌ **Knowledge Graph Error**: Failed to search knowledge graph. Please try again or contact support.\n\n*Error details: {str(e)[:100]}*"


@rag_agent.tool
async def local_dual_search_tool(
    ctx: RunContext[AgentDependencies], 
    query: str,
    limit: int = 10,
    use_vector: bool = True,
    use_graph: bool = True,
    vector_weight: float = 0.6
) -> str:
    """
    SMART Local Path: Dual Storage search combining vector + graph with tenant isolation.
    
    Intelligently synthesizes results from both Neon PostgreSQL + pgvector (semantic similarity)
    and Neo4j + Graphiti (relationship discovery) within tenant boundaries.
    
    Args:
        query: Search query text
        limit: Maximum results per system (1-25)
        use_vector: Enable vector search component
        use_graph: Enable graph search component  
        vector_weight: Weight for vector vs graph results (0.0-1.0)
    
    Returns:
        Synthesized response combining semantic similarity with relationship insights
    """
    try:
        # Validate input
        search_input = LocalDualSearchInput(
            tenant_id=ctx.deps.tenant_id,
            query=query,
            limit=min(limit, 25),
            use_vector=use_vector,
            use_graph=use_graph,
            vector_weight=max(0.0, min(1.0, vector_weight))
        )
        
        # Validate at least one search type is enabled
        if not search_input.use_vector and not search_input.use_graph:
            return "❌ **Configuration Error**: At least one search type (vector or graph) must be enabled."
        
        # Parallel execution for optimal performance
        search_tasks = []
        
        if search_input.use_vector:
            vector_task = asyncio.create_task(
                vector_search_tool(ctx, query, search_input.limit, 0.7, True),
                name="vector_search"
            )
            search_tasks.append(("vector", vector_task))
        
        if search_input.use_graph:
            graph_task = asyncio.create_task(
                graph_search_tool(ctx, query, search_input.limit, "similarity", True),
                name="graph_search"
            )
            search_tasks.append(("graph", graph_task))
        
        # Execute searches in parallel
        logger.debug(f"Starting dual search for tenant {search_input.tenant_id}: {len(search_tasks)} tasks")
        
        search_results = {}
        completed_tasks = 0
        
        for search_type, task in search_tasks:
            try:
                result = await task
                search_results[search_type] = result
                completed_tasks += 1
                logger.debug(f"Completed {search_type} search for tenant {search_input.tenant_id}")
            except Exception as task_error:
                logger.error(f"{search_type} search failed for tenant {search_input.tenant_id}: {task_error}")
                search_results[search_type] = f"❌ {search_type.title()} search temporarily unavailable: {str(task_error)[:50]}"
        
        if completed_tasks == 0:
            return f"❌ **Local Dual Search Error**: All search systems failed for query '{query}'. Please try again or contact support."
        
        # Intelligent synthesis of results
        synthesis_parts = []
        
        # Header with query and scope
        synthesis_parts.append(f"""🔄 **Local Path: Dual Storage Results** 
        
**Query**: {query}
**Search Strategy**: {'Vector + Graph' if len(search_results) > 1 else list(search_results.keys())[0].title()}
**Tenant**: Isolated search within your knowledge base
**Systems**: {completed_tasks}/{len(search_tasks)} active

---""")
        
        # Vector search results (semantic similarity)
        if "vector" in search_results:
            vector_result = search_results["vector"]
            if not vector_result.startswith("❌"):
                synthesis_parts.append(f"## 📊 **Semantic Content Analysis**\n{vector_result}\n")
            else:
                synthesis_parts.append(f"## 📊 **Semantic Content Analysis**\n{vector_result}\n")
        
        # Graph search results (relationships and entities)
        if "graph" in search_results:
            graph_result = search_results["graph"]  
            if not graph_result.startswith("❌"):
                synthesis_parts.append(f"## 🧠 **Knowledge Graph Insights**\n{graph_result}\n")
            else:
                synthesis_parts.append(f"## 🧠 **Knowledge Graph Insights**\n{graph_result}\n")
        
        # Intelligent synthesis summary
        successful_searches = [k for k, v in search_results.items() if not v.startswith("❌")]
        
        if len(successful_searches) > 1:
            synthesis_parts.append(f"""## 🎯 **Intelligent Synthesis**

Your query revealed information through **both semantic similarity and relationship analysis**:

🔍 **Content Perspective**: Found relevant documents and passages that semantically match your query
🔗 **Relationship Perspective**: Discovered connected entities and hidden relationships in your knowledge base

This **dual-path analysis** provides both direct content matches and contextual connections, offering a comprehensive view of information within your tenant's data scope.

---

💡 **Search Quality**: {len(successful_searches)}/2 systems active • **Tenant Isolation**: Complete • **Data Scope**: Your knowledge base only""")
        
        elif len(successful_searches) == 1:
            search_type = successful_searches[0]
            synthesis_parts.append(f"""## 🎯 **Single-System Results**

Results provided by **{search_type} search only**. {'Graph search was unavailable - results show semantic similarity only.' if search_type == 'vector' else 'Vector search was unavailable - results show relationship analysis only.'}

💡 **Search Quality**: {len(successful_searches)}/2 systems active • **Tenant Isolation**: Complete • **Data Scope**: Your knowledge base only""")
        
        else:
            synthesis_parts.append("""## ❌ **Search Unavailable**

Both search systems encountered errors. This may be temporary - please try again in a few moments.

💡 **Troubleshooting**: Check your query format, verify data ingestion, or contact support if the issue persists.""")
        
        # Join all parts
        final_response = "\n".join(synthesis_parts)
        
        # Log successful completion
        logger.info(f"Local dual search completed for tenant {search_input.tenant_id}: {completed_tasks}/{len(search_tasks)} systems, query='{query[:50]}'")
        
        return final_response
        
    except Exception as e:
        logger.error(f"Local dual search error for tenant {ctx.deps.tenant_id}: {e}")
        return f"""❌ **Local Dual Search System Error**

Failed to execute multi-system search for query: '{query}'

**Error**: {str(e)[:100]}{'...' if len(str(e)) > 100 else ''}

💡 **Next Steps**: Try a simpler query, check system status, or contact support if the issue persists."""


# Entity and Relationship Discovery Tools

@rag_agent.tool
async def get_entity_relationships_tool(
    ctx: RunContext[AgentDependencies],
    entity_name: str,
    relationship_types: Optional[List[str]] = None,
    direction: str = "both",
    limit: int = 20
) -> str:
    """
    Discover relationships for a specific entity within tenant boundary.
    
    Args:
        entity_name: Name of the entity to explore
        relationship_types: Filter by relationship types (optional)
        direction: Relationship direction ("both", "outgoing", "incoming")
        limit: Maximum relationships to return
    
    Returns:
        Formatted entity relationship information
    """
    try:
        # Find entity first
        entities = await ctx.deps.neo4j_manager.search_entities(
            tenant_id=ctx.deps.tenant_id,
            query=entity_name,
            limit=1
        )
        
        if not entities:
            return f"🔍 **Entity Not Found**: No entity named '{entity_name}' found in your knowledge base.\n\n*Try searching for similar terms or check if the entity has been ingested.*"
        
        entity = entities[0]
        
        # Get relationships
        relationships = await ctx.deps.neo4j_manager.get_entity_relationships(
            tenant_id=ctx.deps.tenant_id,
            entity_uuid=entity.uuid,
            relationship_types=relationship_types,
            direction=direction,
            limit=limit
        )
        
        if not relationships:
            return f"🔗 **No Relationships Found**: Entity '{entity_name}' has no relationships in the specified direction.\n\n*This entity may be isolated or relationships haven't been extracted yet.*"
        
        # Format relationships
        formatted_rels = []
        rel_types = set()
        
        for i, rel in enumerate(relationships, 1):
            rel_type = rel.get('relationship_type', 'RELATED_TO')
            source_name = rel.get('source_entity', {}).get('name', 'Unknown')
            target_name = rel.get('target_entity', {}).get('name', 'Unknown')
            
            rel_types.add(rel_type)
            
            formatted_rels.append(
                f"**{i}. {source_name}** → *{rel_type}* → **{target_name}**"
            )
        
        response = f"""🔗 **Entity Relationships** for "{entity_name}"

**Entity Type**: {entity.entity_type}
**Direction**: {direction}
**Relationships Found**: {len(relationships)}
**Relationship Types**: {', '.join(sorted(rel_types))}

{chr(10).join(formatted_rels)}

💡 *All relationships are within your tenant's knowledge base and show how this entity connects to others.*"""
        
        return response
        
    except Exception as e:
        logger.error(f"Entity relationships error for tenant {ctx.deps.tenant_id}: {e}")
        return f"❌ **Entity Relationship Error**: Failed to retrieve relationships for '{entity_name}'.\n\n*Error: {str(e)[:100]}*"


@rag_agent.tool
async def get_entity_timeline_tool(
    ctx: RunContext[AgentDependencies],
    entity_name: str,
    limit: int = 50
) -> str:
    """
    Get temporal timeline for an entity within tenant boundary.
    
    Args:
        entity_name: Name of the entity to explore
        limit: Maximum timeline events to return
    
    Returns:
        Formatted entity timeline information
    """
    try:
        # Find entity first
        entities = await ctx.deps.neo4j_manager.search_entities(
            tenant_id=ctx.deps.tenant_id,
            query=entity_name,
            limit=1
        )
        
        if not entities:
            return f"🔍 **Entity Not Found**: No entity named '{entity_name}' found in your knowledge base."
        
        entity = entities[0]
        
        # Get timeline
        timeline = await ctx.deps.neo4j_manager.get_entity_timeline(
            tenant_id=ctx.deps.tenant_id,
            entity_uuid=entity.uuid,
            limit=limit
        )
        
        if not timeline:
            return f"📅 **No Timeline Found**: Entity '{entity_name}' has no temporal information available."
        
        # Format timeline
        formatted_timeline = []
        
        for i, event in enumerate(timeline, 1):
            event_date = event.get('valid_at', 'Unknown date')
            fact = event.get('fact', str(event))
            
            episode_info = ""
            if event.get('episode'):
                episode = event['episode']
                episode_info = f"\n   📄 *Source*: {episode.get('name', 'Unknown')}"
            
            formatted_timeline.append(
                f"**{i}. {event_date}**: {fact}{episode_info}"
            )
        
        response = f"""📅 **Entity Timeline** for "{entity_name}"

**Entity Type**: {entity.entity_type}
**Timeline Events**: {len(timeline)}
**Time Span**: {timeline[-1].get('valid_at', 'Unknown')} to {timeline[0].get('valid_at', 'Unknown')}

{chr(10).join(formatted_timeline)}

💡 *Timeline shows temporal facts and events for this entity from your knowledge base.*"""
        
        return response
        
    except Exception as e:
        logger.error(f"Entity timeline error for tenant {ctx.deps.tenant_id}: {e}")
        return f"❌ **Entity Timeline Error**: Failed to retrieve timeline for '{entity_name}'.\n\n*Error: {str(e)[:100]}*"


# Connection Discovery Tool

@rag_agent.tool
async def find_connection_path_tool(
    ctx: RunContext[AgentDependencies],
    source_entity: str,
    target_entity: str,
    max_depth: int = 3
) -> str:
    """
    Find connection paths between two entities within tenant boundary.
    
    Args:
        source_entity: Starting entity name
        target_entity: Target entity name
        max_depth: Maximum path depth to explore
    
    Returns:
        Formatted connection path information
    """
    try:
        # Find connection paths
        paths = await ctx.deps.neo4j_manager.find_connection_path(
            tenant_id=ctx.deps.tenant_id,
            source_entity_name=source_entity,
            target_entity_name=target_entity,
            max_depth=max_depth
        )
        
        if not paths:
            return f"""🔍 **No Connection Found** between "{source_entity}" and "{target_entity}"

These entities may not be connected within {max_depth} relationship steps, or one or both entities may not exist in your knowledge base.

💡 *Try increasing the max_depth parameter or verify both entity names.*"""
        
        # Format connection paths
        formatted_paths = []
        
        for i, path in enumerate(paths, 1):
            path_length = path.get('length', 0)
            nodes = path.get('nodes', [])
            relationships = path.get('relationships', [])
            
            # Build path visualization
            path_viz = []
            for j, node in enumerate(nodes):
                node_name = node.get('name', 'Unknown')
                path_viz.append(f"**{node_name}**")
                
                # Add relationship arrow if not last node
                if j < len(relationships):
                    rel = relationships[j]
                    rel_type = rel.get('type', 'RELATED_TO')
                    path_viz.append(f" → *{rel_type}* → ")
            
            path_text = "".join(path_viz)
            formatted_paths.append(f"**Path {i}** ({path_length} steps):\n   {path_text}")
        
        response = f"""🔗 **Connection Paths** from "{source_entity}" to "{target_entity}"

**Paths Found**: {len(paths)}
**Maximum Depth**: {max_depth} steps
**Shortest Path**: {min(p.get('length', 999) for p in paths)} steps

{chr(10).join(formatted_paths)}

💡 *Paths show how these entities are connected through your knowledge base relationships.*"""
        
        return response
        
    except Exception as e:
        logger.error(f"Connection path error for tenant {ctx.deps.tenant_id}: {e}")
        return f"""❌ **Connection Path Error**: Failed to find path between "{source_entity}" and "{target_entity}".

*Error: {str(e)[:100]}*"""


# Tenant Statistics and Health Tools

@rag_agent.tool
async def get_tenant_stats_tool(
    ctx: RunContext[AgentDependencies]
) -> str:
    """
    Get comprehensive statistics for the current tenant's knowledge base.
    
    Returns:
        Formatted tenant statistics and health information
    """
    try:
        # Get database statistics
        db_usage = await ctx.deps.neon_manager.get_tenant_usage(ctx.deps.tenant_id)
        
        # Get graph statistics  
        graph_stats = await ctx.deps.neo4j_manager.get_tenant_graph_stats(ctx.deps.tenant_id)
        
        # Format statistics
        response = f"""📊 **Knowledge Base Statistics** for your tenant

## 📄 **Document Storage (PostgreSQL)**
- **Documents**: {db_usage.get('documents', 0):,}
- **Content Chunks**: {db_usage.get('chunks', 0):,}
- **Storage Used**: {db_usage.get('storage_mb', 0):.1f} MB
- **Active Sessions**: {db_usage.get('active_sessions', 0)}

## 🧠 **Knowledge Graph (Neo4j)**
- **Entities**: {graph_stats.get('entities', 0):,}
- **Relationships**: {graph_stats.get('relationships', 0):,}  
- **Facts**: {graph_stats.get('facts', 0):,}
- **Episodes**: {graph_stats.get('episodes', 0):,}

## 🏷️ **Entity Types**"""
        
        # Add entity types breakdown
        entity_types = graph_stats.get('entity_types', {})
        if entity_types:
            for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                response += f"\n- **{entity_type}**: {count:,}"
        else:
            response += "\n- *No entities found*"
        
        response += "\n\n## 🔗 **Relationship Types**"
        
        # Add relationship types breakdown
        rel_types = graph_stats.get('relationship_types', {})
        if rel_types:
            for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                response += f"\n- **{rel_type}**: {count:,}"
        else:
            response += "\n- *No relationships found*"
        
        response += f"""

## 💡 **Insights**
- **Knowledge Density**: {(graph_stats.get('relationships', 0) / max(graph_stats.get('entities', 1), 1)):.1f} relationships per entity
- **Content Coverage**: {(graph_stats.get('episodes', 0) / max(db_usage.get('documents', 1), 1)):.1f} knowledge episodes per document  
- **Data Isolation**: Complete tenant boundary enforcement active

*Statistics are updated in real-time and reflect only your tenant's data.*"""
        
        return response
        
    except Exception as e:
        logger.error(f"Tenant stats error for tenant {ctx.deps.tenant_id}: {e}")
        return f"❌ **Statistics Error**: Failed to retrieve tenant statistics.\n\n*Error: {str(e)[:100]}*"


# Export configured agent and tools
__all__ = [
    'rag_agent',
    'AgentDependencies',
    'vector_search_tool',
    'graph_search_tool', 
    'local_dual_search_tool',
    'get_entity_relationships_tool',
    'get_entity_timeline_tool',
    'find_connection_path_tool',
    'get_tenant_stats_tool'
]