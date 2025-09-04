"""
Tests for Neon project manager functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch
import uuid

# Import directly to avoid module import issues
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../Tenant"))

from neon_project_manager import NeonProjectManager, NeonAPIError


class TestNeonProjectManager:
    """Test Neon project manager operations."""

    @pytest.fixture
    def project_manager(self):
        """Create a NeonProjectManager instance for testing."""
        return NeonProjectManager("test_api_key")

    @pytest.mark.asyncio
    async def test_create_project_success(self, project_manager):
        """Test successful project creation."""
        mock_response = {
            "project": {
                "id": "proj_123456",
                "name": "tenant-test-123",
                "region_id": "aws-us-east-1",
                "created_at": "2024-01-01T00:00:00Z",
            }
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_post.return_value.__aenter__.return_value.status = 201

            tenant_id = str(uuid.uuid4())
            result = await project_manager.create_project(tenant_id)

            assert result.project_id == "proj_123456"
            assert result.name == "tenant-test-123"
            assert result.region_id == "aws-us-east-1"

    @pytest.mark.asyncio
    async def test_create_project_api_error(self, project_manager):
        """Test project creation with API error."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 400
            mock_post.return_value.__aenter__.return_value.text = AsyncMock(
                return_value="Bad Request"
            )

            tenant_id = str(uuid.uuid4())

            with pytest.raises(NeonAPIError):
                await project_manager.create_project(tenant_id)

    @pytest.mark.asyncio
    async def test_get_project_info_success(self, project_manager):
        """Test successful project info retrieval."""
        mock_response = {
            "project": {
                "id": "proj_123456",
                "name": "tenant-test-123",
                "region_id": "aws-us-east-1",
                "created_at": "2024-01-01T00:00:00Z",
            }
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            result = await project_manager.get_project_info("proj_123456")

            assert result.project_id == "proj_123456"
            assert result.name == "tenant-test-123"

    @pytest.mark.asyncio
    async def test_get_project_info_not_found(self, project_manager):
        """Test project info retrieval for non-existent project."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 404
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value="Not Found"
            )

            with pytest.raises(NeonAPIError):
                await project_manager.get_project_info("nonexistent")

    @pytest.mark.asyncio
    async def test_delete_project_success(self, project_manager):
        """Test successful project deletion."""
        mock_response = {"message": "Project deleted successfully"}

        with patch("aiohttp.ClientSession.delete") as mock_delete:
            mock_delete.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_delete.return_value.__aenter__.return_value.status = 200

            result = await project_manager.delete_project("proj_123456")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_project_error(self, project_manager):
        """Test project deletion with error."""
        with patch("aiohttp.ClientSession.delete") as mock_delete:
            mock_delete.return_value.__aenter__.return_value.status = 400
            mock_delete.return_value.__aenter__.return_value.text = AsyncMock(
                return_value="Bad Request"
            )

            with pytest.raises(NeonAPIError):
                await project_manager.delete_project("proj_123456")

    @pytest.mark.asyncio
    async def test_get_connection_string_success(self, project_manager):
        """Test successful connection string retrieval."""
        mock_response = {
            "connection_uris": [
                {"connection_uri": "postgresql://user:pass@host:5432/neondb"}
            ]
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            result = await project_manager.get_connection_string("proj_123456")

            assert result == "postgresql://user:pass@host:5432/neondb"

    @pytest.mark.asyncio
    async def test_get_connection_string_error(self, project_manager):
        """Test connection string retrieval with error."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 404
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value="Not Found"
            )

            with pytest.raises(NeonAPIError):
                await project_manager.get_connection_string("nonexistent")
