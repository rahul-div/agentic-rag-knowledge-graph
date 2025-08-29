"""
Neo4j + Graphiti tenant isolation implementation.

This module provides industry-standard multi-tenant knowledge graph operations
for Local Path: Dual Storage architecture with complete tenant isolation.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

from neo4j import AsyncGraphDatabase, AsyncDriver
from graphiti import Graphiti
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class TenantAwareGraphModel(BaseModel):
    """Base model for tenant-aware graph entities."""
    tenant_id: str = Field(..., description="Tenant identifier for graph isolation")


class GraphEntity(TenantAwareGraphModel):
    """Graph entity with tenant isolation."""
    uuid: Optional[str] = None
    name: str
    entity_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    summary: Optional[str] = None


class GraphRelationship(TenantAwareGraphModel):
    """Graph relationship with tenant isolation."""
    uuid: Optional[str] = None
    source_entity_uuid: str
    target_entity_uuid: str
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    summary: Optional[str] = None


class GraphFact(TenantAwareGraphModel):
    """Graph fact with tenant context."""
    uuid: Optional[str] = None
    fact: str
    entity_uuids: List[str] = Field(default_factory=list)
    valid_at: Optional[datetime] = None
    invalid_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Episode(TenantAwareGraphModel):
    """Episode (document) processed by Graphiti."""
    uuid: Optional[str] = None
    name: str
    content: str
    source_description: str
    reference_time: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Neo4jGraphitiTenantManager:
    """
    Neo4j + Graphiti tenant isolation manager.
    
    Provides secure multi-tenant knowledge graph operations with complete
    entity and relationship isolation using tenant-aware queries.
    """
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver: Optional[AsyncDriver] = None
        self.graphiti_clients: Dict[str, Graphiti] = {}  # Per-tenant Graphiti instances
    
    async def initialize(self):
        """Initialize Neo4j connection and setup tenant constraints."""
        self.driver = AsyncGraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=60
        )
        
        # Verify connection and setup schema
        await self._verify_connection()
        await self._ensure_tenant_constraints()
        logger.info("Neo4j + Graphiti tenant manager initialized successfully")
    
    async def close(self):
        """Close Neo4j connection and cleanup resources."""
        if self.driver:
            await self.driver.close()
            
        # Close Graphiti clients
        for client in self.graphiti_clients.values():
            if hasattr(client, 'close'):
                await client.close()
        
        self.graphiti_clients.clear()
        logger.info("Neo4j + Graphiti connections closed")
    
    async def _verify_connection(self):
        """Verify Neo4j connection."""
        async with self.driver.session() as session:
            result = await session.run("RETURN 'Connection successful' AS message")
            record = await result.single()
            logger.debug(f"Neo4j connection verified: {record['message']}")
    
    async def _ensure_tenant_constraints(self):
        """Ensure tenant isolation constraints and indexes exist."""
        constraints_and_indexes = [
            # Tenant constraints for entities
            """
            CREATE CONSTRAINT tenant_entity_constraint IF NOT EXISTS
            FOR (n:Entity) REQUIRE n.tenant_id IS NOT NULL
            """,
            
            # Tenant constraints for relationships
            """
            CREATE CONSTRAINT tenant_relationship_constraint IF NOT EXISTS
            FOR ()-[r:RELATES_TO]-() REQUIRE r.tenant_id IS NOT NULL
            """,
            
            # UUID constraints
            """
            CREATE CONSTRAINT entity_uuid_unique IF NOT EXISTS
            FOR (n:Entity) REQUIRE n.uuid IS UNIQUE
            """,
            
            # Tenant performance indexes
            """
            CREATE INDEX tenant_entity_index IF NOT EXISTS
            FOR (n:Entity) ON (n.tenant_id, n.name)
            """,
            
            """
            CREATE INDEX tenant_entity_type_index IF NOT EXISTS
            FOR (n:Entity) ON (n.tenant_id, n.entity_type)
            """,
            
            """
            CREATE INDEX tenant_relationship_type_index IF NOT EXISTS
            FOR ()-[r:RELATES_TO]-() ON (r.tenant_id, r.relationship_type)
            """,
            
            # Episode (document) constraints
            """
            CREATE CONSTRAINT episode_uuid_unique IF NOT EXISTS
            FOR (n:Episode) REQUIRE n.uuid IS UNIQUE
            """,
            
            """
            CREATE INDEX tenant_episode_index IF NOT EXISTS
            FOR (n:Episode) ON (n.tenant_id, n.name)
            """,
            
            # Fact nodes
            """
            CREATE INDEX tenant_fact_index IF NOT EXISTS
            FOR (n:Fact) ON (n.tenant_id)
            """,
        ]
        
        async with self.driver.session() as session:
            for constraint_query in constraints_and_indexes:
                try:
                    await session.run(constraint_query)
                    logger.debug(f"Applied constraint/index: {constraint_query[:50]}...")
                except Exception as e:
                    logger.warning(f"Constraint/index warning (may already exist): {e}")
    
    def _get_graphiti_client(self, tenant_id: str) -> Graphiti:
        """Get or create tenant-specific Graphiti client."""
        if tenant_id not in self.graphiti_clients:
            # Create tenant-specific Graphiti client with isolated namespace
            self.graphiti_clients[tenant_id] = Graphiti(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password,
                database="neo4j",  # Use same database but different namespace
                # Add tenant prefix to all node labels and relationship types
                namespace_prefix=f"tenant_{tenant_id}_"
            )
            logger.info(f"Created Graphiti client for tenant: {tenant_id}")
        
        return self.graphiti_clients[tenant_id]
    
    # Tenant Validation
    
    async def validate_tenant(self, tenant_id: str) -> bool:
        """Validate tenant exists and is active in Neo4j."""
        query = """
        MATCH (t:TenantConfig {tenant_id: $tenant_id, status: 'active'})
        RETURN t
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, tenant_id=tenant_id)
            record = await result.single()
            return record is not None
    
    async def create_tenant_config(self, tenant_id: str, name: str, **metadata) -> bool:
        """Create tenant configuration in Neo4j."""
        query = """
        MERGE (t:TenantConfig {tenant_id: $tenant_id})
        SET t.name = $name,
            t.status = 'active',
            t.created_at = datetime(),
            t.metadata = $metadata
        RETURN t
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                tenant_id=tenant_id,
                name=name,
                metadata=metadata
            )
            record = await result.single()
            
            if record:
                logger.info(f"Created tenant config: {tenant_id} ({name})")
                return True
            return False
    
    # Episode (Document) Operations with Tenant Isolation
    
    async def add_episode(
        self,
        tenant_id: str,
        name: str,
        content: str,
        source_description: str,
        reference_time: Optional[datetime] = None,
        metadata: Dict[str, Any] = None
    ) -> Episode:
        """
        Add episode (document) with tenant isolation using Graphiti.
        
        This automatically extracts entities and relationships from the content
        and tags everything with the tenant_id.
        """
        # Get tenant-specific Graphiti client
        graphiti_client = self._get_graphiti_client(tenant_id)
        
        # Prepare episode data
        episode_time = reference_time or datetime.now(timezone.utc)
        episode_metadata = metadata or {}
        episode_metadata['tenant_id'] = tenant_id  # Ensure tenant_id in metadata
        
        try:
            # Use Graphiti to process the episode
            result = await graphiti_client.add_episode(
                name=name,
                episode_body=content,
                source_description=source_description,
                reference_time=episode_time.isoformat(),
                metadata=episode_metadata
            )
            
            # Tag all created entities with tenant_id
            await self._tag_episode_entities(tenant_id, result.episode_uuid)
            
            episode = Episode(
                uuid=result.episode_uuid,
                name=name,
                content=content,
                source_description=source_description,
                reference_time=episode_time,
                tenant_id=tenant_id,
                metadata=episode_metadata
            )
            
            logger.info(f"Added episode {name} for tenant {tenant_id}: {result.episode_uuid}")
            return episode
            
        except Exception as e:
            logger.error(f"Error adding episode for tenant {tenant_id}: {e}")
            raise
    
    async def _tag_episode_entities(self, tenant_id: str, episode_uuid: str):
        """Tag all entities and relationships from episode with tenant_id."""
        queries = [
            # Tag entities created in this episode
            """
            MATCH (e:Entity)-[:FROM_EPISODE]->(ep:Episode {uuid: $episode_uuid})
            SET e.tenant_id = $tenant_id
            """,
            
            # Tag relationships created in this episode  
            """
            MATCH ()-[r:RELATES_TO]->()
            WHERE r.episode_uuid = $episode_uuid
            SET r.tenant_id = $tenant_id
            """,
            
            # Tag facts created in this episode
            """
            MATCH (f:Fact)-[:FROM_EPISODE]->(ep:Episode {uuid: $episode_uuid})
            SET f.tenant_id = $tenant_id
            """,
            
            # Tag the episode itself
            """
            MATCH (ep:Episode {uuid: $episode_uuid})
            SET ep.tenant_id = $tenant_id
            """
        ]
        
        async with self.driver.session() as session:
            for query in queries:
                try:
                    await session.run(query, episode_uuid=episode_uuid, tenant_id=tenant_id)
                except Exception as e:
                    logger.warning(f"Tagging query warning: {e}")
    
    # Entity Operations with Tenant Isolation
    
    async def search_entities(
        self,
        tenant_id: str,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[GraphEntity]:
        """Search entities within tenant boundary."""
        # Build Cypher query with tenant filtering
        where_clauses = ["n.tenant_id = $tenant_id"]
        params = {"tenant_id": tenant_id, "query": query, "limit": limit}
        
        if entity_types:
            where_clauses.append("n.entity_type IN $entity_types")
            params["entity_types"] = entity_types
        
        # Text search in name and properties
        where_clauses.append(
            "(n.name CONTAINS $query OR "
            "ANY(key IN keys(n.properties) WHERE n.properties[key] CONTAINS $query))"
        )
        
        cypher_query = f"""
        MATCH (n:Entity)
        WHERE {' AND '.join(where_clauses)}
        RETURN n
        ORDER BY n.name
        LIMIT $limit
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher_query, **params)
            entities = []
            
            async for record in result:
                node = record['n']
                entity = GraphEntity(
                    uuid=node.get('uuid'),
                    name=node.get('name', ''),
                    entity_type=node.get('entity_type', ''),
                    properties=node.get('properties', {}),
                    tenant_id=node.get('tenant_id'),
                    created_at=node.get('created_at'),
                    summary=node.get('summary')
                )
                entities.append(entity)
            
            logger.debug(f"Found {len(entities)} entities for tenant {tenant_id}")
            return entities
    
    async def get_entity_relationships(
        self,
        tenant_id: str,
        entity_uuid: str,
        relationship_types: Optional[List[str]] = None,
        direction: str = "both",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get entity relationships within tenant boundary."""
        # Direction patterns
        direction_patterns = {
            "outgoing": "(source)-[r:RELATES_TO]->(target)",
            "incoming": "(source)<-[r:RELATES_TO]-(target)", 
            "both": "(source)-[r:RELATES_TO]-(target)"
        }
        
        pattern = direction_patterns.get(direction, direction_patterns["both"])
        
        where_clauses = [
            "source.tenant_id = $tenant_id",
            "target.tenant_id = $tenant_id", 
            "r.tenant_id = $tenant_id",
            "source.uuid = $entity_uuid"
        ]
        
        params = {
            "tenant_id": tenant_id,
            "entity_uuid": entity_uuid,
            "limit": limit
        }
        
        if relationship_types:
            where_clauses.append("r.relationship_type IN $relationship_types")
            params["relationship_types"] = relationship_types
        
        cypher_query = f"""
        MATCH {pattern}
        WHERE {' AND '.join(where_clauses)}
        RETURN source, r, target
        ORDER BY r.created_at DESC
        LIMIT $limit
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher_query, **params)
            relationships = []
            
            async for record in result:
                source_node = record['source']
                rel = record['r']
                target_node = record['target']
                
                relationship_data = {
                    'relationship_uuid': rel.get('uuid'),
                    'relationship_type': rel.get('relationship_type'),
                    'source_entity': {
                        'uuid': source_node.get('uuid'),
                        'name': source_node.get('name'),
                        'entity_type': source_node.get('entity_type')
                    },
                    'target_entity': {
                        'uuid': target_node.get('uuid'),
                        'name': target_node.get('name'),
                        'entity_type': target_node.get('entity_type')
                    },
                    'properties': rel.get('properties', {}),
                    'created_at': rel.get('created_at'),
                    'tenant_id': rel.get('tenant_id')
                }
                relationships.append(relationship_data)
            
            logger.debug(f"Found {len(relationships)} relationships for entity {entity_uuid}")
            return relationships
    
    async def get_entity_timeline(
        self,
        tenant_id: str,
        entity_uuid: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get entity timeline (facts and events) within tenant."""
        cypher_query = """
        MATCH (e:Entity {uuid: $entity_uuid, tenant_id: $tenant_id})
        OPTIONAL MATCH (e)-[:HAS_FACT]->(f:Fact {tenant_id: $tenant_id})
        OPTIONAL MATCH (f)-[:FROM_EPISODE]->(ep:Episode {tenant_id: $tenant_id})
        RETURN f, ep
        ORDER BY f.valid_at DESC, ep.reference_time DESC
        LIMIT $limit
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                cypher_query,
                entity_uuid=entity_uuid,
                tenant_id=tenant_id,
                limit=limit
            )
            
            timeline = []
            async for record in result:
                fact_node = record.get('f')
                episode_node = record.get('ep')
                
                if fact_node:
                    timeline_item = {
                        'type': 'fact',
                        'uuid': fact_node.get('uuid'),
                        'fact': fact_node.get('fact'),
                        'valid_at': fact_node.get('valid_at'),
                        'invalid_at': fact_node.get('invalid_at'),
                        'metadata': fact_node.get('metadata', {}),
                        'tenant_id': fact_node.get('tenant_id')
                    }
                    
                    if episode_node:
                        timeline_item['episode'] = {
                            'uuid': episode_node.get('uuid'),
                            'name': episode_node.get('name'),
                            'reference_time': episode_node.get('reference_time')
                        }
                    
                    timeline.append(timeline_item)
            
            logger.debug(f"Found {len(timeline)} timeline items for entity {entity_uuid}")
            return timeline
    
    # Graph Search Operations with Tenant Isolation
    
    async def graph_search(
        self,
        tenant_id: str,
        query: str,
        search_type: str = "similarity",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform graph search within tenant boundary.
        
        Args:
            tenant_id: Tenant identifier
            query: Search query
            search_type: Type of search ("similarity", "entities", "facts")
            limit: Maximum results
        """
        graphiti_client = self._get_graphiti_client(tenant_id)
        
        try:
            if search_type == "similarity":
                # Use Graphiti's similarity search with tenant filtering
                results = await graphiti_client.search(
                    query=query,
                    limit=limit,
                    search_type="similarity"
                )
                
            elif search_type == "entities":
                # Search entities by name/content
                results = await self.search_entities(tenant_id, query, limit=limit)
                return [{"type": "entity", "data": entity.dict()} for entity in results]
                
            elif search_type == "facts":
                # Search facts using Cypher
                cypher_query = """
                MATCH (f:Fact {tenant_id: $tenant_id})
                WHERE f.fact CONTAINS $query
                RETURN f
                ORDER BY f.valid_at DESC
                LIMIT $limit
                """
                
                async with self.driver.session() as session:
                    result = await session.run(cypher_query, tenant_id=tenant_id, query=query, limit=limit)
                    facts = []
                    
                    async for record in result:
                        fact_node = record['f']
                        facts.append({
                            'type': 'fact',
                            'uuid': fact_node.get('uuid'),
                            'fact': fact_node.get('fact'),
                            'valid_at': fact_node.get('valid_at'),
                            'invalid_at': fact_node.get('invalid_at'),
                            'tenant_id': fact_node.get('tenant_id')
                        })
                    
                    return facts
            
            # Filter results to ensure tenant isolation
            filtered_results = []
            for result in results:
                if hasattr(result, 'tenant_id') and result.tenant_id == tenant_id:
                    filtered_results.append(result)
                elif isinstance(result, dict) and result.get('tenant_id') == tenant_id:
                    filtered_results.append(result)
            
            logger.debug(f"Graph search ({search_type}) for tenant {tenant_id}: {len(filtered_results)} results")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Graph search error for tenant {tenant_id}: {e}")
            raise
    
    # Entity Relationship Discovery
    
    async def find_connection_path(
        self,
        tenant_id: str,
        source_entity_name: str,
        target_entity_name: str,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """Find connection path between entities within tenant."""
        cypher_query = """
        MATCH (source:Entity {name: $source_name, tenant_id: $tenant_id}),
              (target:Entity {name: $target_name, tenant_id: $tenant_id})
        MATCH path = shortestPath((source)-[*1..$max_depth {tenant_id: $tenant_id}]-(target))
        RETURN path
        LIMIT 5
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                cypher_query,
                source_name=source_entity_name,
                target_name=target_entity_name,
                tenant_id=tenant_id,
                max_depth=max_depth
            )
            
            paths = []
            async for record in result:
                path = record['path']
                path_data = {
                    'length': len(path.relationships),
                    'nodes': [
                        {
                            'uuid': node.get('uuid'),
                            'name': node.get('name'),
                            'entity_type': node.get('entity_type')
                        }
                        for node in path.nodes
                    ],
                    'relationships': [
                        {
                            'type': rel.type,
                            'properties': dict(rel)
                        }
                        for rel in path.relationships
                    ]
                }
                paths.append(path_data)
            
            logger.debug(f"Found {len(paths)} connection paths between {source_entity_name} and {target_entity_name}")
            return paths
    
    # Tenant Resource Management
    
    async def get_tenant_graph_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get graph statistics for tenant."""
        stats_queries = {
            'entities': "MATCH (n:Entity {tenant_id: $tenant_id}) RETURN count(n) as count",
            'relationships': "MATCH ()-[r:RELATES_TO {tenant_id: $tenant_id}]->() RETURN count(r) as count",
            'facts': "MATCH (f:Fact {tenant_id: $tenant_id}) RETURN count(f) as count",
            'episodes': "MATCH (e:Episode {tenant_id: $tenant_id}) RETURN count(e) as count"
        }
        
        entity_types_query = """
        MATCH (n:Entity {tenant_id: $tenant_id})
        RETURN n.entity_type as entity_type, count(*) as count
        ORDER BY count DESC
        """
        
        relationship_types_query = """
        MATCH ()-[r:RELATES_TO {tenant_id: $tenant_id}]->()
        RETURN r.relationship_type as relationship_type, count(*) as count
        ORDER BY count DESC
        """
        
        stats = {}
        async with self.driver.session() as session:
            # Basic counts
            for stat_name, query in stats_queries.items():
                result = await session.run(query, tenant_id=tenant_id)
                record = await result.single()
                stats[stat_name] = record['count'] if record else 0
            
            # Entity types breakdown
            result = await session.run(entity_types_query, tenant_id=tenant_id)
            entity_types = {}
            async for record in result:
                entity_types[record['entity_type']] = record['count']
            stats['entity_types'] = entity_types
            
            # Relationship types breakdown
            result = await session.run(relationship_types_query, tenant_id=tenant_id)
            relationship_types = {}
            async for record in result:
                relationship_types[record['relationship_type']] = record['count']
            stats['relationship_types'] = relationship_types
        
        return stats
    
    async def cleanup_tenant_data(self, tenant_id: str, confirm: bool = False) -> Dict[str, int]:
        """
        Clean up all tenant data (USE WITH EXTREME CAUTION).
        
        Args:
            tenant_id: Tenant to clean up
            confirm: Must be True to actually delete data
        """
        if not confirm:
            raise ValueError("Must set confirm=True to delete tenant data")
        
        cleanup_queries = [
            "MATCH (f:Fact {tenant_id: $tenant_id}) DETACH DELETE f",
            "MATCH ()-[r:RELATES_TO {tenant_id: $tenant_id}]->() DELETE r",
            "MATCH (n:Entity {tenant_id: $tenant_id}) DETACH DELETE n",
            "MATCH (e:Episode {tenant_id: $tenant_id}) DETACH DELETE e",
        ]
        
        deleted_counts = {}
        async with self.driver.session() as session:
            for query in cleanup_queries:
                result = await session.run(query, tenant_id=tenant_id)
                summary = await result.consume()
                deleted_counts[query.split()[1].strip('(:')] = summary.counters.nodes_deleted + summary.counters.relationships_deleted
        
        # Remove tenant from Graphiti clients cache
        if tenant_id in self.graphiti_clients:
            del self.graphiti_clients[tenant_id]
        
        logger.warning(f"Deleted all data for tenant {tenant_id}: {deleted_counts}")
        return deleted_counts


# Usage Example and Testing
async def example_usage():
    """Example usage of Neo4jGraphitiTenantManager."""
    # Initialize with Neo4j credentials
    neo4j_uri = "neo4j+s://your-neo4j-instance.databases.neo4j.io"
    username = "neo4j"
    password = "your-password"
    
    manager = Neo4jGraphitiTenantManager(neo4j_uri, username, password)
    await manager.initialize()
    
    try:
        tenant_id = "client_demo"
        
        # Create tenant config
        await manager.create_tenant_config(tenant_id, "Demo Client Corp")
        print(f"Created tenant config: {tenant_id}")
        
        # Add episode (document) with entity extraction
        episode = await manager.add_episode(
            tenant_id=tenant_id,
            name="Project Meeting Notes",
            content="""
            Today we discussed the Q4 roadmap with the development team.
            John Smith, the project manager, outlined the key milestones.
            Sarah Johnson from the design team presented the new UI mockups.
            We need to integrate with the payment system by December 15th.
            The backend API development is led by Mike Chen.
            """,
            source_description="Meeting notes from October 15, 2024",
            metadata={"meeting_type": "planning", "attendees": 5}
        )
        print(f"Added episode: {episode.name}")
        
        # Search entities
        entities = await manager.search_entities(tenant_id, "project", limit=5)
        print(f"Found {len(entities)} entities related to 'project'")
        
        if entities:
            entity_uuid = entities[0].uuid
            # Get entity relationships
            relationships = await manager.get_entity_relationships(tenant_id, entity_uuid)
            print(f"Found {len(relationships)} relationships for entity")
            
            # Get entity timeline
            timeline = await manager.get_entity_timeline(tenant_id, entity_uuid)
            print(f"Found {len(timeline)} timeline events for entity")
        
        # Graph search
        search_results = await manager.graph_search(tenant_id, "development team", search_type="facts")
        print(f"Graph search results: {len(search_results)}")
        
        # Get tenant statistics
        stats = await manager.get_tenant_graph_stats(tenant_id)
        print(f"Tenant statistics: {stats}")
        
    finally:
        await manager.close()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())