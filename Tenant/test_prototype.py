#!/usr/bin/env python3
"""
Multi-Tenant RAG Prototype Testing Script
Comprehensive validation of the prototype API with 3-4 tenant scenarios.
"""

import asyncio
import json
import sys
import time
from typing import Dict, List, Any
from pathlib import Path

try:
    import httpx
    from dotenv import load_dotenv
except ImportError:
    print("Please install required packages: pip install httpx python-dotenv")
    sys.exit(1)

# Load environment
load_dotenv()


class PrototypeAPITester:
    """Comprehensive tester for the prototype API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.tenants: List[Dict[str, Any]] = []
        self.test_results: Dict[str, Any] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results."""
        print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {status}")
        if details:
            print(f"   {details}")

        self.test_results[test_name] = {
            "status": status,
            "details": details,
            "timestamp": time.time(),
        }

    async def test_health_check(self):
        """Test API health endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/health")

            if response.status_code == 200:
                health_data = response.json()
                if health_data["status"] == "healthy":
                    self.log_test(
                        "Health Check", "PASS", f"Services: {health_data['services']}"
                    )
                else:
                    self.log_test(
                        "Health Check", "FAIL", f"Status: {health_data['status']}"
                    )
            else:
                self.log_test("Health Check", "FAIL", f"HTTP {response.status_code}")

        except Exception as e:
            self.log_test("Health Check", "FAIL", str(e))

    async def test_create_tenants(self, tenant_count: int = 3):
        """Test creating multiple tenants."""
        print(f"\n🏢 Creating {tenant_count} test tenants...")

        tenant_configs = [
            {"name": "TechCorp", "email": "admin@techcorp.com"},
            {"name": "HealthPlus", "email": "admin@healthplus.com"},
            {"name": "EduSystems", "email": "admin@edusystems.com"},
            {"name": "FinanceGroup", "email": "admin@financegroup.com"},
        ]

        for i in range(tenant_count):
            config = tenant_configs[i]
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/v1/tenants",
                    json={
                        "name": config["name"],
                        "email": config["email"],
                        "region": "aws-us-east-1",
                        "max_documents": 100,
                        "max_storage_mb": 50,
                    },
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
                tenants_list = response.json()
                self.log_test(
                    "List Tenants", "PASS", f"Found {len(tenants_list)} tenants"
                )
            else:
                self.log_test("List Tenants", "FAIL", f"HTTP {response.status_code}")

        except Exception as e:
            self.log_test("List Tenants", "FAIL", str(e))

    async def test_document_upload(self):
        """Test document upload for each tenant."""
        print(f"\n📄 Testing document upload for {len(self.tenants)} tenants...")

        # Test documents for each tenant
        test_documents = [
            {
                "title": "TechCorp Product Manual",
                "source": "product_manual.txt",
                "content": "TechCorp's flagship product is an AI-powered analytics platform that helps businesses make data-driven decisions. The platform includes machine learning algorithms, real-time dashboards, and predictive analytics capabilities.",
            },
            {
                "title": "HealthPlus Patient Care Guidelines",
                "source": "care_guidelines.txt",
                "content": "HealthPlus provides comprehensive healthcare services including preventive care, emergency services, and specialized treatments. Our patient care guidelines emphasize quality, safety, and patient satisfaction.",
            },
            {
                "title": "EduSystems Learning Framework",
                "source": "learning_framework.txt",
                "content": "EduSystems offers innovative educational technology solutions for schools and universities. Our learning framework incorporates adaptive learning, gamification, and personalized instruction methods.",
            },
            {
                "title": "FinanceGroup Investment Strategy",
                "source": "investment_strategy.txt",
                "content": "FinanceGroup specializes in wealth management and investment advisory services. Our investment strategy focuses on diversified portfolios, risk management, and long-term value creation for clients.",
            },
        ]

        for i, tenant in enumerate(self.tenants):
            if i < len(test_documents):
                doc = test_documents[i]
                try:
                    # Create multipart form data
                    files = {"file": (doc["source"], doc["content"], "text/plain")}
                    data = {"title": doc["title"], "source": doc["source"]}
                    headers = {"Authorization": f"Bearer {tenant['api_key']}"}

                    response = await self.client.post(
                        f"{self.base_url}/api/v1/documents/upload",
                        files=files,
                        data=data,
                        headers=headers,
                    )

                    if response.status_code == 200:
                        doc_data = response.json()
                        self.log_test(
                            f"Upload Document ({tenant['name']})",
                            "PASS",
                            f"Doc ID: {doc_data['id'][:8]}..., Title: {doc['title']}",
                        )
                    else:
                        self.log_test(
                            f"Upload Document ({tenant['name']})",
                            "FAIL",
                            f"HTTP {response.status_code}: {response.text}",
                        )

                except Exception as e:
                    self.log_test(f"Upload Document ({tenant['name']})", "FAIL", str(e))

    async def test_document_listing(self):
        """Test document listing for each tenant."""
        print(f"\n📋 Testing document listing for each tenant...")

        for tenant in self.tenants:
            try:
                headers = {"Authorization": f"Bearer {tenant['api_key']}"}
                response = await self.client.get(
                    f"{self.base_url}/api/v1/documents", headers=headers
                )

                if response.status_code == 200:
                    docs = response.json()
                    self.log_test(
                        f"List Documents ({tenant['name']})",
                        "PASS",
                        f"Found {len(docs)} documents",
                    )
                else:
                    self.log_test(
                        f"List Documents ({tenant['name']})",
                        "FAIL",
                        f"HTTP {response.status_code}",
                    )

            except Exception as e:
                self.log_test(f"List Documents ({tenant['name']})", "FAIL", str(e))

    async def test_rag_queries(self):
        """Test RAG queries for each tenant."""
        print(f"\n🤖 Testing RAG queries for each tenant...")

        # Tenant-specific queries
        queries = [
            "What is TechCorp's main product?",
            "What services does HealthPlus provide?",
            "How does EduSystems approach learning?",
            "What is FinanceGroup's investment focus?",
        ]

        for i, tenant in enumerate(self.tenants):
            if i < len(queries):
                query = queries[i]
                try:
                    headers = {"Authorization": f"Bearer {tenant['api_key']}"}
                    response = await self.client.post(
                        f"{self.base_url}/api/v1/query",
                        json={
                            "query": query,
                            "use_vector": True,
                            "use_graph": True,
                            "max_results": 5,
                        },
                        headers=headers,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        response_text = (
                            result["response"][:100] + "..."
                            if len(result["response"]) > 100
                            else result["response"]
                        )
                        self.log_test(
                            f"RAG Query ({tenant['name']})",
                            "PASS",
                            f"Query: '{query}' → Response: '{response_text}'",
                        )
                    else:
                        self.log_test(
                            f"RAG Query ({tenant['name']})",
                            "FAIL",
                            f"HTTP {response.status_code}: {response.text}",
                        )

                except Exception as e:
                    self.log_test(f"RAG Query ({tenant['name']})", "FAIL", str(e))

    async def test_cross_tenant_isolation(self):
        """Test that tenants cannot access each other's data."""
        print(f"\n🔒 Testing cross-tenant isolation...")

        if len(self.tenants) < 2:
            self.log_test("Cross-Tenant Isolation", "SKIP", "Need at least 2 tenants")
            return

        # Try to use tenant A's token to query tenant B's data
        tenant_a = self.tenants[0]
        tenant_b = self.tenants[1]

        try:
            # Query with tenant A's token about tenant B's content
            headers = {"Authorization": f"Bearer {tenant_a['api_key']}"}
            response = await self.client.post(
                f"{self.base_url}/api/v1/query",
                json={
                    "query": f"Tell me about {tenant_b['name']}",
                    "use_vector": True,
                    "use_graph": True,
                    "max_results": 5,
                },
                headers=headers,
            )

            if response.status_code == 200:
                result = response.json()
                # Check if response contains information about tenant B
                # This should NOT happen if isolation is working
                if tenant_b["name"].lower() in result["response"].lower():
                    self.log_test(
                        "Cross-Tenant Isolation",
                        "FAIL",
                        f"Tenant A can access Tenant B's data!",
                    )
                else:
                    self.log_test(
                        "Cross-Tenant Isolation",
                        "PASS",
                        "Tenant data properly isolated",
                    )
            else:
                self.log_test(
                    "Cross-Tenant Isolation",
                    "FAIL",
                    f"Unexpected error: HTTP {response.status_code}",
                )

        except Exception as e:
            self.log_test("Cross-Tenant Isolation", "FAIL", str(e))

    async def test_concurrent_operations(self):
        """Test concurrent operations across tenants."""
        print(f"\n⚡ Testing concurrent operations...")

        if len(self.tenants) < 2:
            self.log_test("Concurrent Operations", "SKIP", "Need at least 2 tenants")
            return

        try:
            # Create concurrent query tasks
            tasks = []
            for tenant in self.tenants:
                headers = {"Authorization": f"Bearer {tenant['api_key']}"}
                task = self.client.post(
                    f"{self.base_url}/api/v1/query",
                    json={
                        "query": f"What does {tenant['name']} do?",
                        "use_vector": True,
                        "use_graph": True,
                        "max_results": 3,
                    },
                    headers=headers,
                )
                tasks.append(task)

            # Execute all queries concurrently
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            successful_responses = 0
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    print(f"   ❌ Tenant {self.tenants[i]['name']}: {response}")
                elif response.status_code == 200:
                    successful_responses += 1
                    print(f"   ✅ Tenant {self.tenants[i]['name']}: Success")
                else:
                    print(
                        f"   ❌ Tenant {self.tenants[i]['name']}: HTTP {response.status_code}"
                    )

            self.log_test(
                "Concurrent Operations",
                "PASS" if successful_responses == len(self.tenants) else "PARTIAL",
                f"{successful_responses}/{len(self.tenants)} successful in {end_time - start_time:.2f}s",
            )

        except Exception as e:
            self.log_test("Concurrent Operations", "FAIL", str(e))

    async def test_tenant_stats(self):
        """Test tenant statistics endpoint."""
        print(f"\n📊 Testing tenant statistics...")

        for tenant in self.tenants:
            try:
                headers = {"Authorization": f"Bearer {tenant['api_key']}"}
                response = await self.client.get(
                    f"{self.base_url}/api/v1/stats", headers=headers
                )

                if response.status_code == 200:
                    stats = response.json()
                    self.log_test(
                        f"Tenant Stats ({tenant['name']})",
                        "PASS",
                        f"Docs: {stats['documents_count']}, Storage: {stats['storage_used_mb']}MB",
                    )
                else:
                    self.log_test(
                        f"Tenant Stats ({tenant['name']})",
                        "FAIL",
                        f"HTTP {response.status_code}",
                    )

            except Exception as e:
                self.log_test(f"Tenant Stats ({tenant['name']})", "FAIL", str(e))

    async def test_isolation_validation(self):
        """Test isolation validation endpoint."""
        print(f"\n🔍 Testing isolation validation...")

        for tenant in self.tenants:
            try:
                headers = {"Authorization": f"Bearer {tenant['api_key']}"}
                response = await self.client.get(
                    f"{self.base_url}/api/v1/validate-isolation", headers=headers
                )

                if response.status_code == 200:
                    validation = response.json()
                    self.log_test(
                        f"Isolation Validation ({tenant['name']})",
                        "PASS",
                        f"DB: {validation['database_isolation']}, Graph: {validation['graph_isolation']}",
                    )
                else:
                    self.log_test(
                        f"Isolation Validation ({tenant['name']})",
                        "FAIL",
                        f"HTTP {response.status_code}",
                    )

            except Exception as e:
                self.log_test(
                    f"Isolation Validation ({tenant['name']})", "FAIL", str(e)
                )

    async def run_full_test_suite(self, tenant_count: int = 3):
        """Run the complete test suite."""
        print("🧪 Multi-Tenant RAG Prototype Test Suite")
        print("=" * 50)

        start_time = time.time()

        # Core functionality tests
        await self.test_health_check()
        await self.test_create_tenants(tenant_count)
        await self.test_list_tenants()

        # Document management tests
        await self.test_document_upload()
        await self.test_document_listing()

        # RAG functionality tests
        await self.test_rag_queries()

        # Isolation and security tests
        await self.test_cross_tenant_isolation()
        await self.test_concurrent_operations()

        # Monitoring tests
        await self.test_tenant_stats()
        await self.test_isolation_validation()

        end_time = time.time()

        # Print summary
        print("\n" + "=" * 50)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result["status"] == "PASS"
        )
        failed_tests = sum(
            1 for result in self.test_results.values() if result["status"] == "FAIL"
        )
        skipped_tests = total_tests - passed_tests - failed_tests

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️  Skipped: {skipped_tests}")
        print(f"⏱️  Duration: {end_time - start_time:.2f}s")
        print(f"📊 Success Rate: {(passed_tests / total_tests) * 100:.1f}%")

        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if result["status"] == "FAIL":
                    print(f"   • {test_name}: {result['details']}")

        # Save detailed results
        with open("prototype_test_results.json", "w") as f:
            json.dump(
                {
                    "summary": {
                        "total": total_tests,
                        "passed": passed_tests,
                        "failed": failed_tests,
                        "skipped": skipped_tests,
                        "duration": end_time - start_time,
                        "success_rate": (passed_tests / total_tests) * 100,
                    },
                    "tenants_created": len(self.tenants),
                    "results": self.test_results,
                },
                f,
                indent=2,
                default=str,
            )

        print(f"\n💾 Detailed results saved to: prototype_test_results.json")

        return passed_tests == total_tests


async def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Tenant RAG Prototype Tester")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument(
        "--tenants", type=int, default=3, help="Number of tenants to test"
    )
    args = parser.parse_args()

    async with PrototypeAPITester(args.url) as tester:
        success = await tester.run_full_test_suite(args.tenants)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
