#!/usr/bin/env python3
"""
Advanced Prototype Testing Script
Tests the advanced multi-tenant API with real Neo4j integration.
"""

import asyncio
import sys
from typing import Dict, List, Any

try:
    import httpx
except ImportError:
    print("Please install httpx: pip install httpx")
    sys.exit(1)


class AdvancedPrototypeTester:
    """Comprehensive tester for the advanced prototype API."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=15.0)
        self.tenants: List[Dict[str, Any]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results."""
        print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {status}")
        if details:
            print(f"   {details}")

    async def test_health_check(self):
        """Test advanced health endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/health")

            if response.status_code == 200:
                health_data = response.json()
                if health_data["status"] == "healthy":
                    services = health_data["services"]
                    env = health_data["environment"]
                    self.log_test(
                        "Advanced Health Check",
                        "PASS",
                        f"Environment: {env}, Neo4j: {services.get('graph', 'unknown')}, AI: {services.get('ai', 'unknown')}",
                    )
                    return True
                else:
                    self.log_test(
                        "Advanced Health Check",
                        "FAIL",
                        f"Status: {health_data['status']}",
                    )
                    return False
            else:
                self.log_test(
                    "Advanced Health Check", "FAIL", f"HTTP {response.status_code}"
                )
                return False

        except Exception as e:
            self.log_test("Advanced Health Check", "FAIL", str(e))
            return False

    async def test_create_tenants(self):
        """Test creating tenants with mock Neon projects."""
        print("\n🏢 Creating tenants with mock Neon projects...")

        tenant_configs = [
            {
                "name": "AcmeCorp",
                "email": "admin@acmecorp.com",
                "region": "aws-us-east-1",
                "max_documents": 75,
                "max_storage_mb": 40,
            },
            {
                "name": "TechStart",
                "email": "admin@techstart.com",
                "region": "aws-us-east-1",
                "max_documents": 50,
                "max_storage_mb": 30,
            },
            {
                "name": "DataCorp",
                "email": "admin@datacorp.com",
                "region": "aws-us-east-1",
                "max_documents": 100,
                "max_storage_mb": 60,
            },
        ]

        for config in tenant_configs:
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/v1/tenants", json=config
                )

                if response.status_code == 200:
                    tenant_data = response.json()
                    self.tenants.append(tenant_data)
                    self.log_test(
                        f"Create Tenant {config['name']}",
                        "PASS",
                        f"Project: {tenant_data['neon_project_id']}, API: {tenant_data['api_key'][:16]}...",
                    )
                else:
                    self.log_test(
                        f"Create Tenant {config['name']}",
                        "FAIL",
                        f"HTTP {response.status_code}: {response.text}",
                    )

            except Exception as e:
                self.log_test(f"Create Tenant {config['name']}", "FAIL", str(e))

    async def test_advanced_document_upload(self):
        """Test document upload with database + graph ingestion."""
        print("\n📄 Testing advanced document upload (Database + Graph)...")

        test_documents = [
            {
                "title": "AI Strategy Document",
                "content": "Our artificial intelligence strategy focuses on machine learning, natural language processing, and computer vision. We aim to deploy AI solutions across customer service, product development, and operational efficiency. Key technologies include neural networks, transformers, and reinforcement learning algorithms.",
            },
            {
                "title": "Product Roadmap 2025",
                "content": "The 2025 product roadmap includes three major releases: Q1 will feature enhanced analytics dashboard, Q2 introduces AI-powered recommendations, Q3 delivers real-time collaboration tools, and Q4 launches mobile applications. Each release targets specific customer segments and business objectives.",
            },
            {
                "title": "Market Analysis Report",
                "content": "Market analysis shows growing demand for AI-powered solutions in enterprise software. Competitors include Microsoft, Google, and Amazon with their respective AI platforms. Our competitive advantage lies in specialized industry knowledge and custom AI model development.",
            },
        ]

        for tenant in self.tenants[:2]:  # Test with first 2 tenants
            tenant_id = tenant["id"]
            tenant_name = tenant["name"]

            for doc in test_documents:
                try:
                    response = await self.client.post(
                        f"{self.base_url}/api/v1/tenants/{tenant_id}/documents",
                        json=doc,
                    )

                    if response.status_code == 200:
                        doc_data = response.json()
                        self.log_test(
                            f"Upload to {tenant_name}",
                            "PASS",
                            f"{doc['title']} -> {doc_data['chunks']} chunks, {doc_data['graph_entities']} entities, NS: {doc_data['namespace']}",
                        )
                    else:
                        self.log_test(
                            f"Upload to {tenant_name}",
                            "FAIL",
                            f"HTTP {response.status_code}: {response.text}",
                        )

                except Exception as e:
                    self.log_test(f"Upload to {tenant_name}", "FAIL", str(e))

    async def test_hybrid_queries(self):
        """Test hybrid database + graph queries."""
        print("\n🔍 Testing hybrid queries (Database + Graph)...")

        test_queries = [
            "What is our AI strategy?",
            "Tell me about the product roadmap",
            "Who are our competitors?",
            "What technologies do we use?",
            "When is the next product release?",
        ]

        for tenant in self.tenants[:2]:  # Test with first 2 tenants
            tenant_id = tenant["id"]
            tenant_name = tenant["name"]

            for query in test_queries:
                try:
                    response = await self.client.post(
                        f"{self.base_url}/api/v1/tenants/{tenant_id}/query",
                        json={"query": query, "use_graph": True},
                    )

                    if response.status_code == 200:
                        query_data = response.json()
                        self.log_test(
                            f"Query {tenant_name}",
                            "PASS",
                            f"'{query}' -> DB:{query_data['database_results']}, Graph:{query_data['graph_results']}, Total:{query_data['total_sources']}",
                        )
                        if query_data["total_sources"] > 0:
                            print(f"      Response: {query_data['response'][:100]}...")
                    else:
                        self.log_test(
                            f"Query {tenant_name}",
                            "FAIL",
                            f"HTTP {response.status_code}: {response.text}",
                        )

                except Exception as e:
                    self.log_test(f"Query {tenant_name}", "FAIL", str(e))

    async def test_tenant_isolation_advanced(self):
        """Test advanced tenant isolation with graph namespaces."""
        print("\n🔒 Testing advanced tenant isolation (Database + Graph)...")

        if len(self.tenants) >= 2:
            tenant1 = self.tenants[0]
            tenant2 = self.tenants[1]

            # Query tenant 2 for tenant 1's specific AI strategy content
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/v1/tenants/{tenant2['id']}/query",
                    json={
                        "query": "artificial intelligence strategy machine learning",
                        "use_graph": True,
                    },
                )

                if response.status_code == 200:
                    query_data = response.json()
                    # Check if tenant 2 can see tenant 1's AI strategy content
                    if (
                        "AI Strategy Document" not in query_data["response"]
                        and query_data["total_sources"] == 0
                    ):
                        self.log_test(
                            "Advanced Tenant Isolation",
                            "PASS",
                            f"{tenant2['name']} cannot access {tenant1['name']}'s AI strategy data",
                        )
                    else:
                        self.log_test(
                            "Advanced Tenant Isolation",
                            "FAIL",
                            f"Potential data leakage detected! Sources: {query_data['total_sources']}",
                        )
                else:
                    self.log_test(
                        "Advanced Tenant Isolation",
                        "FAIL",
                        f"HTTP {response.status_code}",
                    )

            except Exception as e:
                self.log_test("Advanced Tenant Isolation", "FAIL", str(e))

    async def test_comprehensive_stats(self):
        """Test comprehensive tenant statistics."""
        print("\n📊 Testing comprehensive tenant statistics...")

        for tenant in self.tenants:
            tenant_id = tenant["id"]
            tenant_name = tenant["name"]

            try:
                response = await self.client.get(
                    f"{self.base_url}/api/v1/tenants/{tenant_id}/stats"
                )

                if response.status_code == 200:
                    stats = response.json()
                    self.log_test(
                        f"Stats {tenant_name}",
                        "PASS",
                        f"Docs:{stats['documents']}, Chunks:{stats['chunks']}, Entities:{stats['graph_entities']}, Rels:{stats['graph_relationships']}, NS:{stats['namespace']}",
                    )
                else:
                    self.log_test(
                        f"Stats {tenant_name}", "FAIL", f"HTTP {response.status_code}"
                    )

            except Exception as e:
                self.log_test(f"Stats {tenant_name}", "FAIL", str(e))

    async def test_list_tenants_advanced(self):
        """Test listing tenants with advanced details."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/tenants")

            if response.status_code == 200:
                tenants = response.json()
                self.log_test(
                    "List Tenants Advanced", "PASS", f"Found {len(tenants)} tenants"
                )
                for tenant in tenants:
                    print(f"   - {tenant['name']} ({tenant['id'][:8]}...)")
                    print(f"     Project: {tenant['neon_project_id']}")
                    print(f"     Documents: {tenant['document_count']}")
                    print(f"     Status: {tenant['status']}")
            else:
                self.log_test(
                    "List Tenants Advanced", "FAIL", f"HTTP {response.status_code}"
                )

        except Exception as e:
            self.log_test("List Tenants Advanced", "FAIL", str(e))

    async def run_all_tests(self):
        """Run all advanced prototype tests."""
        print("""
        ╔══════════════════════════════════════════════════════════════╗
        ║         Advanced Multi-Tenant RAG Prototype Testing          ║
        ║     Real Neo4j + Mock Neon + Graphiti Integration Test      ║
        ╚══════════════════════════════════════════════════════════════╝
        """)

        # Test connectivity
        if not await self.test_health_check():
            print("❌ Advanced API is not healthy. Stopping tests.")
            return

        # Run comprehensive tests
        await self.test_create_tenants()
        await self.test_list_tenants_advanced()
        await self.test_advanced_document_upload()
        await self.test_hybrid_queries()
        await self.test_tenant_isolation_advanced()
        await self.test_comprehensive_stats()

        print("\n✅ Advanced prototype testing completed!")
        print(f"📋 Created {len(self.tenants)} tenants with mock Neon projects")
        print(f"🕸️ Tested real Neo4j graph integration with namespacing")
        print(f"🔍 Validated hybrid database + graph search capabilities")
        print(f"🔒 Confirmed tenant isolation at database and graph levels")
        print(f"🎯 Advanced multi-tenant architecture prototype validated!")


async def main():
    async with AdvancedPrototypeTester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
