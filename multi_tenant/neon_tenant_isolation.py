"""
Neon PostgreSQL + pgvector tenant isolation implementation.

This module provides industry-standard multi-tenant database operations
for Local Path: Dual Storage architecture with complete tenant isolation.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import asyncpg
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class TenantAwareModel(BaseModel):
    """Base model for all tenant-aware data structures."""
    tenant_id: str = Field(..., description="Tenant identifier for data isolation")


class Tenant(BaseModel):
    """Tenant configuration model."""
    id: str
    name: str
    status: str = "active"
    max_documents: int = 1000
    max_storage_mb: int = 500
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class Document(TenantAwareModel):
    """Document model with tenant isolation."""
    id: Optional[str] = None
    title: str
    source: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Chunk(TenantAwareModel):
    """Chunk model with tenant isolation and vector embedding."""
    id: Optional[str] = None
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    chunk_index: int
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class TenantSession(TenantAwareModel):
    """Session model with tenant context."""
    id: Optional[str] = None
    user_id: str
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class NeonTenantManager:
    """
    Neon PostgreSQL tenant isolation manager.
    
    Provides secure multi-tenant operations with complete data isolation
    using row-level security and tenant-aware queries.
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize connection pool and setup database schema."""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=5,
            max_size=20,
            command_timeout=30
        )
        
        # Verify schema exists
        await self._ensure_schema()
        logger.info("Neon tenant manager initialized successfully")
    
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Neon connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        
        async with self.pool.acquire() as conn:
            yield conn
    
    async def _ensure_schema(self):
        """Ensure all required tables and functions exist."""
        schema_queries = [
            # Enable pgvector extension
            "CREATE EXTENSION IF NOT EXISTS vector;",
            
            # Create tenants table
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                max_documents INTEGER DEFAULT 1000,
                max_storage_mb INTEGER DEFAULT 500,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                
                CONSTRAINT valid_status CHECK (status IN ('active', 'suspended', 'deleted'))
            );
            """,
            
            # Create documents table with tenant isolation
            """
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR(50) PRIMARY KEY,
                tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """,
            
            # Create chunks table with vector embeddings and tenant isolation
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id VARCHAR(50) PRIMARY KEY,
                tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                document_id VARCHAR(50) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                embedding VECTOR(768),
                chunk_index INTEGER NOT NULL,
                token_count INTEGER,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """,
            
            # Create sessions table with tenant context
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR(50) PRIMARY KEY,
                tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                user_id VARCHAR(100) NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """,
        ]
        
        # Performance indexes (tenant-first design)
        index_queries = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_tenant_id ON documents(tenant_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_tenant_updated ON documents(tenant_id, updated_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_tenant_document ON chunks(tenant_id, document_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_tenant_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WHERE tenant_id IS NOT NULL;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_tenant_user ON sessions(tenant_id, user_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_tenant_expires ON sessions(tenant_id, expires_at);",
        ]
        
        async with self.get_connection() as conn:
            # Create tables
            for query in schema_queries:
                try:
                    await conn.execute(query)
                    logger.debug(f"Executed schema query: {query[:50]}...")
                except Exception as e:
                    logger.error(f"Error executing schema query: {e}")
                    raise
            
            # Create indexes (non-blocking)
            for query in index_queries:
                try:
                    await conn.execute(query)
                    logger.debug(f"Executed index query: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"Index creation warning (may already exist): {e}")
            
            # Create tenant-aware vector search function
            await self._create_vector_search_function(conn)
            await self._create_hybrid_search_function(conn)
    
    async def _create_vector_search_function(self, conn):
        """Create tenant-aware vector search function."""
        function_sql = """
        CREATE OR REPLACE FUNCTION match_chunks_tenant(
            query_embedding VECTOR(768),
            filter_tenant_id VARCHAR(50),
            match_threshold FLOAT DEFAULT 0.7,
            match_count INTEGER DEFAULT 10
        )
        RETURNS TABLE (
            chunk_id VARCHAR(50),
            document_id VARCHAR(50),
            content TEXT,
            similarity FLOAT,
            metadata JSONB,
            document_title TEXT,
            document_source TEXT,
            tenant_id VARCHAR(50)
        )
        LANGUAGE sql STABLE
        AS $$
            SELECT 
                c.id as chunk_id,
                c.document_id,
                c.content,
                1 - (c.embedding <=> query_embedding) as similarity,
                c.metadata,
                d.title as document_title,
                d.source as document_source,
                c.tenant_id
            FROM chunks c
            INNER JOIN documents d ON c.document_id = d.id AND d.tenant_id = filter_tenant_id
            WHERE c.tenant_id = filter_tenant_id
            AND c.embedding IS NOT NULL
            AND 1 - (c.embedding <=> query_embedding) > match_threshold
            ORDER BY c.embedding <=> query_embedding
            LIMIT match_count;
        $$;
        """
        
        await conn.execute(function_sql)
        logger.debug("Created tenant-aware vector search function")
    
    async def _create_hybrid_search_function(self, conn):
        """Create tenant-aware hybrid search function combining vector + text search."""
        function_sql = """
        CREATE OR REPLACE FUNCTION hybrid_search_chunks_tenant(
            query_embedding VECTOR(768),
            query_text TEXT,
            filter_tenant_id VARCHAR(50),
            match_threshold FLOAT DEFAULT 0.7,
            match_count INTEGER DEFAULT 10,
            vector_weight FLOAT DEFAULT 0.7
        )
        RETURNS TABLE (
            chunk_id VARCHAR(50),
            document_id VARCHAR(50),
            content TEXT,
            combined_score FLOAT,
            vector_similarity FLOAT,
            text_similarity FLOAT,
            metadata JSONB,
            document_title TEXT,
            document_source TEXT,
            tenant_id VARCHAR(50)
        )
        LANGUAGE sql STABLE
        AS $$
            WITH vector_search AS (
                SELECT 
                    c.id as chunk_id,
                    c.document_id,
                    c.content,
                    1 - (c.embedding <=> query_embedding) as vector_similarity,
                    c.metadata,
                    d.title as document_title,
                    d.source as document_source,
                    c.tenant_id
                FROM chunks c
                INNER JOIN documents d ON c.document_id = d.id AND d.tenant_id = filter_tenant_id
                WHERE c.tenant_id = filter_tenant_id
                AND c.embedding IS NOT NULL
            ),
            text_search AS (
                SELECT 
                    c.id as chunk_id,
                    similarity(c.content, query_text) as text_similarity
                FROM chunks c
                INNER JOIN documents d ON c.document_id = d.id AND d.tenant_id = filter_tenant_id
                WHERE c.tenant_id = filter_tenant_id
                AND c.content ILIKE '%' || query_text || '%'
            )
            SELECT 
                vs.chunk_id,
                vs.document_id,
                vs.content,
                (vector_weight * vs.vector_similarity + (1 - vector_weight) * COALESCE(ts.text_similarity, 0)) as combined_score,
                vs.vector_similarity,
                COALESCE(ts.text_similarity, 0) as text_similarity,
                vs.metadata,
                vs.document_title,
                vs.document_source,
                vs.tenant_id
            FROM vector_search vs
            LEFT JOIN text_search ts ON vs.chunk_id = ts.chunk_id
            WHERE vs.vector_similarity > match_threshold
            ORDER BY combined_score DESC
            LIMIT match_count;
        $$;
        """
        
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            await conn.execute(function_sql)
            logger.debug("Created tenant-aware hybrid search function")
        except Exception as e:
            logger.warning(f"Could not create hybrid search function: {e}")
    
    # Tenant Management Operations
    
    async def create_tenant(self, tenant_id: str, name: str, **kwargs) -> Tenant:
        """Create a new tenant with resource limits."""
        tenant = Tenant(
            id=tenant_id,
            name=name,
            max_documents=kwargs.get('max_documents', 1000),
            max_storage_mb=kwargs.get('max_storage_mb', 500),
            metadata=kwargs.get('metadata', {})
        )
        
        query = """
        INSERT INTO tenants (id, name, status, max_documents, max_storage_mb, metadata)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING created_at, updated_at
        """
        
        async with self.get_connection() as conn:
            result = await conn.fetchrow(
                query,
                tenant.id,
                tenant.name,
                tenant.status,
                tenant.max_documents,
                tenant.max_storage_mb,
                json.dumps(tenant.metadata)
            )
            
            tenant.created_at = result['created_at']
            logger.info(f"Created tenant: {tenant_id} ({name})")
            return tenant
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        query = "SELECT * FROM tenants WHERE id = $1 AND status = 'active'"
        
        async with self.get_connection() as conn:
            result = await conn.fetchrow(query, tenant_id)
            if result:
                tenant_dict = dict(result)
                tenant_dict['metadata'] = json.loads(tenant_dict.get('metadata', '{}'))
                return Tenant(**tenant_dict)
            return None
    
    async def list_tenants(self, status: str = 'active') -> List[Tenant]:
        """List all tenants by status."""
        query = "SELECT * FROM tenants WHERE status = $1 ORDER BY name"
        
        async with self.get_connection() as conn:
            results = await conn.fetch(query, status)
            tenants = []
            for result in results:
                tenant_dict = dict(result)
                tenant_dict['metadata'] = json.loads(tenant_dict.get('metadata', '{}'))
                tenants.append(Tenant(**tenant_dict))
            return tenants
    
    async def update_tenant_status(self, tenant_id: str, status: str) -> bool:
        """Update tenant status (active, suspended, deleted)."""
        query = """
        UPDATE tenants 
        SET status = $1, updated_at = NOW()
        WHERE id = $2
        RETURNING id
        """
        
        async with self.get_connection() as conn:
            result = await conn.fetchrow(query, status, tenant_id)
            if result:
                logger.info(f"Updated tenant {tenant_id} status to {status}")
                return True
            return False
    
    # Document Operations with Tenant Isolation
    
    async def create_document(self, document: Document) -> str:
        """Create document with tenant validation."""
        # Validate tenant exists
        tenant = await self.get_tenant(document.tenant_id)
        if not tenant:
            raise ValueError(f"Invalid tenant: {document.tenant_id}")
        
        # Check document limit
        doc_count = await self.count_documents(document.tenant_id)
        if doc_count >= tenant.max_documents:
            raise ValueError(f"Document limit exceeded for tenant {document.tenant_id}")
        
        document_id = document.id or f"doc_{uuid.uuid4().hex[:16]}"
        
        query = """
        INSERT INTO documents (id, tenant_id, title, source, content, metadata)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING created_at
        """
        
        async with self.get_connection() as conn:
            await conn.fetchrow(
                query,
                document_id,
                document.tenant_id,
                document.title,
                document.source,
                document.content,
                json.dumps(document.metadata)
            )
            
        logger.info(f"Created document {document_id} for tenant {document.tenant_id}")
        return document_id
    
    async def get_document(self, document_id: str, tenant_id: str) -> Optional[Document]:
        """Get document with tenant validation."""
        query = """
        SELECT d.*, 
               (SELECT COUNT(*) FROM chunks c WHERE c.document_id = d.id AND c.tenant_id = $2) as chunk_count
        FROM documents d
        WHERE d.id = $1 AND d.tenant_id = $2
        """
        
        async with self.get_connection() as conn:
            result = await conn.fetchrow(query, document_id, tenant_id)
            if result:
                doc_dict = dict(result)
                doc_dict['metadata'] = json.loads(doc_dict.get('metadata', '{}'))
                return Document(**doc_dict)
            return None
    
    async def list_documents(self, tenant_id: str, limit: int = 50, offset: int = 0) -> List[Document]:
        """List documents for specific tenant."""
        query = """
        SELECT d.*,
               COUNT(c.id) as chunk_count
        FROM documents d
        LEFT JOIN chunks c ON d.id = c.document_id AND c.tenant_id = $1
        WHERE d.tenant_id = $1
        GROUP BY d.id, d.tenant_id, d.title, d.source, d.content, d.metadata, d.created_at, d.updated_at
        ORDER BY d.updated_at DESC
        LIMIT $2 OFFSET $3
        """
        
        async with self.get_connection() as conn:
            results = await conn.fetch(query, tenant_id, limit, offset)
            documents = []
            for result in results:
                doc_dict = dict(result)
                doc_dict['metadata'] = json.loads(doc_dict.get('metadata', '{}'))
                documents.append(Document(**doc_dict))
            return documents
    
    async def count_documents(self, tenant_id: str) -> int:
        """Count documents for tenant."""
        query = "SELECT COUNT(*) FROM documents WHERE tenant_id = $1"
        
        async with self.get_connection() as conn:
            result = await conn.fetchval(query, tenant_id)
            return result
    
    # Chunk Operations with Vector Search
    
    async def create_chunks(self, chunks: List[Chunk]) -> List[str]:
        """Batch create chunks with tenant validation."""
        if not chunks:
            return []
        
        # Validate all chunks belong to same tenant
        tenant_id = chunks[0].tenant_id
        if not all(chunk.tenant_id == tenant_id for chunk in chunks):
            raise ValueError("All chunks must belong to same tenant")
        
        # Validate tenant exists
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Invalid tenant: {tenant_id}")
        
        chunk_ids = []
        query = """
        INSERT INTO chunks (id, tenant_id, document_id, content, embedding, chunk_index, token_count, metadata)
        VALUES ($1, $2, $3, $4, $5::vector, $6, $7, $8)
        RETURNING id
        """
        
        async with self.get_connection() as conn:
            async with conn.transaction():
                for chunk in chunks:
                    chunk_id = chunk.id or f"chunk_{uuid.uuid4().hex[:16]}"
                    
                    await conn.fetchrow(
                        query,
                        chunk_id,
                        chunk.tenant_id,
                        chunk.document_id,
                        chunk.content,
                        chunk.embedding,
                        chunk.chunk_index,
                        chunk.token_count,
                        json.dumps(chunk.metadata)
                    )
                    
                    chunk_ids.append(chunk_id)
        
        logger.info(f"Created {len(chunk_ids)} chunks for tenant {tenant_id}")
        return chunk_ids
    
    async def vector_search(
        self,
        embedding: List[float],
        tenant_id: str,
        threshold: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Vector similarity search with tenant isolation."""
        query = "SELECT * FROM match_chunks_tenant($1::vector, $2, $3, $4)"
        
        async with self.get_connection() as conn:
            results = await conn.fetch(query, embedding, tenant_id, threshold, limit)
            
            search_results = []
            for result in results:
                result_dict = dict(result)
                result_dict['metadata'] = json.loads(result_dict.get('metadata', '{}'))
                search_results.append(result_dict)
            
            logger.debug(f"Vector search for tenant {tenant_id}: {len(search_results)} results")
            return search_results
    
    async def hybrid_search(
        self,
        embedding: List[float],
        query_text: str,
        tenant_id: str,
        threshold: float = 0.7,
        limit: int = 10,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Hybrid vector + text search with tenant isolation."""
        query = "SELECT * FROM hybrid_search_chunks_tenant($1::vector, $2, $3, $4, $5, $6)"
        
        async with self.get_connection() as conn:
            results = await conn.fetch(
                query, embedding, query_text, tenant_id, threshold, limit, vector_weight
            )
            
            search_results = []
            for result in results:
                result_dict = dict(result)
                result_dict['metadata'] = json.loads(result_dict.get('metadata', '{}'))
                search_results.append(result_dict)
            
            logger.debug(f"Hybrid search for tenant {tenant_id}: {len(search_results)} results")
            return search_results
    
    # Session Management
    
    async def create_session(
        self,
        tenant_id: str,
        user_id: str,
        timeout_minutes: int = 120,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create session with tenant association."""
        # Validate tenant
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Invalid tenant: {tenant_id}")
        
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)
        
        query = """
        INSERT INTO sessions (id, tenant_id, user_id, expires_at, metadata)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """
        
        async with self.get_connection() as conn:
            result = await conn.fetchrow(
                query,
                session_id,
                tenant_id,
                user_id,
                expires_at,
                json.dumps(metadata or {})
            )
            
        logger.info(f"Created session {session_id} for tenant {tenant_id}, user {user_id}")
        return result['id']
    
    async def get_session(self, session_id: str) -> Optional[TenantSession]:
        """Get active session with tenant information."""
        query = """
        SELECT s.*, t.name as tenant_name
        FROM sessions s
        INNER JOIN tenants t ON s.tenant_id = t.id
        WHERE s.id = $1 AND s.expires_at > NOW() AND t.status = 'active'
        """
        
        async with self.get_connection() as conn:
            result = await conn.fetchrow(query, session_id)
            if result:
                session_dict = dict(result)
                session_dict['metadata'] = json.loads(session_dict.get('metadata', '{}'))
                return TenantSession(**session_dict)
            return None
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions."""
        query = "DELETE FROM sessions WHERE expires_at <= NOW()"
        
        async with self.get_connection() as conn:
            result = await conn.execute(query)
            count = int(result.split()[-1])  # Extract count from "DELETE X"
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            return count
    
    # Tenant Resource Management
    
    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get resource usage statistics for tenant."""
        queries = {
            'documents': "SELECT COUNT(*) FROM documents WHERE tenant_id = $1",
            'chunks': "SELECT COUNT(*) FROM chunks WHERE tenant_id = $1", 
            'active_sessions': "SELECT COUNT(*) FROM sessions WHERE tenant_id = $1 AND expires_at > NOW()",
            'storage_mb': """
                SELECT ROUND(
                    (SUM(LENGTH(d.content)) + SUM(LENGTH(c.content))) / 1024.0 / 1024.0, 2
                ) 
                FROM documents d 
                LEFT JOIN chunks c ON d.id = c.document_id AND c.tenant_id = $1
                WHERE d.tenant_id = $1
            """
        }
        
        usage = {}
        async with self.get_connection() as conn:
            for metric, query in queries.items():
                result = await conn.fetchval(query, tenant_id)
                usage[metric] = result or 0
        
        return usage


# Usage Example and Testing
async def example_usage():
    """Example usage of NeonTenantManager."""
    # Initialize with Neon connection string
    neon_url = "postgresql://username:password@ep-cool-math-123456.us-east-1.aws.neon.tech/neondb?sslmode=require"
    
    manager = NeonTenantManager(neon_url)
    await manager.initialize()
    
    try:
        # Create tenant
        tenant = await manager.create_tenant("client_demo", "Demo Client Corp")
        print(f"Created tenant: {tenant.id}")
        
        # Create document
        document = Document(
            tenant_id=tenant.id,
            title="Project Requirements",
            source="requirements.md",
            content="This is a sample project requirements document with important details..."
        )
        doc_id = await manager.create_document(document)
        print(f"Created document: {doc_id}")
        
        # Create chunks with embeddings
        chunks = [
            Chunk(
                tenant_id=tenant.id,
                document_id=doc_id,
                content="Project requirements overview section...",
                embedding=[0.1] * 768,  # Mock embedding
                chunk_index=0,
                token_count=50
            ),
            Chunk(
                tenant_id=tenant.id,
                document_id=doc_id,
                content="Technical specifications and constraints...",
                embedding=[0.2] * 768,  # Mock embedding
                chunk_index=1,
                token_count=75
            )
        ]
        
        chunk_ids = await manager.create_chunks(chunks)
        print(f"Created chunks: {len(chunk_ids)}")
        
        # Perform vector search
        query_embedding = [0.15] * 768  # Mock query embedding
        results = await manager.vector_search(query_embedding, tenant.id, threshold=0.5, limit=5)
        print(f"Vector search results: {len(results)}")
        
        # Get tenant usage
        usage = await manager.get_tenant_usage(tenant.id)
        print(f"Tenant usage: {usage}")
        
    finally:
        await manager.close()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())