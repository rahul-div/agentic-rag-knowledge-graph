"""
Multi-Tenant Manager for Neon PostgreSQL with Row-Level Security
Based on official Neon multi-tenancy patterns and best practices.
"""

import asyncio
import asyncpg
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from contextlib import asynccontextmanager
import json

logger = logging.getLogger(__name__)


@dataclass
class Tenant:
    """Tenant model with validation and metadata."""

    id: str
    name: str
    email: str
    status: str = "active"
    max_documents: int = 1000
    max_storage_mb: int = 500
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.id:
            self.id = f"tenant_{uuid.uuid4().hex[:8]}"


@dataclass
class Document:
    """Document model with tenant isolation."""

    tenant_id: str
    title: str
    source: str
    content: str
    id: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class Chunk:
    """Chunk model with vector embeddings and tenant isolation."""

    tenant_id: str
    document_id: str
    content: str
    chunk_index: int
    id: Optional[str] = None
    embedding: Optional[List[float]] = None
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.id:
            self.id = str(uuid.uuid4())


class TenantManager:
    """
    Multi-tenant manager for Neon PostgreSQL with Row-Level Security.

    Provides complete tenant isolation using RLS policies and tenant-aware queries.
    Based on official Neon documentation patterns.
    """

    def __init__(self, connection_string: str, pool_size: int = 10):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """Initialize connection pool and verify schema."""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=self.pool_size,
                command_timeout=60,
            )

            # Verify schema exists
            async with self.pool.acquire() as conn:
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('tenants', 'documents', 'chunks', 'sessions', 'messages')
                """)

                required_tables = {
                    "tenants",
                    "documents",
                    "chunks",
                    "sessions",
                    "messages",
                }
                existing_tables = {row["table_name"] for row in tables}

                if not required_tables.issubset(existing_tables):
                    missing = required_tables - existing_tables
                    raise Exception(
                        f"Missing required tables: {missing}. Please run schema.sql first."
                    )

            logger.info("TenantManager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize TenantManager: {e}")
            raise

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def get_connection(self, tenant_id: Optional[str] = None):
        """Get database connection with optional tenant context."""
        if not self.pool:
            raise Exception("TenantManager not initialized. Call initialize() first.")

        async with self.pool.acquire() as conn:
            if tenant_id:
                # Set tenant context for RLS
                await conn.execute("SELECT set_tenant_context($1)", tenant_id)

            try:
                yield conn
            finally:
                # Clear tenant context
                if tenant_id:
                    await conn.execute(
                        "SELECT set_config('app.current_tenant_id', '', true)"
                    )

    # Tenant Management Methods

    async def create_tenant(
        self,
        tenant_id: str,
        name: str,
        email: str,
        max_documents: int = 1000,
        max_storage_mb: int = 500,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tenant:
        """Create a new tenant with validation."""
        try:
            if metadata is None:
                metadata = {}

            async with self.get_connection() as conn:
                # Check if tenant already exists
                existing = await conn.fetchrow(
                    "SELECT id FROM tenants WHERE id = $1 OR email = $2",
                    tenant_id,
                    email,
                )

                if existing:
                    raise ValueError(
                        f"Tenant with ID '{tenant_id}' or email '{email}' already exists"
                    )

                # Create tenant
                row = await conn.fetchrow(
                    """
                    INSERT INTO tenants (id, name, email, max_documents, max_storage_mb, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING *
                """,
                    tenant_id,
                    name,
                    email,
                    max_documents,
                    max_storage_mb,
                    json.dumps(metadata),
                )

                tenant = Tenant(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    status=row["status"],
                    max_documents=row["max_documents"],
                    max_storage_mb=row["max_storage_mb"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

                logger.info(f"Created tenant: {tenant_id}")
                return tenant

        except Exception as e:
            logger.error(f"Failed to create tenant {tenant_id}: {e}")
            raise

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM tenants WHERE id = $1", tenant_id
                )

                if not row:
                    return None

                return Tenant(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    status=row["status"],
                    max_documents=row["max_documents"],
                    max_storage_mb=row["max_storage_mb"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            return None

    async def list_tenants(self, status: Optional[str] = None) -> List[Tenant]:
        """List all tenants, optionally filtered by status."""
        try:
            async with self.get_connection() as conn:
                if status:
                    rows = await conn.fetch(
                        "SELECT * FROM tenants WHERE status = $1 ORDER BY created_at",
                        status,
                    )
                else:
                    rows = await conn.fetch("SELECT * FROM tenants ORDER BY created_at")

                return [
                    Tenant(
                        id=row["id"],
                        name=row["name"],
                        email=row["email"],
                        status=row["status"],
                        max_documents=row["max_documents"],
                        max_storage_mb=row["max_storage_mb"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to list tenants: {e}")
            return []

    async def delete_tenant(self, tenant_id: str, force: bool = False) -> bool:
        """Delete tenant and all associated data."""
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    # Check if tenant has data
                    if not force:
                        doc_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM documents WHERE tenant_id = $1",
                            tenant_id,
                        )
                        if doc_count > 0:
                            raise ValueError(
                                f"Tenant {tenant_id} has {doc_count} documents. Use force=True to delete."
                            )

                    # Delete in correct order (foreign key constraints)
                    await conn.execute(
                        "DELETE FROM messages WHERE tenant_id = $1", tenant_id
                    )
                    await conn.execute(
                        "DELETE FROM sessions WHERE tenant_id = $1", tenant_id
                    )
                    await conn.execute(
                        "DELETE FROM chunks WHERE tenant_id = $1", tenant_id
                    )
                    await conn.execute(
                        "DELETE FROM documents WHERE tenant_id = $1", tenant_id
                    )
                    await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_id)

                    logger.info(f"Deleted tenant: {tenant_id}")
                    return True

        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {e}")
            return False

    # Document Management Methods

    async def create_document(self, document: Document) -> str:
        """Create a document with tenant isolation."""
        try:
            async with self.get_connection(document.tenant_id) as conn:
                # Verify tenant exists
                tenant_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM tenants WHERE id = $1)",
                    document.tenant_id,
                )
                if not tenant_exists:
                    raise ValueError(f"Tenant {document.tenant_id} does not exist")

                # Insert document (quota checking handled by trigger)
                doc_id = await conn.fetchval(
                    """
                    INSERT INTO documents (id, tenant_id, title, source, content, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                """,
                    document.id,
                    document.tenant_id,
                    document.title,
                    document.source,
                    document.content,
                    json.dumps(document.metadata),
                )

                logger.info(
                    f"Created document {doc_id} for tenant {document.tenant_id}"
                )
                return doc_id

        except Exception as e:
            logger.error(
                f"Failed to create document for tenant {document.tenant_id}: {e}"
            )
            raise

    async def get_document(
        self, tenant_id: str, document_id: str
    ) -> Optional[Document]:
        """Get document by ID with tenant isolation."""
        try:
            async with self.get_connection(tenant_id) as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM documents WHERE id = $1 AND tenant_id = $2",
                    document_id,
                    tenant_id,
                )

                if not row:
                    return None

                return Document(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    title=row["title"],
                    source=row["source"],
                    content=row["content"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

        except Exception as e:
            logger.error(
                f"Failed to get document {document_id} for tenant {tenant_id}: {e}"
            )
            return None

    async def list_documents(
        self, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> List[Document]:
        """List documents for a tenant."""
        try:
            async with self.get_connection(tenant_id) as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM documents 
                    WHERE tenant_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2 OFFSET $3
                """,
                    tenant_id,
                    limit,
                    offset,
                )

                return [
                    Document(
                        id=row["id"],
                        tenant_id=row["tenant_id"],
                        title=row["title"],
                        source=row["source"],
                        content=row["content"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to list documents for tenant {tenant_id}: {e}")
            return []

    # Chunk Management Methods

    async def create_chunks(self, chunks: List[Chunk]) -> List[str]:
        """Create multiple chunks with tenant isolation."""
        if not chunks:
            return []

        tenant_id = chunks[0].tenant_id

        try:
            async with self.get_connection(tenant_id) as conn:
                chunk_ids = []

                async with conn.transaction():
                    for chunk in chunks:
                        if chunk.tenant_id != tenant_id:
                            raise ValueError(
                                "All chunks must belong to the same tenant"
                            )

                        chunk_id = await conn.fetchval(
                            """
                            INSERT INTO chunks (id, tenant_id, document_id, content, embedding, chunk_index, token_count, metadata)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                            RETURNING id
                        """,
                            chunk.id,
                            chunk.tenant_id,
                            chunk.document_id,
                            chunk.content,
                            chunk.embedding,
                            chunk.chunk_index,
                            chunk.token_count,
                            json.dumps(chunk.metadata),
                        )

                        chunk_ids.append(chunk_id)

                logger.info(f"Created {len(chunk_ids)} chunks for tenant {tenant_id}")
                return chunk_ids

        except Exception as e:
            logger.error(f"Failed to create chunks for tenant {tenant_id}: {e}")
            raise

    async def vector_search(
        self,
        tenant_id: str,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Perform tenant-aware vector search."""
        try:
            async with self.get_connection(tenant_id) as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM match_chunks_tenant($1, $2, $3, $4)
                """,
                    query_embedding,
                    tenant_id,
                    threshold,
                    limit,
                )

                return [
                    {
                        "chunk_id": row["chunk_id"],
                        "document_id": row["document_id"],
                        "content": row["content"],
                        "similarity": float(row["similarity"]),
                        "metadata": json.loads(row["metadata"])
                        if row["metadata"]
                        else {},
                        "document_title": row["document_title"],
                        "tenant_id": row["tenant_id"],
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to perform vector search for tenant {tenant_id}: {e}")
            return []

    # Tenant Statistics and Monitoring

    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive tenant statistics."""
        try:
            async with self.get_connection() as conn:
                stats = await conn.fetchrow(
                    """
                    SELECT * FROM tenant_stats WHERE tenant_id = $1
                """,
                    tenant_id,
                )

                if not stats:
                    return {}

                return {
                    "tenant_id": stats["tenant_id"],
                    "tenant_name": stats["tenant_name"],
                    "status": stats["status"],
                    "document_count": stats["document_count"],
                    "chunk_count": stats["chunk_count"],
                    "storage_mb_used": float(stats["storage_mb_used"]),
                    "max_documents": stats["max_documents"],
                    "max_storage_mb": stats["max_storage_mb"],
                    "doc_usage_percent": float(stats["doc_usage_percent"])
                    if stats["doc_usage_percent"]
                    else 0,
                    "storage_usage_percent": float(stats["storage_usage_percent"])
                    if stats["storage_usage_percent"]
                    else 0,
                    "active_sessions": stats["active_sessions"],
                    "tenant_created_at": stats["tenant_created_at"],
                }

        except Exception as e:
            logger.error(f"Failed to get stats for tenant {tenant_id}: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        try:
            async with self.get_connection() as conn:
                # Check database connection
                db_version = await conn.fetchval("SELECT version()")

                # Check tenant count
                tenant_count = await conn.fetchval("SELECT COUNT(*) FROM tenants")

                # Check active tenants
                active_tenants = await conn.fetchval(
                    "SELECT COUNT(*) FROM tenants WHERE status = 'active'"
                )

                # Check total documents
                total_docs = await conn.fetchval("SELECT COUNT(*) FROM documents")

                # Check total chunks
                total_chunks = await conn.fetchval("SELECT COUNT(*) FROM chunks")

                return {
                    "status": "healthy",
                    "database_version": db_version,
                    "tenant_count": tenant_count,
                    "active_tenants": active_tenants,
                    "total_documents": total_docs,
                    "total_chunks": total_chunks,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# Example usage and testing functions
async def example_usage():
    """Example usage of TenantManager."""
    # Initialize manager
    manager = TenantManager("postgresql://user:pass@localhost/db")
    await manager.initialize()

    try:
        # Create tenant
        tenant = await manager.create_tenant(
            tenant_id="demo_corp",
            name="Demo Corporation",
            email="demo@corp.com",
            max_documents=500,
            max_storage_mb=250,
        )
        print(f"Created tenant: {tenant.id}")

        # Create document
        document = Document(
            tenant_id="demo_corp",
            title="Project Requirements",
            source="requirements.md",
            content="This document outlines the project requirements for our new RAG system...",
        )
        doc_id = await manager.create_document(document)
        print(f"Created document: {doc_id}")

        # Get tenant stats
        stats = await manager.get_tenant_stats("demo_corp")
        print(f"Tenant stats: {stats}")

    finally:
        await manager.close()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
