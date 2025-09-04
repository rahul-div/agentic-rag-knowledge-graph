#!/usr/bin/env python3
"""
REAL Multi-Tenant Test Script
Tests with actual validated Phase 1 & 2 components to create:
- REAL Neon projects (visible in Neon UI)
- REAL document ingestion into Neo4j (new nodes in your graph)
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import your REAL validated components
try:
    from tenant_manager import TenantManager, TenantCreateRequest
    from tenant_graphiti_client import TenantGraphitiClient
    from multi_tenant_agent import MultiTenantRAGAgent, TenantContext

    # Import Document from the correct location
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from agent.models import Document
    from dotenv import load_dotenv
    import os
except ImportError as e:
    print(f"Error importing real components: {e}")
    print("Make sure all Phase 1 & 2 components are available")
    sys.exit(1)

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealComponentTester:
    """Test with actual validated components to create real resources."""

    def __init__(self):
        self.tenant_manager = None
        self.graphiti_client = None
        self.rag_agent = None
        self.created_tenants = []

    async def initialize_real_components(self):
        """Initialize the real validated components."""
        print("🔧 Initializing REAL validated components...")

        try:
            # Initialize TenantManager with real Neon API
            self.tenant_manager = TenantManager(
                neon_api_key=os.getenv("NEON_API_KEY"),
                catalog_db_url=os.getenv("CATALOG_DATABASE_URL"),
                default_region=os.getenv("NEON_DEFAULT_REGION", "aws-us-east-1"),
            )
            print("✅ Real TenantManager initialized")

            # Initialize TenantGraphitiClient with real Neo4j
            self.graphiti_client = TenantGraphitiClient(
                neo4j_uri=os.getenv("NEO4J_URI"),
                neo4j_user=os.getenv("NEO4J_USER"),  # Fixed: was NEO4J_USERNAME
                neo4j_password=os.getenv("NEO4J_PASSWORD"),
            )
            await self.graphiti_client.initialize()
            print("✅ Real TenantGraphitiClient initialized")

            # Initialize MultiTenantRAGAgent
            self.rag_agent = MultiTenantRAGAgent(
                tenant_manager=self.tenant_manager,
                graphiti_client=self.graphiti_client,
                model_name=os.getenv(
                    "MODEL_CHOICE", "gemini-2.0-flash-thinking-exp-1219"
                ),
            )
            print("✅ Real MultiTenantRAGAgent initialized")

            return True

        except Exception as e:
            print(f"❌ Failed to initialize real components: {e}")
            return False

    async def create_real_tenant(self, name: str, email: str) -> bool:
        """Create a REAL tenant that will appear in Neon UI."""
        print(f"\n🏢 Creating REAL tenant: {name}")

        try:
            # Create tenant request object
            request = TenantCreateRequest(
                name=name,
                email=email,
                region="aws-us-east-1",  # Use your region
                plan="basic",
                max_documents=100,
                max_storage_mb=50,
            )

            # This will create an ACTUAL Neon project via API
            tenant = await self.tenant_manager.create_tenant(request)

            if tenant:
                print(f"✅ REAL tenant created!")
                print(f"   Tenant ID: {tenant.tenant_id}")
                print(f"   Neon Project ID: {tenant.neon_project_id}")
                print(f"   Database URL: {tenant.database_url[:50]}...")
                print(f"   Status: {tenant.status}")

                self.created_tenants.append(
                    {
                        "tenant_id": str(tenant.tenant_id),
                        "name": tenant.tenant_name,
                        "neon_project_id": tenant.neon_project_id,
                        "database_url": tenant.database_url,
                    }
                )

                return True
            else:
                print(f"❌ Failed to retrieve created tenant")
                return False

        except Exception as e:
            print(f"❌ Failed to create real tenant: {e}")
            return False

    async def ingest_real_documents(self, tenant_id: str, tenant_name: str):
        """Ingest REAL documents that will create actual nodes in Neo4j."""
        print(f"\n📄 Ingesting REAL documents for {tenant_name}...")

        # Real documents that will create actual knowledge graph nodes
        real_documents = [
            Document(
                title="Company AI Strategy 2025",
                source="strategy_doc.md",
                content="""Our artificial intelligence strategy for 2025 focuses on three key areas:

1. Machine Learning Infrastructure: We're building a robust ML platform using TensorFlow and PyTorch frameworks. Our data scientists work with GPUs and cloud computing resources to train large language models and computer vision systems.

2. Natural Language Processing: We're developing conversational AI agents that can understand customer queries, provide technical support, and automate content generation. These systems use transformer architectures and attention mechanisms.

3. Business Intelligence: AI-powered analytics help us understand customer behavior, predict market trends, and optimize operational efficiency. We use neural networks for recommendation systems and predictive modeling.""",
                metadata={
                    "department": "Technology",
                    "document_type": "strategy",
                    "confidentiality": "internal",
                    "author": "CTO Office",
                },
            ),
            Document(
                title="Product Development Roadmap Q1-Q3 2025",
                source="product_roadmap.md",
                content="""Product Development Roadmap for 2025:

Q1 Goals (January-March):
- Launch AI-powered customer service chatbot
- Implement real-time analytics dashboard
- Deploy automated testing framework
- Release mobile application beta version

Q2 Goals (April-June): 
- Introduce machine learning recommendation engine
- Launch multi-tenant SaaS platform
- Implement advanced security features
- Scale infrastructure to support 10,000 users

Q3 Goals (July-September):
- Deploy computer vision quality control system
- Launch enterprise API marketplace
- Implement blockchain payment system
- Achieve SOC2 Type II compliance certification

Key Technologies: React, Node.js, PostgreSQL, Neo4j, Docker, Kubernetes, AWS""",
                metadata={
                    "department": "Product",
                    "document_type": "roadmap",
                    "quarter": "Q1-Q3",
                    "stakeholders": ["Engineering", "Product", "Security"],
                },
            ),
        ]

        ingested_count = 0
        for document in real_documents:
            try:
                # Create run context for the agent
                class RunContext:
                    def __init__(self, tenant_id):
                        self.tenant_id = tenant_id

                run_context = RunContext(tenant_id)

                # This will create REAL nodes in your Neo4j database
                result = await self.rag_agent.ingest_document(
                    run_context=run_context, document=document
                )

                print(f"✅ Ingested: {document.title}")
                print(f"   Document ID: {document.id}")
                print(f"   Content length: {len(document.content)} characters")
                print(f"   Metadata: {document.metadata}")

                ingested_count += 1

            except Exception as e:
                print(f"❌ Failed to ingest {document.title}: {e}")

        print(f"\n📊 Ingested {ingested_count}/{len(real_documents)} documents")
        return ingested_count > 0

    async def query_real_system(self, tenant_id: str, tenant_name: str):
        """Query the real system to verify data ingestion."""
        print(f"\n🔍 Querying REAL system for {tenant_name}...")

        test_queries = [
            "What is our AI strategy?",
            "Tell me about the product roadmap",
            "What technologies do we use?",
            "When is the chatbot launch planned?",
        ]

        for query in test_queries:
            try:
                tenant_context = TenantContext(
                    tenant_id=tenant_id,
                    user_id="test_user",
                    permissions=["read", "write"],
                )

                # This will query actual data from Neo4j and PostgreSQL
                result = await self.rag_agent.query(
                    tenant_context=tenant_context, query=query
                )

                print(f"✅ Query: '{query}'")
                print(f"   Response: {result['response'][:150]}...")
                print(f"   Tenant: {result['tenant_id']}")
                print()

            except Exception as e:
                print(f"❌ Query failed: {e}")

    async def check_real_graph_data(self):
        """Check what was actually added to Neo4j."""
        print("\n🕸️ Checking REAL graph data in Neo4j...")

        try:
            # Query for tenant namespaces that were actually created
            for tenant in self.created_tenants:
                tenant_id = tenant["tenant_id"]
                tenant_name = tenant["name"]

                # Get real statistics from the graph
                stats = await self.rag_agent.get_tenant_stats(tenant_id)

                print(f"📊 Real stats for {tenant_name}:")
                print(f"   Tenant ID: {tenant_id}")
                print(f"   Documents: {stats.get('documents', 0)}")
                print(f"   Chunks: {stats.get('chunks', 0)}")
                print(f"   Graph Entities: {stats.get('graph_entities', 0)}")
                print(f"   Graph Relationships: {stats.get('graph_relationships', 0)}")
                print()

        except Exception as e:
            print(f"❌ Failed to check graph data: {e}")

    async def cleanup(self):
        """Clean up connections."""
        if self.tenant_manager:
            await self.tenant_manager.close()
        if self.graphiti_client:
            await self.graphiti_client.close()
        print("🔄 Cleanup completed")

    async def run_real_test(self):
        """Run the complete real component test."""
        print("""
        ╔══════════════════════════════════════════════════════════════╗
        ║              REAL Multi-Tenant Component Test                ║
        ║                                                              ║
        ║   This will create ACTUAL resources:                        ║
        ║   • Real Neon projects (visible in Neon UI)                 ║
        ║   • Real documents in Neo4j (new nodes in your graph)       ║
        ║                                                              ║
        ║   ⚠️  WARNING: This uses your actual API quotas!            ║
        ╚══════════════════════════════════════════════════════════════╝
        """)

        # Confirm before proceeding
        response = input("Do you want to proceed with REAL resource creation? (y/N): ")
        if response.lower() != "y":
            print("Test cancelled.")
            return

        try:
            # Initialize real components
            if not await self.initialize_real_components():
                print("❌ Failed to initialize components. Exiting.")
                return

            # Create ONE real tenant for testing
            success = await self.create_real_tenant(
                name="RealTestCorp", email="test@realtestcorp.com"
            )

            if not success:
                print("❌ Failed to create real tenant. Exiting.")
                return

            # Use the first created tenant
            tenant_data = self.created_tenants[0]
            tenant_id = tenant_data["tenant_id"]
            tenant_name = tenant_data["name"]

            # Ingest real documents
            if await self.ingest_real_documents(tenant_id, tenant_name):
                # Query the system
                await self.query_real_system(tenant_id, tenant_name)

                # Check what was actually created
                await self.check_real_graph_data()

                print("\n✅ REAL COMPONENT TEST COMPLETED!")
                print(
                    f"🎯 Check your Neon UI for project: {tenant_data['neon_project_id']}"
                )
                print(
                    f"🕸️ Check your Neo4j for new tenant namespace: tenant_{tenant_id[:8]}"
                )
                print(f"📊 Real documents and entities have been created!")

        except Exception as e:
            print(f"❌ Real test failed: {e}")
            import traceback

            traceback.print_exc()

        finally:
            await self.cleanup()


async def main():
    """Main entry point for real component testing."""
    tester = RealComponentTester()
    await tester.run_real_test()


if __name__ == "__main__":
    asyncio.run(main())
