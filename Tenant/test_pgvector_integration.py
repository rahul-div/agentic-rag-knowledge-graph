#!/usr/bin/env python3
"""
Test script to validate pgvector functionality in multi-tenant system.
This script tests the complete pipeline from document ingestion to vector search.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

from tenant_manager import TenantManager, TenantCreateRequest

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_pgvector_multi_tenant():
    """Test the complete pgvector functionality in multi-tenant system"""

    logger.info("🧪 Starting pgvector multi-tenant test")

    # Initialize tenant manager
    tenant_manager = TenantManager(
        neon_api_key=os.getenv("NEON_API_KEY"),
        catalog_db_url=os.getenv("CATALOG_DATABASE_URL"),
        neo4j_uri=os.getenv("NEO4J_URI"),
        neo4j_user=os.getenv("NEO4J_USER"),
        neo4j_password=os.getenv("NEO4J_PASSWORD"),
    )

    try:
        await tenant_manager._ensure_initialized()
        logger.info("✅ Tenant manager initialized")

        # Test 1: Create a test tenant
        test_tenant_name = (
            f"pgvector_test_tenant_{int(asyncio.get_event_loop().time())}"
        )

        create_request = TenantCreateRequest(
            name=test_tenant_name,
            email=f"{test_tenant_name}@example.com",
            region="aws-us-east-1",
        )

        logger.info(f"🔄 Creating test tenant: {test_tenant_name}")
        tenant_info = await tenant_manager.create_tenant(create_request)
        tenant_id = str(tenant_info.tenant_id)
        logger.info(f"✅ Created tenant: {tenant_id}")

        # Test 2: Validate schema has pgvector support
        logger.info("🔄 Validating database schema...")
        schema_validation = (
            await tenant_manager.schema_initializer.validate_tenant_schema(
                tenant_info.database_url
            )
        )

        if schema_validation["valid"]:
            logger.info("✅ Schema validation passed")
            logger.info(f"   - Extensions: {schema_validation['existing_extensions']}")
            logger.info(f"   - Functions: {schema_validation['existing_functions']}")
        else:
            logger.error(f"❌ Schema validation failed: {schema_validation}")
            return False

        # Test 3: Ingest test documents with embeddings
        test_documents = [
            {
                "title": "AI Technology Overview",
                "source": "ai_tech.md",
                "content": """
                Artificial Intelligence (AI) has revolutionized many industries through machine learning,
                neural networks, and deep learning technologies. Google's AI initiatives include 
                advanced language models like Gemini, computer vision systems, and natural language 
                processing capabilities. These technologies are transforming how we interact with computers.
                """,
                "metadata": {"category": "technology", "topic": "ai"},
            },
            {
                "title": "Cloud Computing Fundamentals",
                "source": "cloud_fundamentals.md",
                "content": """
                Cloud computing provides on-demand access to computing resources including servers,
                storage, databases, and applications. Major cloud providers like AWS, Google Cloud,
                and Microsoft Azure offer scalable infrastructure services. Container technologies
                like Docker and Kubernetes enable efficient application deployment and management.
                """,
                "metadata": {"category": "technology", "topic": "cloud"},
            },
            {
                "title": "Database Technologies",
                "source": "databases.md",
                "content": """
                Modern database technologies include relational databases like PostgreSQL,
                NoSQL databases like MongoDB, and vector databases for AI applications.
                PostgreSQL with pgvector extension enables vector similarity search for
                machine learning embeddings. This is crucial for RAG systems and semantic search.
                """,
                "metadata": {"category": "technology", "topic": "databases"},
            },
        ]

        ingested_docs = []
        for doc in test_documents:
            logger.info(f"🔄 Ingesting document: {doc['title']}")

            doc_id = await tenant_manager.ingest_document_with_embeddings(
                tenant_id=tenant_id,
                title=doc["title"],
                source=doc["source"],
                content=doc["content"],
                metadata=doc["metadata"],
            )

            ingested_docs.append(doc_id)
            logger.info(f"✅ Ingested document: {doc_id}")

        # Test 4: Test vector search
        test_queries = [
            "artificial intelligence machine learning",
            "cloud computing infrastructure",
            "PostgreSQL vector database",
            "Google AI technology",
        ]

        for query in test_queries:
            logger.info(f"🔄 Testing vector search for: '{query}'")

            # Test vector search
            vector_results = await tenant_manager.search_documents_with_embeddings(
                tenant_id=tenant_id, query=query, limit=5, search_type="vector"
            )

            logger.info(f"   📊 Vector search results: {len(vector_results)}")
            for i, result in enumerate(vector_results[:2]):
                logger.info(
                    f"     {i + 1}. Similarity: {result.get('similarity', 0):.3f}"
                )
                logger.info(f"        Content: {result['content'][:100]}...")

            # Test hybrid search
            hybrid_results = await tenant_manager.search_documents_with_embeddings(
                tenant_id=tenant_id, query=query, limit=5, search_type="hybrid"
            )

            logger.info(f"   📊 Hybrid search results: {len(hybrid_results)}")
            for i, result in enumerate(hybrid_results[:2]):
                combined_score = result.get("combined_score", 0)
                vector_score = result.get("vector_score", 0)
                text_score = result.get("text_score", 0)
                logger.info(
                    f"     {i + 1}. Combined: {combined_score:.3f} (V:{vector_score:.3f}, T:{text_score:.3f})"
                )

        # Test 5: Direct pgvector functionality test
        logger.info("🔄 Testing direct pgvector functionality...")

        import asyncpg

        conn = await asyncpg.connect(tenant_info.database_url)

        try:
            # Test vector extension
            extensions = await conn.fetch(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            if extensions:
                logger.info("✅ pgvector extension is installed")
            else:
                logger.error("❌ pgvector extension not found")
                return False

            # Test vector similarity query
            test_embedding = [0.1] * 768  # Test embedding
            embedding_str = "[" + ",".join(map(str, test_embedding)) + "]"

            results = await conn.fetch(
                """
                SELECT c.id, c.content, 1 - (c.embedding <=> $1::vector) as similarity
                FROM chunks c 
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> $1::vector
                LIMIT 3
                """,
                embedding_str,
            )

            logger.info(
                f"✅ Direct vector similarity query returned {len(results)} results"
            )

            # Test match_chunks function
            function_results = await conn.fetch(
                "SELECT * FROM match_chunks($1::vector, 0.0, 3)", embedding_str
            )

            logger.info(
                f"✅ match_chunks function returned {len(function_results)} results"
            )

        finally:
            await conn.close()

        # Test 6: Performance test
        logger.info("🔄 Running performance test...")

        import time

        start_time = time.time()

        performance_results = await tenant_manager.search_documents_with_embeddings(
            tenant_id=tenant_id,
            query="machine learning artificial intelligence",
            limit=10,
            search_type="hybrid",
        )

        search_time = time.time() - start_time
        logger.info(
            f"✅ Performance test: {len(performance_results)} results in {search_time:.3f}s"
        )

        # Test 7: Cleanup
        logger.info(f"🔄 Cleaning up test tenant: {tenant_id}")
        await tenant_manager.delete_tenant(tenant_id)
        logger.info("✅ Test tenant deleted")

        logger.info("🎉 All pgvector tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await tenant_manager.close()


async def test_schema_migration():
    """Test schema migration to enable pgvector on existing tenants"""

    logger.info("🧪 Testing schema migration for pgvector")

    tenant_manager = TenantManager(
        neon_api_key=os.getenv("NEON_API_KEY"),
        catalog_db_url=os.getenv("CATALOG_DATABASE_URL"),
    )

    try:
        await tenant_manager._ensure_initialized()

        # Get all existing tenants
        tenants = await tenant_manager.list_tenants()
        logger.info(f"Found {len(tenants)} existing tenants")

        for tenant in tenants[:2]:  # Test first 2 tenants only
            tenant_id = str(tenant.tenant_id)
            logger.info(f"🔄 Testing schema migration for tenant: {tenant_id}")

            # Check current schema
            validation = await tenant_manager.schema_initializer.validate_tenant_schema(
                tenant.database_url
            )

            logger.info(
                f"   Current schema version: {validation.get('schema_version')}"
            )
            logger.info(
                f"   Has vector extension: {'vector' in validation.get('existing_extensions', [])}"
            )

            # If schema needs update, reinitialize
            if not validation.get("valid") or "vector" not in validation.get(
                "existing_extensions", []
            ):
                logger.info(f"   🔄 Updating schema for tenant {tenant_id}")

                success = (
                    await tenant_manager.schema_initializer.initialize_tenant_database(
                        tenant.database_url
                    )
                )

                if success:
                    logger.info(f"   ✅ Schema updated for tenant {tenant_id}")
                else:
                    logger.error(f"   ❌ Schema update failed for tenant {tenant_id}")
            else:
                logger.info(f"   ✅ Schema already up to date for tenant {tenant_id}")

    finally:
        await tenant_manager.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        asyncio.run(test_schema_migration())
    else:
        asyncio.run(test_pgvector_multi_tenant())
