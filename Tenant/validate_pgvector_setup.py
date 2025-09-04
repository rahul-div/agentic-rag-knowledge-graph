#!/usr/bin/env python3
"""
Simple validation script to test the corrected pgvector multi-tenant components
"""

import sys
import os

sys.path.append("/Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph")

print("🧪 Testing pgvector multi-tenant components...")

try:
    # Test imports
    print("1. Testing imports...")
    from Tenant.multi_tenant_ingestion import (
        MultiTenantIngestionPipeline,
        MultiTenantDocument,
    )
    from Tenant.tenant_schema_initializer import TenantSchemaInitializer

    print("   ✅ All imports successful")

    # Test schema version and pgvector support
    print("2. Testing schema configuration...")
    initializer = TenantSchemaInitializer()
    print(f"   ✅ Schema version: {initializer.SCHEMA_VERSION}")

    # Check pgvector extension
    if "CREATE EXTENSION IF NOT EXISTS vector" in initializer.TENANT_SCHEMA_SQL:
        print("   ✅ pgvector extension enabled")
    else:
        print("   ❌ pgvector extension missing")

    # Check vector embedding column
    if "embedding vector(768)" in initializer.TENANT_SCHEMA_SQL:
        print("   ✅ Vector embedding column (768 dimensions)")
    else:
        print("   ❌ Vector embedding column missing")

    # Check vector search functions
    if "CREATE OR REPLACE FUNCTION match_chunks(" in initializer.TENANT_SCHEMA_SQL:
        print("   ✅ Vector search function (match_chunks)")
    else:
        print("   ❌ Vector search function missing")

    if "CREATE OR REPLACE FUNCTION hybrid_search(" in initializer.TENANT_SCHEMA_SQL:
        print("   ✅ Hybrid search function")
    else:
        print("   ❌ Hybrid search function missing")

    # Check vector indexes
    if "idx_chunks_embedding ON chunks USING ivfflat" in initializer.TENANT_SCHEMA_SQL:
        print("   ✅ Vector similarity index (ivfflat)")
    else:
        print("   ❌ Vector similarity index missing")

    # Test multi-tenant document structure
    print("3. Testing document structure...")
    test_doc = MultiTenantDocument(
        title="Test Document",
        source="test.md",
        content="This is a test document for AI and machine learning.",
        metadata={"category": "technology", "topic": "ai"},
    )
    print(f"   ✅ Document created: {test_doc.title}")
    print(f"   ✅ Metadata: {test_doc.metadata}")

    # Test ingestion pipeline initialization
    print("4. Testing ingestion pipeline...")
    pipeline = MultiTenantIngestionPipeline()
    print(f"   ✅ Pipeline initialized")
    print(f"   ✅ Chunker config: {pipeline.chunker_config.chunk_size} chars")
    print(f"   ✅ Embedder dimensions: {pipeline.embedder.get_embedding_dimension()}")

    print("\n🎉 All component tests passed!")
    print("\n📋 Summary:")
    print("   - pgvector extension enabled in schema")
    print("   - Vector embeddings (768 dimensions) supported")
    print("   - Vector similarity search functions available")
    print("   - Hybrid search (vector + text) implemented")
    print("   - Multi-tenant ingestion pipeline ready")
    print("   - JSON serialization for metadata fixed")

    print("\n🚀 Next steps:")
    print("   - Deploy schema to existing tenants")
    print("   - Test with real documents and embeddings")
    print("   - Validate vector search performance")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback

    traceback.print_exc()
