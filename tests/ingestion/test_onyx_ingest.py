"""
Test suite for Onyx ingestion functionality.

Tests the document formatting, API integration, and error handling
for the Onyx Cloud ingestion pipeline.
"""

import asyncio
import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from ingestion.onyx_ingest import (
    OnyxDocumentFormatter,
    OnyxCloudIngestor,
    ingest_to_onyx,
    OnyxIngestionError,
)
from onyx.service import OnyxService, OnyxAPIError, OnyxTimeoutError


@pytest.fixture
def sample_document_content():
    """Sample document content for testing."""
    return """
    # Sample Document
    
    This is a test document with multiple sections.
    
    ## Section 1
    
    This is the first section with some content.
    It contains multiple paragraphs for testing chunking.
    
    ## Section 2
    
    This is the second section with different content.
    It also has multiple paragraphs to test the formatting.
    
    ## Conclusion
    
    This concludes our sample document.
    """


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        "author": "Test Author",
        "category": "testing",
        "tags": ["test", "document", "sample"]
    }


class TestOnyxDocumentFormatter:
    """Test cases for the OnyxDocumentFormatter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = OnyxDocumentFormatter()
    
    @pytest.mark.asyncio
    async def test_format_document_basic(self, sample_document_content):
        """Test basic document formatting."""
        file_path = "/test/sample.md"
        
        result = await self.formatter.format_document(
            content=sample_document_content,
            file_path=file_path
        )
        
        # Verify structure
        assert "sections" in result
        assert "document_id" in result
        assert "semantic_identifier" in result
        assert "metadata" in result
        assert "doc_updated_at" in result
        
        # Verify sections
        sections = result["sections"]
        assert isinstance(sections, list)
        assert len(sections) > 0
        
        # Each section should have required fields
        for section in sections:
            assert "text" in section
            assert isinstance(section["text"], str)
            assert len(section["text"].strip()) > 0
    
    @pytest.mark.asyncio
    async def test_format_document_with_metadata(self, sample_document_content, sample_metadata):
        """Test document formatting with custom metadata."""
        file_path = "/test/sample.md"
        document_id = "test-doc-123"
        
        result = await self.formatter.format_document(
            content=sample_document_content,
            file_path=file_path,
            document_id=document_id,
            metadata=sample_metadata
        )
        
        # Verify custom values
        assert result["document_id"] == document_id
        assert result["metadata"]["author"] == "Test Author"
        assert "category" in result["metadata"]
    
    @pytest.mark.asyncio
    async def test_format_empty_document(self):
        """Test handling of empty document."""
        with pytest.raises(OnyxIngestionError):
            await self.formatter.format_document(
                content="",
                file_path="/test/empty.txt"
            )
    
    def test_generate_semantic_identifier(self):
        """Test semantic identifier generation."""
        file_path = "/documents/important_report_2024.pdf"
        title = "Important Report 2024"
        
        identifier = self.formatter._generate_semantic_identifier(file_path, title)
        
        assert isinstance(identifier, str)
        assert len(identifier) > 0
        assert "important_report" in identifier.lower()
    
    def test_extract_title_from_content(self):
        """Test title extraction from document content."""
        content = "# Main Title\n\nSome content here"
        
        title = self.formatter._extract_title(content, "/test/doc.md")
        
        assert "Main Title" in title
    
    def test_extract_title_from_filename(self):
        """Test title extraction from filename when no title in content."""
        content = "Just some content without title"
        file_path = "/documents/my_important_document.txt"
        
        title = self.formatter._extract_title(content, file_path)
        
        assert "my_important_document" in title.lower()


class TestOnyxCloudIngestor:
    """Test cases for the OnyxCloudIngestor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create ingestor with mocked service to prevent actual API calls
        with patch('ingestion.onyx_ingest.OnyxService'):
            self.ingestor = OnyxCloudIngestor()
    
    @pytest.mark.asyncio
    @patch('ingestion.onyx_ingest.OnyxService')
    async def test_successful_ingestion(self, mock_onyx_service, sample_document_content):
        """Test successful document ingestion."""
        # Mock the service response
        mock_service_instance = mock_onyx_service.return_value
        mock_service_instance.ingest_document.return_value = {
            "status": "success",
            "document_id": "test-123"
        }
        
        result = await self.ingestor.ingest_document(
            content=sample_document_content,
            file_path="/test/sample.md",
            document_id="test-123"
        )
        
        # Verify success response
        assert result["success"] is True
        assert result["document_id"] == "test-123"
        assert result["attempts"] == 1
        assert "sections_count" in result
    
    @pytest.mark.asyncio
    @patch('ingestion.onyx_ingest.OnyxService')
    async def test_ingestion_with_retry(self, mock_onyx_service, sample_document_content):
        """Test ingestion with retry logic."""
        # Mock service to fail first time, succeed second time
        mock_service_instance = mock_onyx_service.return_value
        mock_service_instance.ingest_document.side_effect = [
            OnyxTimeoutError("Timeout"),
            {"status": "success", "document_id": "test-123"}
        ]
        
        result = await self.ingestor.ingest_document(
            content=sample_document_content,
            file_path="/test/sample.md"
        )
        
        # Verify retry worked
        assert result["success"] is True
        assert result["attempts"] == 2
    
    @pytest.mark.asyncio
    @patch('ingestion.onyx_ingest.OnyxService')
    async def test_ingestion_authentication_error(self, mock_onyx_service, sample_document_content):
        """Test handling of authentication errors (no retry)."""
        # Mock authentication error
        mock_service_instance = mock_onyx_service.return_value
        mock_service_instance.ingest_document.side_effect = OnyxAPIError(
            "Unauthorized", status_code=401
        )
        
        with pytest.raises(OnyxIngestionError) as exc_info:
            await self.ingestor.ingest_document(
                content=sample_document_content,
                file_path="/test/sample.md"
            )
        
        assert "Authentication failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('ingestion.onyx_ingest.OnyxService')
    async def test_ingestion_max_retries_exceeded(self, mock_onyx_service, sample_document_content):
        """Test behavior when max retries are exceeded."""
        # Create ingestor with low retry count for testing
        ingestor = OnyxCloudIngestor(max_retries=2)
        
        # Mock service to always fail
        mock_service_instance = mock_onyx_service.return_value
        mock_service_instance.ingest_document.side_effect = OnyxTimeoutError("Always timeout")
        
        with pytest.raises(OnyxIngestionError) as exc_info:
            await ingestor.ingest_document(
                content=sample_document_content,
                file_path="/test/sample.md"
            )
        
        assert "Failed to ingest document after 3 attempts" in str(exc_info.value)


class TestIngestToOnyxFunction:
    """Test cases for the main ingest_to_onyx function."""
    
    @pytest.mark.asyncio
    @patch('ingestion.onyx_ingest.OnyxCloudIngestor')
    async def test_successful_end_to_end_ingestion(self, mock_ingestor_class, sample_document_content):
        """Test successful end-to-end ingestion workflow."""
        # Mock the ingestor
        mock_ingestor = mock_ingestor_class.return_value
        mock_ingestor.ingest_document.return_value = {
            "success": True,
            "document_id": "test-123",
            "semantic_identifier": "test-doc",
            "sections_count": 3,
            "response": {"status": "ok"},
            "attempts": 1
        }
        
        result = await ingest_to_onyx(
            content=sample_document_content,
            file_path="/test/sample.md"
        )
        
        # Verify result structure
        assert result["success"] is True
        assert result["document_id"] == "test-123"
        assert "processing_time_ms" in result
    
    @pytest.mark.asyncio
    @patch('ingestion.onyx_ingest.OnyxCloudIngestor')
    async def test_ingestion_failure_handling(self, mock_ingestor_class, sample_document_content):
        """Test handling of ingestion failures."""
        # Mock ingestor to raise error
        mock_ingestor = mock_ingestor_class.return_value
        mock_ingestor.ingest_document.side_effect = OnyxIngestionError(
            "Test error", document_path="/test/sample.md"
        )
        
        result = await ingest_to_onyx(
            content=sample_document_content,
            file_path="/test/sample.md"
        )
        
        # Verify error handling
        assert result["success"] is False
        assert "error" in result
        assert "processing_time_ms" in result


class TestOnyxServiceIntegration:
    """Integration tests for OnyxService with mocked HTTP responses."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock environment variables for config
        with patch.dict(os.environ, {
            "ONYX_API_KEY": "test-key",
            "ONYX_BASE_URL": "https://test.onyx.app",
            "ONYX_TIMEOUT": "30"
        }):
            self.service = OnyxService()
    
    @patch('onyx.service.requests.Session.request')
    def test_ingest_document_api_call(self, mock_request):
        """Test that ingest_document makes correct API call."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "id": "doc-123"}
        mock_request.return_value = mock_response
        
        sections = [
            {"text": "Section 1 content"},
            {"text": "Section 2 content", "link": "https://example.com"}
        ]
        
        result = self.service.ingest_document(
            sections=sections,
            document_id="test-doc",
            semantic_identifier="Test Document"
        )
        
        # Verify the API call
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        
        # Check request details
        assert call_args[0][0] == "POST"  # method
        assert "/onyx-api/ingestion" in call_args[0][1]  # URL
        
        # Check payload structure
        # The payload should be in the 'json' parameter
        payload = call_args[1]["json"]
        assert "document" in payload
        assert "cc_pair_id" in payload
        assert payload["document"]["sections"] == sections
        assert payload["document"]["id"] == "test-doc"
    
    @patch('onyx.service.requests.Session.request')
    def test_ingest_document_error_handling(self, mock_request):
        """Test error handling in ingest_document."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_response.text = "Bad Request"
        mock_request.return_value = mock_response
        
        sections = [{"text": "Test content"}]
        
        with pytest.raises(OnyxAPIError) as exc_info:
            self.service.ingest_document(sections=sections)
        
        assert exc_info.value.status_code == 400
    
    def test_ingest_document_validation(self):
        """Test input validation in ingest_document."""
        # Test empty sections
        with pytest.raises(ValueError):
            self.service.ingest_document(sections=[])
        
        # Test invalid section format
        with pytest.raises(ValueError):
            self.service.ingest_document(sections=[{"no_text": "invalid"}])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
