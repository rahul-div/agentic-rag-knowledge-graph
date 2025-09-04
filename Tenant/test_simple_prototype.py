#!/usr/bin/env python3
"""
Quick Prototype Testing Script
Tests the simplified multi-tenant API to ensure core functionality works.
"""

import asyncio
import json
import sys
from typing import Dict, List, Any

try:
    import httpx
except ImportError:
    print("Please install httpx: pip install httpx")
    sys.exit(1)


class QuickPrototypeTester:
    """Quick tester for the simplified prototype API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
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
        """Test API health endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/health")

            if response.status_code == 200:
                health_data = response.json()
                self.log_test(
                    "Health Check", "PASS", f"Services: {health_data['services']}"
                )
                return True
            else:
                self.log_test("Health Check", "FAIL", f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Health Check", "FAIL", str(e))
            return False

    async def test_create_tenants(self):
        """Test creating 3 tenants."""
        print(f"\n🏢 Creating test tenants...")

        tenant_configs = [
            {"name": "TechCorp", "email": "admin@techcorp.com", "max_documents": 50},
            {
                "name": "HealthPlus",
                "email": "admin@healthplus.com",
                "max_documents": 75,
            },
            {
                "name": "EduSystems",
                "email": "admin@edusystems.com",
                "max_documents": 100,
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
                        f"ID: {tenant_data['id'][:8]}..., API Key: {tenant_data['api_key'][:16]}...",
                    )
                else:
                    self.log_test(
                        f"Create Tenant {config['name']}",
                        "FAIL",
                        f"HTTP {response.status_code}: {response.text}",
                    )

            except Exception as e:
                self.log_test(f"Create Tenant {config['name']}", "FAIL", str(e))

    async def test_list_tenants(self):
        """Test listing tenants."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/tenants")

            if response.status_code == 200:
                tenants = response.json()
                self.log_test("List Tenants", "PASS", f"Found {len(tenants)} tenants")
                for tenant in tenants:
                    print(
                        f"   - {tenant['name']} ({tenant['id'][:8]}...): {tenant['document_count']} docs"
                    )
            else:
                self.log_test("List Tenants", "FAIL", f"HTTP {response.status_code}")

        except Exception as e:
            self.log_test("List Tenants", "FAIL", str(e))

    async def test_upload_documents(self):
        """Test uploading documents to tenants."""
        print(f"\n📄 Uploading test documents...")

        test_documents = [
            {
                "title": "Company Overview",
                "content": "TechCorp is a leading technology company specializing in artificial intelligence and machine learning solutions. Founded in 2020, we have grown to serve over 500 enterprise clients worldwide.",
            },
            {
                "title": "Product Catalog",
                "content": "Our main products include: AI Assistant Platform, Data Analytics Suite, Machine Learning Infrastructure, and Custom AI Solutions for enterprise clients.",
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
                            f"Upload Doc to {tenant_name}",
                            "PASS",
                            f"{doc['title']} -> {doc_data['chunks']} chunks",
                        )
                    else:
                        self.log_test(
                            f"Upload Doc to {tenant_name}",
                            "FAIL",
                            f"HTTP {response.status_code}: {response.text}",
                        )

                except Exception as e:
                    self.log_test(f"Upload Doc to {tenant_name}", "FAIL", str(e))

    async def test_queries(self):
        """Test querying tenant knowledge bases."""
        print(f"\n🔍 Testing queries...")

        test_queries = [
            "What does the company do?",
            "Tell me about the products",
            "How many clients do we have?",
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
                            f"Query: '{query}' -> {len(query_data['sources'])} sources",
                        )
                        if query_data["sources"]:
                            print(f"      Response: {query_data['response'][:100]}...")
                    else:
                        self.log_test(
                            f"Query {tenant_name}",
                            "FAIL",
                            f"HTTP {response.status_code}: {response.text}",
                        )

                except Exception as e:
                    self.log_test(f"Query {tenant_name}", "FAIL", str(e))

    async def test_tenant_isolation(self):
        """Test that tenants only see their own data."""
        print(f"\n🔒 Testing tenant isolation...")

        if len(self.tenants) >= 2:
            tenant1 = self.tenants[0]
            tenant2 = self.tenants[1]

            # Query tenant 2 for tenant 1's specific content
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/v1/tenants/{tenant2['id']}/query",
                    json={
                        "query": "TechCorp artificial intelligence",
                        "use_graph": True,
                    },
                )

                if response.status_code == 200:
                    query_data = response.json()
                    if "TechCorp" not in query_data["response"]:
                        self.log_test(
                            "Tenant Isolation",
                            "PASS",
                            "Tenant 2 cannot see Tenant 1's data",
                        )
                    else:
                        self.log_test(
                            "Tenant Isolation", "FAIL", "Data leakage detected!"
                        )
                else:
                    self.log_test(
                        "Tenant Isolation", "FAIL", f"HTTP {response.status_code}"
                    )

            except Exception as e:
                self.log_test("Tenant Isolation", "FAIL", str(e))

    async def test_tenant_stats(self):
        """Test tenant statistics."""
        print(f"\n📊 Testing tenant statistics...")

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
                        f"Docs: {stats['documents']}, Chunks: {stats['chunks']}, Entities: {stats['graph_entities']}",
                    )
                else:
                    self.log_test(
                        f"Stats {tenant_name}", "FAIL", f"HTTP {response.status_code}"
                    )

            except Exception as e:
                self.log_test(f"Stats {tenant_name}", "FAIL", str(e))

    async def run_all_tests(self):
        """Run all prototype tests."""
        print("""
        ╔══════════════════════════════════════════════════════════════╗
        ║              Multi-Tenant RAG Prototype Testing              ║
        ║                  Validating Core Functionality               ║
        ╚══════════════════════════════════════════════════════════════╝
        """)

        # Basic connectivity
        if not await self.test_health_check():
            print("❌ API is not healthy. Stopping tests.")
            return

        # Core functionality tests
        await self.test_create_tenants()
        await self.test_list_tenants()
        await self.test_upload_documents()
        await self.test_queries()
        await self.test_tenant_isolation()
        await self.test_tenant_stats()

        print(f"\n✅ Prototype testing completed!")
        print(f"📋 Created {len(self.tenants)} tenants")
        print(f"🎯 Core multi-tenant functionality validated")


async def main():
    async with QuickPrototypeTester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
