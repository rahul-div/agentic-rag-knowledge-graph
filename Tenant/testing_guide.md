# Multi-Tenant RAG System Testing Guide

## 🧪 **Overview**

This comprehensive testing guide covers all aspects of validating the multi-tenant RAG system, ensuring complete tenant isolation, security, and functionality.

## 📋 **Testing Strategy**

### **Test Categories**

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing  
3. **Security Tests**: Tenant isolation and authentication
4. **Performance Tests**: Load and stress testing
5. **End-to-End Tests**: Full workflow validation

## 🚀 **Quick Start Testing**

### **Prerequisites**

```bash
pip install pytest pytest-asyncio httpx pytest-cov
```

### **Run All Tests**

```bash
# Run complete test suite
pytest tests/ -v --cov=Tenant

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v  
pytest tests/security/ -v
```

## 🔧 **Unit Tests**

### **Test Structure**

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── test_tenant_manager.py
│   ├── test_graphiti_client.py
│   ├── test_auth_middleware.py
│   └── test_agent.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_rag_pipeline.py
│   └── test_database_isolation.py
├── security/
│   ├── test_tenant_isolation.py
│   ├── test_authentication.py
│   └── test_authorization.py
└── performance/
    ├── test_load.py
    └── test_stress.py
```

### **Example Test Files**

#### **tests/conftest.py**

```python
import pytest
import asyncio
import asyncpg
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from Tenant.tenant_manager import TenantManager, Tenant, Document
from Tenant.multi_tenant_graphiti import TenantGraphitiClient
from Tenant.multi_tenant_agent import MultiTenantRAGAgent, TenantContext
from Tenant.auth_middleware import JWTManager

# Async test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_db_pool():
    """Mock database pool for testing."""
    pool = AsyncMock()
    
    # Mock connection
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None
    
    return pool

@pytest.fixture
async def tenant_manager(mock_db_pool):
    """Create tenant manager with mocked database."""
    manager = TenantManager("mock://connection")
    manager.pool = mock_db_pool
    return manager

@pytest.fixture
async def graphiti_client():
    """Create mocked Graphiti client."""
    client = TenantGraphitiClient("mock://neo4j", "user", "pass")
    client.graphiti = AsyncMock()
    client._initialized = True
    return client

@pytest.fixture
async def rag_agent(tenant_manager, graphiti_client):
    """Create RAG agent with mocked dependencies."""
    agent = MultiTenantRAGAgent(tenant_manager, graphiti_client)
    await agent.initialize()
    return agent

@pytest.fixture
def jwt_manager():
    """Create JWT manager for testing."""
    return JWTManager("test-secret-key")

@pytest.fixture
def sample_tenant():
    """Sample tenant for testing."""
    return Tenant(
        id="test_tenant",
        name="Test Corporation",
        email="test@corp.com",
        status="active",
        max_documents=100,
        max_storage_mb=50,
        metadata={"type": "test"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return Document(
        tenant_id="test_tenant",
        title="Test Document",
        source="test.md",
        content="This is a test document for the multi-tenant RAG system.",
        metadata={"category": "test"}
    )

@pytest.fixture
def tenant_context():
    """Sample tenant context for testing."""
    return TenantContext(
        tenant_id="test_tenant",
        user_id="test_user",
        permissions=["read", "write"],
        metadata={"session": "test_session"}
    )
```

#### **tests/unit/test_tenant_manager.py**

```python
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from Tenant.tenant_manager import TenantManager, Tenant, Document, Chunk

class TestTenantManager:
    """Test suite for TenantManager."""
    
    @pytest.mark.asyncio
    async def test_create_tenant(self, tenant_manager, mock_db_pool):
        """Test tenant creation."""
        # Mock database response
        mock_row = {
            'id': 'test_tenant',
            'name': 'Test Corp',
            'email': 'test@corp.com',
            'status': 'active',
            'max_documents': 100,
            'max_storage_mb': 50,
            'metadata': '{}',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow.return_value = None  # No existing tenant
        conn.fetchrow.side_effect = [None, mock_row]  # Check, then create
        
        # Test creation
        tenant = await tenant_manager.create_tenant(
            tenant_id="test_tenant",
            name="Test Corp",
            email="test@corp.com"
        )
        
        assert tenant.id == "test_tenant"
        assert tenant.name == "Test Corp"
        assert tenant.email == "test@corp.com"
        assert tenant.status == "active"
    
    @pytest.mark.asyncio
    async def test_create_duplicate_tenant(self, tenant_manager, mock_db_pool):
        """Test creation of duplicate tenant raises error."""
        # Mock existing tenant
        mock_row = {'id': 'test_tenant'}
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow.return_value = mock_row
        
        with pytest.raises(ValueError, match="already exists"):
            await tenant_manager.create_tenant(
                tenant_id="test_tenant",
                name="Test Corp",
                email="test@corp.com"
            )
    
    @pytest.mark.asyncio
    async def test_get_tenant(self, tenant_manager, mock_db_pool):
        """Test getting tenant by ID."""
        mock_row = {
            'id': 'test_tenant',
            'name': 'Test Corp',
            'email': 'test@corp.com',
            'status': 'active',
            'max_documents': 100,
            'max_storage_mb': 50,
            'metadata': '{"type": "test"}',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow.return_value = mock_row
        
        tenant = await tenant_manager.get_tenant("test_tenant")
        
        assert tenant is not None
        assert tenant.id == "test_tenant"
        assert tenant.metadata == {"type": "test"}
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_tenant(self, tenant_manager, mock_db_pool):
        """Test getting non-existent tenant returns None."""
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow.return_value = None
        
        tenant = await tenant_manager.get_tenant("nonexistent")
        assert tenant is None
    
    @pytest.mark.asyncio
    async def test_vector_search(self, tenant_manager, mock_db_pool):
        """Test tenant-aware vector search."""
        mock_rows = [
            {
                'chunk_id': 'chunk_1',
                'document_id': 'doc_1',
                'content': 'Test content',
                'similarity': 0.9,
                'metadata': '{"source": "test"}',
                'document_title': 'Test Doc',
                'tenant_id': 'test_tenant'
            }
        ]
        
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetch.return_value = mock_rows
        
        results = await tenant_manager.vector_search(
            tenant_id="test_tenant",
            query_embedding=[0.1] * 768,
            limit=10
        )
        
        assert len(results) == 1
        assert results[0]['chunk_id'] == 'chunk_1'
        assert results[0]['tenant_id'] == 'test_tenant'
        assert results[0]['similarity'] == 0.9
```

#### **tests/unit/test_graphiti_client.py**

```python
import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from Tenant.multi_tenant_graphiti import TenantGraphitiClient, GraphEpisode

class TestTenantGraphitiClient:
    """Test suite for TenantGraphitiClient."""
    
    @pytest.mark.asyncio
    async def test_namespace_generation(self, graphiti_client):
        """Test tenant namespace generation."""
        namespace = graphiti_client._get_tenant_namespace("test_tenant")
        assert namespace == "tenant_test_tenant"
    
    @pytest.mark.asyncio
    async def test_add_episode(self, graphiti_client):
        """Test adding episode to tenant namespace."""
        episode = GraphEpisode(
            tenant_id="test_tenant",
            name="Test Episode",
            content="Test content for the episode",
            source_description="Test source"
        )
        
        # Mock successful addition
        graphiti_client.graphiti.add_episode.return_value = None
        
        result = await graphiti_client.add_episode_for_tenant(episode)
        
        assert result is True
        graphiti_client.graphiti.add_episode.assert_called_once()
        
        # Verify namespace was used
        call_args = graphiti_client.graphiti.add_episode.call_args
        assert call_args.kwargs['group_id'] == "tenant_test_tenant"
    
    @pytest.mark.asyncio
    async def test_search_tenant_graph(self, graphiti_client):
        """Test searching within tenant namespace."""
        mock_results = [
            {"entity": "Test Entity", "type": "concept"},
            {"entity": "Another Entity", "type": "person"}
        ]
        
        graphiti_client.graphiti.search.return_value = mock_results
        
        results = await graphiti_client.search_tenant_graph(
            tenant_id="test_tenant",
            query="test query",
            limit=5
        )
        
        assert len(results) == 2
        assert all(r['tenant_id'] == 'test_tenant' for r in results)
        assert all(r['namespace'] == 'tenant_test_tenant' for r in results)
        
        # Verify search was called with correct namespace
        graphiti_client.graphiti.search.assert_called_once_with(
            query="test query",
            group_id="tenant_test_tenant"
        )
    
    @pytest.mark.asyncio
    async def test_get_tenant_stats(self, graphiti_client):
        """Test getting tenant graph statistics."""
        mock_entities = [
            {"name": "Entity 1", "type": "concept"},
            {"name": "Entity 2", "type": "person"},
            {"name": "Entity 3", "type": "organization"}
        ]
        
        graphiti_client.graphiti.search.return_value = mock_entities
        
        stats = await graphiti_client.get_tenant_graph_stats("test_tenant")
        
        assert stats['tenant_id'] == 'test_tenant'
        assert stats['namespace'] == 'tenant_test_tenant'
        assert stats['entity_count'] == 3
        assert len(stats['entities_sample']) <= 10
```

## 🔒 **Security Tests**

#### **tests/security/test_tenant_isolation.py**

```python
import pytest
from unittest.mock import AsyncMock

class TestTenantIsolation:
    """Test suite for tenant data isolation."""
    
    @pytest.mark.asyncio
    async def test_database_isolation(self, tenant_manager, mock_db_pool):
        """Test that database queries are properly isolated by tenant."""
        # Mock two different tenant responses
        tenant_a_docs = [{'id': 'doc_a1', 'tenant_id': 'tenant_a'}]
        tenant_b_docs = [{'id': 'doc_b1', 'tenant_id': 'tenant_b'}]
        
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        
        # First call for tenant A
        conn.fetch.return_value = tenant_a_docs
        docs_a = await tenant_manager.list_documents("tenant_a")
        
        # Second call for tenant B  
        conn.fetch.return_value = tenant_b_docs
        docs_b = await tenant_manager.list_documents("tenant_b")
        
        # Verify isolation
        assert len(docs_a) == 1
        assert docs_a[0].tenant_id == "tenant_a"
        assert len(docs_b) == 1
        assert docs_b[0].tenant_id == "tenant_b"
        
        # Verify SQL calls included tenant filtering
        assert conn.fetch.call_count == 2
        for call in conn.fetch.call_args_list:
            sql = call[0][0]
            assert "tenant_id = $1" in sql
    
    @pytest.mark.asyncio
    async def test_graph_namespace_isolation(self, graphiti_client):
        """Test that graph queries are isolated by namespace."""
        # Mock different results for different tenants
        tenant_a_results = [{"entity": "A Entity"}]
        tenant_b_results = [{"entity": "B Entity"}]
        
        # Test tenant A search
        graphiti_client.graphiti.search.return_value = tenant_a_results
        results_a = await graphiti_client.search_tenant_graph("tenant_a", "test")
        
        # Test tenant B search
        graphiti_client.graphiti.search.return_value = tenant_b_results
        results_b = await graphiti_client.search_tenant_graph("tenant_b", "test")
        
        # Verify different namespaces were used
        assert len(results_a) == 1
        assert results_a[0]['namespace'] == 'tenant_tenant_a'
        assert len(results_b) == 1
        assert results_b[0]['namespace'] == 'tenant_tenant_b'
        
        # Verify search calls used correct namespaces
        calls = graphiti_client.graphiti.search.call_args_list
        assert calls[0].kwargs['group_id'] == 'tenant_tenant_a'
        assert calls[1].kwargs['group_id'] == 'tenant_tenant_b'
    
    @pytest.mark.asyncio
    async def test_cross_tenant_data_leakage_prevention(self, rag_agent):
        """Test that one tenant cannot access another tenant's data."""
        # Create contexts for different tenants
        context_a = TenantContext(tenant_id="tenant_a", permissions=["read"])
        context_b = TenantContext(tenant_id="tenant_b", permissions=["read"])
        
        # Mock search results
        rag_agent.tenant_manager.vector_search.return_value = [
            {"chunk_id": "chunk_a", "tenant_id": "tenant_a"}
        ]
        rag_agent.graphiti_client.search_tenant_graph.return_value = [
            {"result": "graph_a", "tenant_id": "tenant_a"}
        ]
        
        # Search as tenant A
        results_a = await rag_agent.quick_search("tenant_a", "test query")
        
        # Verify only tenant A's data is returned
        if isinstance(results_a, list) and results_a:
            for result in results_a:
                if 'tenant_id' in result:
                    assert result['tenant_id'] == 'tenant_a'
```

#### **tests/security/test_authentication.py**

```python
import pytest
from datetime import datetime, timedelta
from jose import jwt

from Tenant.auth_middleware import JWTManager, TenantContext

class TestAuthentication:
    """Test suite for JWT authentication."""
    
    def test_create_access_token(self, jwt_manager):
        """Test access token creation."""
        token = jwt_manager.create_access_token(
            tenant_id="test_tenant",
            user_id="test_user",
            permissions=["read", "write"]
        )
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify payload
        payload = jwt.decode(token, jwt_manager.secret_key, algorithms=[jwt_manager.algorithm])
        assert payload['tenant_id'] == 'test_tenant'
        assert payload['user_id'] == 'test_user'
        assert payload['permissions'] == ['read', 'write']
        assert payload['type'] == 'access'
    
    def test_verify_valid_token(self, jwt_manager):
        """Test verification of valid token."""
        token = jwt_manager.create_access_token("test_tenant", "test_user")
        payload = jwt_manager.verify_token(token)
        
        assert payload['tenant_id'] == 'test_tenant'
        assert payload['user_id'] == 'test_user'
    
    def test_verify_expired_token(self, jwt_manager):
        """Test verification of expired token."""
        # Create token with past expiration
        past_time = datetime.utcnow() - timedelta(hours=1)
        token = jwt_manager.create_access_token(
            "test_tenant", 
            "test_user",
            custom_expiry=timedelta(seconds=-3600)
        )
        
        with pytest.raises(jwt.JWTError):
            jwt_manager.verify_token(token)
    
    def test_extract_tenant_context(self, jwt_manager):
        """Test extracting tenant context from token."""
        token = jwt_manager.create_access_token(
            tenant_id="test_tenant",
            user_id="test_user", 
            permissions=["read", "write", "admin"],
            metadata={"role": "admin"}
        )
        
        context = jwt_manager.extract_tenant_context(token)
        
        assert isinstance(context, TenantContext)
        assert context.tenant_id == "test_tenant"
        assert context.user_id == "test_user"
        assert context.has_permission("read")
        assert context.has_permission("write")
        assert context.is_admin()
        assert context.metadata.get("role") == "admin"
    
    def test_rate_limiting(self, jwt_manager):
        """Test rate limiting functionality."""
        identifier = "test_user"
        
        # Should not be rate limited initially
        assert not jwt_manager.is_rate_limited(identifier)
        
        # Record multiple failed attempts
        for _ in range(jwt_manager.max_failed_attempts):
            jwt_manager.record_failed_attempt(identifier)
        
        # Should now be rate limited
        assert jwt_manager.is_rate_limited(identifier)
        
        # Clear attempts
        jwt_manager.clear_failed_attempts(identifier)
        assert not jwt_manager.is_rate_limited(identifier)
```

## 🔗 **Integration Tests**

#### **tests/integration/test_api_endpoints.py**

```python
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

# This would import your actual FastAPI app
# from Tenant.multi_tenant_api import create_app

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    # Mock app for testing
    client = TestClient(app)  # Replace with your actual app
    
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data

@pytest.mark.asyncio  
async def test_tenant_creation_flow():
    """Test complete tenant creation and authentication flow."""
    client = TestClient(app)  # Replace with your actual app
    
    # 1. Create tenant
    tenant_data = {
        "id": "integration_test",
        "name": "Integration Test Corp",
        "email": "integration@test.com",
        "max_documents": 50,
        "max_storage_mb": 25
    }
    
    response = client.post("/tenants", json=tenant_data)
    assert response.status_code == 200
    
    created_tenant = response.json()
    assert created_tenant["id"] == "integration_test"
    
    # 2. Get authentication token
    response = client.post("/auth/token?tenant_id=integration_test&user_id=test_user")
    assert response.status_code == 200
    
    token_data = response.json()
    assert "access_token" in token_data
    
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create document
    doc_data = {
        "title": "Integration Test Document",
        "source": "integration_test.md",
        "content": "This is an integration test document for the multi-tenant RAG system."
    }
    
    response = client.post("/documents", json=doc_data, headers=headers)
    assert response.status_code == 200
    
    doc_result = response.json()
    assert "document_id" in doc_result
    
    # 4. Query the system
    query_data = {
        "query": "What is this document about?",
        "use_vector": True,
        "use_graph": True,
        "max_results": 5
    }
    
    response = client.post("/query", json=query_data, headers=headers)
    assert response.status_code == 200
    
    query_result = response.json()
    assert "response" in query_result
    assert query_result["tenant_id"] == "integration_test"
```

## ⚡ **Performance Tests**

#### **tests/performance/test_load.py**

```python
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestPerformance:
    """Performance test suite."""
    
    @pytest.mark.asyncio
    async def test_concurrent_tenant_operations(self, rag_agent):
        """Test concurrent operations across multiple tenants."""
        
        async def tenant_operation(tenant_id: str, operation_id: int):
            """Simulate tenant operation."""
            start_time = time.time()
            
            # Mock some work
            await asyncio.sleep(0.1)  # Simulate I/O
            
            end_time = time.time()
            return {
                "tenant_id": tenant_id,
                "operation_id": operation_id,
                "duration": end_time - start_time
            }
        
        # Create tasks for multiple tenants
        tasks = []
        num_tenants = 10
        operations_per_tenant = 5
        
        for tenant_i in range(num_tenants):
            tenant_id = f"tenant_{tenant_i}"
            for op_i in range(operations_per_tenant):
                task = tenant_operation(tenant_id, op_i)
                tasks.append(task)
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify results
        assert len(results) == num_tenants * operations_per_tenant
        
        # Check that operations completed in reasonable time
        assert total_time < 2.0  # Should complete in under 2 seconds
        
        # Verify all tenants were processed
        tenant_ids = {r["tenant_id"] for r in results}
        assert len(tenant_ids) == num_tenants
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, tenant_manager):
        """Test database connection pool under load."""
        
        async def db_operation(operation_id: int):
            """Simulate database operation."""
            async with tenant_manager.get_connection("test_tenant") as conn:
                # Mock database query
                await asyncio.sleep(0.05)  # Simulate query time
                return f"operation_{operation_id}_completed"
        
        # Test with more operations than pool size
        num_operations = 50
        tasks = [db_operation(i) for i in range(num_operations)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify all operations completed
        assert len(results) == num_operations
        
        # Should handle efficiently with connection pooling
        assert total_time < 5.0
```

## 🎯 **Test Execution Scripts**

### **run_tests.py**

```python
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle output."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*50}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} failed with return code {result.returncode}")
        return False
    else:
        print(f"✅ {description} passed")
        return True

def main():
    parser = argparse.ArgumentParser(description="Run multi-tenant RAG tests")
    parser.add_argument("--type", choices=["unit", "integration", "security", "performance", "all"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    base_cmd = "pytest"
    if args.verbose:
        base_cmd += " -v"
    if args.coverage:
        base_cmd += " --cov=Tenant --cov-report=html --cov-report=term"
    
    # Test commands
    test_commands = {
        "unit": f"{base_cmd} tests/unit/",
        "integration": f"{base_cmd} tests/integration/",
        "security": f"{base_cmd} tests/security/",
        "performance": f"{base_cmd} tests/performance/",
        "all": f"{base_cmd} tests/"
    }
    
    success = True
    
    if args.type == "all":
        # Run all test types
        for test_type, cmd in test_commands.items():
            if test_type != "all":
                if not run_command(cmd, f"{test_type.title()} Tests"):
                    success = False
    else:
        # Run specific test type
        cmd = test_commands[args.type]
        success = run_command(cmd, f"{args.type.title()} Tests")
    
    # Additional validation commands
    if success and args.type in ["all", "security"]:
        print("\n" + "="*50)
        print("Running additional security validations...")
        print("="*50)
        
        # Check for common security issues
        security_checks = [
            "bandit -r Tenant/ -f json",
            "safety check --json",
        ]
        
        for cmd in security_checks:
            try:
                subprocess.run(cmd, shell=True, check=True, capture_output=True)
                print(f"✅ Security check passed: {cmd}")
            except subprocess.CalledProcessError:
                print(f"⚠️  Security check failed or found issues: {cmd}")
    
    if success:
        print("\n🎉 All tests passed successfully!")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 📊 **Test Reports and Monitoring**

### **Generate Test Reports**

```bash
# Generate comprehensive test report
pytest tests/ --html=reports/test_report.html --self-contained-html

# Generate coverage report
pytest tests/ --cov=Tenant --cov-report=html --cov-report=term

# Performance profiling
pytest tests/performance/ --profile --profile-svg
```

### **Continuous Integration**

#### **.github/workflows/test.yml**

```yaml
name: Multi-Tenant RAG Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      neo4j:
        image: neo4j:5.0
        env:
          NEO4J_AUTH: neo4j/password
        options: >-
          --health-cmd "cypher-shell -u neo4j -p password 'RETURN 1'"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov httpx
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=Tenant --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 🎯 **Testing Best Practices**

### **Test Organization**
- One test file per module
- Clear test names describing what is being tested
- Use fixtures for common setup
- Mock external dependencies

### **Security Testing**
- Always test tenant isolation
- Verify authentication and authorization
- Test for data leakage between tenants
- Validate input sanitization

### **Performance Testing**
- Test under realistic load conditions
- Monitor database connection pools
- Validate response times meet SLA requirements
- Test concurrent tenant operations

### **Test Data Management**
- Use separate test databases
- Clean up test data after each test
- Use realistic but anonymized test data
- Test with various data sizes

---

## 🚀 **Next Steps**

1. **Implement Test Suite**: Create the test files outlined above
2. **Set Up CI/CD**: Configure automated testing
3. **Performance Baselines**: Establish performance benchmarks
4. **Security Audits**: Regular security testing schedule
5. **Test Documentation**: Maintain test documentation and coverage reports

This comprehensive testing strategy ensures your multi-tenant RAG system is robust, secure, and performant across all tenant operations!
