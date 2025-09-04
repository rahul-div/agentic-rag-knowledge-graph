"""
Tests for catalog database functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
import uuid

# Import directly to avoid module import issues
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../Tenant"))

from catalog_database import CatalogDatabase, TenantProjectInfo


class TestCatalogDatabase:
    """Test catalog database operations."""

    @pytest.fixture
    def catalog_db(self):
        """Create a CatalogDatabase instance for testing."""
        return CatalogDatabase("postgresql://test:test@localhost:5432/test_db")

    @pytest.fixture
    def mock_pool(self):
        """Mock database pool."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        return mock_pool, mock_conn

    @pytest.mark.asyncio
    async def test_create_tenant_project_info(self, catalog_db, mock_pool):
        """Test creating tenant project info."""
        mock_pool_obj, mock_conn = mock_pool

        with patch.object(catalog_db, "pool", mock_pool_obj):
            mock_conn.execute.return_value = None

            tenant_id = str(uuid.uuid4())
            project_info = TenantProjectInfo(
                tenant_id=tenant_id,
                neon_project_id="proj_123",
                neon_database_url="postgresql://user:pass@host/db",
                status="active",
                created_at=datetime.utcnow(),
            )

            await catalog_db.create_tenant_project_info(project_info)

            # Verify the execute was called
            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tenant_project_info(self, catalog_db, mock_pool):
        """Test retrieving tenant project info."""
        mock_pool_obj, mock_conn = mock_pool

        with patch.object(catalog_db, "pool", mock_pool_obj):
            tenant_id = str(uuid.uuid4())
            mock_row = {
                "tenant_id": tenant_id,
                "neon_project_id": "proj_123",
                "neon_database_url": "postgresql://user:pass@host/db",
                "status": "active",
                "created_at": datetime.utcnow(),
            }
            mock_conn.fetchrow.return_value = mock_row

            result = await catalog_db.get_tenant_project_info(tenant_id)

            assert result is not None
            assert result.tenant_id == tenant_id
            assert result.neon_project_id == "proj_123"
            assert result.status == "active"

    @pytest.mark.asyncio
    async def test_get_tenant_project_info_not_found(self, catalog_db, mock_pool):
        """Test retrieving non-existent tenant project info."""
        mock_pool_obj, mock_conn = mock_pool

        with patch.object(catalog_db, "pool", mock_pool_obj):
            mock_conn.fetchrow.return_value = None

            result = await catalog_db.get_tenant_project_info("nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_list_tenant_projects(self, catalog_db, mock_pool):
        """Test listing all tenant projects."""
        mock_pool_obj, mock_conn = mock_pool

        with patch.object(catalog_db, "pool", mock_pool_obj):
            mock_rows = [
                {
                    "tenant_id": str(uuid.uuid4()),
                    "neon_project_id": "proj_123",
                    "neon_database_url": "postgresql://user:pass@host/db1",
                    "status": "active",
                    "created_at": datetime.utcnow(),
                },
                {
                    "tenant_id": str(uuid.uuid4()),
                    "neon_project_id": "proj_456",
                    "neon_database_url": "postgresql://user:pass@host/db2",
                    "status": "inactive",
                    "created_at": datetime.utcnow(),
                },
            ]
            mock_conn.fetch.return_value = mock_rows

            results = await catalog_db.list_tenant_projects()

            assert len(results) == 2
            assert results[0].neon_project_id == "proj_123"
            assert results[1].neon_project_id == "proj_456"

    @pytest.mark.asyncio
    async def test_update_tenant_status(self, catalog_db, mock_pool):
        """Test updating tenant status."""
        mock_pool_obj, mock_conn = mock_pool

        with patch.object(catalog_db, "pool", mock_pool_obj):
            mock_conn.execute.return_value = None

            tenant_id = str(uuid.uuid4())
            await catalog_db.update_tenant_status(tenant_id, "inactive")

            # Verify the execute was called
            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_tenant_project_info(self, catalog_db, mock_pool):
        """Test deleting tenant project info."""
        mock_pool_obj, mock_conn = mock_pool

        with patch.object(catalog_db, "pool", mock_pool_obj):
            mock_conn.execute.return_value = None

            tenant_id = str(uuid.uuid4())
            await catalog_db.delete_tenant_project_info(tenant_id)

            # Verify the execute was called
            mock_conn.execute.assert_called_once()
