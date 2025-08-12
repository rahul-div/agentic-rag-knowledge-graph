"""
Onyx Cloud document ingestion module - CORRECTED IMPLEMENTATION

This module provides functionality to ingest documents directly into Onyx Cloud
using the WORKING file upload API based on official documentation research.

Based on ONYX_CLOUD_API_GUIDE.md findings:
- The /onyx-api/ingestion endpoint returns HTML (requires session authentication)
- The /api/user/file/upload endpoint WORKS with Bearer token authentication
- Official documentation: https://docs.onyx.app/backend_apis/ingestion
"""

import os
import json
import logging
import asyncio
import time
import tempfile
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Import Onyx service for configuration
from onyx.service import OnyxService, OnyxAPIError, OnyxTimeoutError

# Import ingestion utilities  
from .chunker import create_chunker, ChunkingConfig, DocumentChunk

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class OnyxIngestionError(Exception):
    """Custom exception for Onyx ingestion errors."""
    
    def __init__(
        self,
        message: str,
        document_path: Optional[str] = None,
        retry_count: int = 0,
        original_error: Optional[Exception] = None
    ):
        self.document_path = document_path
        self.retry_count = retry_count
        self.original_error = original_error
        super().__init__(message)


class OnyxDocumentFormatter:
    """
    Handles document formatting for Onyx file upload API.
    
    Converts local documents into the format expected by the working 
    /api/user/file/upload endpoint with proper metadata headers.
    """
    
    def __init__(self, chunking_config: Optional[ChunkingConfig] = None):
        """Initialize document formatter with optional chunking configuration."""
        self.chunking_config = chunking_config or ChunkingConfig(
            chunk_size=800,
            chunk_overlap=150,
            max_chunk_size=2000,
            use_semantic_splitting=True
        )
        self.chunker = create_chunker(self.chunking_config)
    
    async def format_document(
        self,
        content: str,
        file_path: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format a document for Onyx Cloud file upload API.
        
        Args:
            content: Raw document content
            file_path: Path to the original file
            document_id: Optional custom document ID
            metadata: Additional metadata for the document
        
        Returns:
            Dict containing formatted document data for file upload
        """
        try:
            # Extract basic document information
            document_title = self._extract_title(content, file_path)
            semantic_identifier = self._generate_semantic_identifier(file_path, document_title)
            
            # Create document sections using chunking
            sections = await self._create_sections(content, document_title, file_path)
            
            if not sections:
                raise OnyxIngestionError(
                    f"No sections created for document: {document_title}",
                    document_path=file_path
                )
            
            # Prepare document metadata
            formatted_metadata = self._format_metadata(content, file_path, metadata)
            
            # Generate document ID if not provided
            if not document_id:
                document_id = self._generate_document_id(file_path)
            
            logger.info(f"Formatted document '{document_title}' with {len(sections)} sections")
            
            return {
                "sections": sections,
                "document_id": document_id,
                "semantic_identifier": semantic_identifier,
                "metadata": formatted_metadata,
                "doc_updated_at": datetime.now().isoformat() + "Z",
                "full_content": self._combine_sections(sections)
            }
            
        except Exception as e:
            logger.error(f"Failed to format document {file_path}: {e}")
            raise OnyxIngestionError(
                f"Document formatting failed: {str(e)}",
                document_path=file_path,
                original_error=e
            )
    
    async def _create_sections(self, content: str, title: str, file_path: str) -> List[Dict[str, str]]:
        """Create document sections using the chunking strategy."""
        try:
            chunks = await self.chunker.chunk_document(
                content=content,
                title=title,
                source=os.path.relpath(file_path, "documents"),
                metadata={"file_path": file_path}
            )
            
            sections = []
            for chunk in chunks:
                section = {
                    "text": chunk.content,
                    "link": f"file://{file_path}#chunk_{chunk.index}"
                }
                sections.append(section)
            
            return sections
            
        except Exception as e:
            logger.error(f"Failed to create sections for {file_path}: {e}")
            # Fallback: create a single section from the entire content
            return [{"text": content, "link": f"file://{file_path}"}]
    
    def _combine_sections(self, sections: List[Dict[str, str]]) -> str:
        """Combine sections into a single document for file upload."""
        return "\n\n".join(section["text"] for section in sections)
    
    def _extract_title(self, content: str, file_path: str) -> str:
        """Extract title from document content or filename."""
        lines = content.split("\n")
        for line in lines[:10]:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return os.path.splitext(os.path.basename(file_path))[0]
    
    def _generate_semantic_identifier(self, file_path: str, title: str) -> str:
        """Generate a human-readable semantic identifier."""
        filename = os.path.basename(file_path)
        if title and title != os.path.splitext(filename)[0]:
            return f"{filename}: {title}"
        return filename
    
    def _generate_document_id(self, file_path: str) -> str:
        """Generate a unique document ID based on file path and timestamp."""
        filename = os.path.basename(file_path)
        timestamp = int(time.time())
        return f"hybrid_rag_{filename}_{timestamp}"
    
    def _format_metadata(
        self,
        content: str,
        file_path: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format metadata for Onyx file upload."""
        metadata = {
            "source_file": os.path.basename(file_path),
            "file_path": file_path,
            "file_size": len(content),
            "ingestion_date": datetime.now().isoformat(),
            "word_count": len(content.split()),
            "line_count": len(content.split("\n")),
            "ingestion_source": "hybrid_rag_system",
            "upload_method": "file_api"
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return metadata


class OnyxCloudIngestor:
    """
    Handles document ingestion to Onyx Cloud using the working file upload API.
    
    Based on ONYX_CLOUD_API_GUIDE.md research:
    - Uses /api/user/file/upload endpoint (confirmed working)
    - Bearer token authentication
    - Proper error handling and retry logic
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0, timeout: int = 30):
        """Initialize Onyx Cloud ingestor with retry configuration."""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.onyx_service = OnyxService()
        self.formatter = OnyxDocumentFormatter()
        
        logger.info(f"Initialized Onyx Cloud ingestor using file upload API")
    
    async def ingest_document(
        self,
        content: str,
        file_path: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a single document to Onyx Cloud using the working file upload API.
        
        Args:
            content: Document content to ingest
            file_path: Path to the source file
            document_id: Optional custom document ID
            metadata: Additional metadata for the document
        
        Returns:
            Dict containing ingestion result and response data
        
        Raises:
            OnyxIngestionError: If ingestion fails after all retries
        """
        logger.info(f"Starting Onyx Cloud file upload for: {os.path.basename(file_path)}")
        
        try:
            # Format document for file upload
            formatted_doc = await self.formatter.format_document(
                content=content,
                file_path=file_path,
                document_id=document_id,
                metadata=metadata
            )
            
            # Attempt upload with retry logic
            result = await self._upload_with_retry(formatted_doc, file_path)
            
            logger.info(f"Successfully uploaded to Onyx Cloud: {formatted_doc['semantic_identifier']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to upload document {file_path}: {e}")
            raise OnyxIngestionError(
                f"Document upload failed: {str(e)}",
                document_path=file_path,
                original_error=e
            )
    
    async def _upload_with_retry(self, formatted_doc: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Perform file upload with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Upload attempt {attempt + 1}/{self.max_retries + 1} for {os.path.basename(file_path)}")
                
                # Perform actual file upload
                upload_response = await self._upload_via_file_api(formatted_doc)
                
                # Success - return the response
                return {
                    "success": True,
                    "document_id": upload_response.get("document_id", formatted_doc["document_id"]),
                    "semantic_identifier": formatted_doc["semantic_identifier"],
                    "sections_count": len(formatted_doc["sections"]),
                    "response": upload_response,
                    "attempts": attempt + 1,
                    "upload_method": "file_api"
                }
                
            except OnyxTimeoutError as e:
                last_exception = e
                logger.warning(f"Upload timeout on attempt {attempt + 1} for {os.path.basename(file_path)}: {e}")
                
            except OnyxAPIError as e:
                last_exception = e
                
                # Don't retry on authentication errors
                if e.status_code == 401:
                    raise OnyxIngestionError(
                        f"Authentication failed for Onyx Cloud: {str(e)}",
                        document_path=file_path,
                        original_error=e
                    )
                
                # Don't retry on client errors (4xx)
                if e.status_code and 400 <= e.status_code < 500:
                    logger.error(f"Client error (HTTP {e.status_code}) for {os.path.basename(file_path)}: {e}")
                    raise OnyxIngestionError(
                        f"Client error during file upload: {str(e)}",
                        document_path=file_path,
                        retry_count=attempt,
                        original_error=e
                    )
                
                logger.warning(f"Upload API error on attempt {attempt + 1} for {os.path.basename(file_path)}: {e}")
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Unexpected upload error on attempt {attempt + 1} for {os.path.basename(file_path)}: {e}")
            
            # If we have more attempts, wait with exponential backoff
            if attempt < self.max_retries:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.info(f"Waiting {wait_time:.1f}s before retry attempt {attempt + 2}")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        raise OnyxIngestionError(
            f"Failed to upload document after {self.max_retries + 1} attempts: {str(last_exception)}",
            document_path=file_path,
            retry_count=self.max_retries,
            original_error=last_exception
        )
    
    async def _upload_via_file_api(self, formatted_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload document using the working /api/user/file/upload endpoint.
        
        This method uses the file upload API which accepts Bearer token authentication
        and returns proper JSON responses, unlike the direct ingestion API.
        """
        try:
            # Prepare document content with Onyx metadata header
            metadata_header = ""
            if formatted_doc.get("metadata"):
                metadata_header = f"#ONYX_METADATA={json.dumps(formatted_doc['metadata'])}\n\n"
            
            # Create full content with metadata
            full_content = metadata_header + formatted_doc["full_content"]
            
            # Create temporary file
            filename = f"{formatted_doc['semantic_identifier']}.md"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
                temp_file.write(full_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload using the working file API
                url = f"{self.onyx_service.base_url}/api/user/file/upload"
                headers = {'Authorization': f'Bearer {self.onyx_service.api_key}'}
                
                with open(temp_file_path, 'rb') as f:
                    files = {'files': (filename, f, 'text/markdown')}
                    
                    logger.info(f"Uploading via file API: {filename}")
                    response = requests.post(url, headers=headers, files=files, timeout=self.timeout)
                
                # Handle response
                if response.status_code == 200:
                    try:
                        data = response.json()[0]  # API returns array with single item
                        logger.info(f"File uploaded successfully: {data.get('document_id')}")
                        return data
                    except (ValueError, IndexError, KeyError) as e:
                        raise OnyxAPIError(f"Invalid response format from file upload API: {e}")
                else:
                    raise OnyxAPIError(
                        f"File upload failed: {response.status_code} {response.reason}",
                        status_code=response.status_code
                    )
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except requests.exceptions.Timeout:
            raise OnyxTimeoutError(f"File upload timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise OnyxAPIError(f"File upload request failed: {e}")


async def ingest_to_onyx(
    content: str,
    file_path: str,
    document_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Main function to ingest a document to Onyx Cloud using the WORKING file upload API.
    
    This is the corrected implementation based on ONYX_CLOUD_API_GUIDE.md research
    that uses the confirmed working /api/user/file/upload endpoint.
    
    Args:
        content: Document content to ingest
        file_path: Path to the source file
        document_id: Optional custom document ID
        metadata: Additional metadata for the document
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        Dict containing ingestion results:
            - success: Boolean indicating success
            - document_id: Generated or provided document ID
            - semantic_identifier: Human-readable identifier
            - sections_count: Number of sections created
            - attempts: Number of attempts made
            - processing_time_ms: Processing time in milliseconds
            - upload_method: "file_api" to indicate the method used
    
    Raises:
        OnyxIngestionError: If ingestion fails after all retries
    """
    start_time = datetime.now()
    
    logger.info(f"Starting Onyx Cloud upload for: {os.path.basename(file_path)}")
    
    try:
        # Initialize ingestor with correct file upload API
        ingestor = OnyxCloudIngestor(max_retries=max_retries)
        
        # Perform upload using working API
        result = await ingestor.ingest_document(
            content=content,
            file_path=file_path,
            document_id=document_id,
            metadata=metadata
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        result["processing_time_ms"] = processing_time
        
        logger.info(f"Document successfully uploaded to Onyx Cloud in {processing_time:.0f}ms")
        logger.info(f"   Document ID: {result['document_id']}")
        logger.info(f"   Semantic ID: {result['semantic_identifier']}")
        logger.info(f"   Sections: {result['sections_count']}, Attempts: {result['attempts']}")
        
        return result
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Onyx Cloud upload failed after {processing_time:.0f}ms: {e}")
        
        # Return detailed failure result instead of raising exception
        return {
            "success": False,
            "document_id": document_id or f"failed_{int(time.time())}",
            "semantic_identifier": os.path.basename(file_path),
            "sections_count": 0,
            "processing_time_ms": processing_time,
            "attempts": 1,
            "error": str(e),
            "upload_method": "file_api"
        }


async def test_onyx_ingestion(
    test_content: str,
    test_filename: str = "TEST_SAFE_TO_DELETE_corrected_onyx.md"
) -> bool:
    """
    Test Onyx Cloud ingestion with sample content using the corrected implementation.
    
    Args:
        test_content: Sample content to test with
        test_filename: Filename for the test document (clearly marked as test)
    
    Returns:
        Boolean indicating success of the test
    """
    logger.info(f"Testing corrected Onyx Cloud ingestion implementation")
    
    try:
        # Create test file path with clear test identifier
        test_file_path = os.path.join("documents", test_filename)
        
        # Use clearly identifiable test metadata
        test_metadata = {
            "test_document": True,
            "safe_to_delete": True,
            "implementation": "corrected_file_upload_api",
            "test_timestamp": datetime.now().isoformat(),
            "warning": "THIS_IS_A_TEST_DOCUMENT_SAFE_TO_DELETE"
        }
        
        # Test upload with corrected implementation
        result = await ingest_to_onyx(
            content=test_content,
            file_path=test_file_path,
            document_id=f"TEST_CORRECTED_{int(time.time())}",
            metadata=test_metadata
        )
        
        if result["success"]:
            logger.info(f"Test upload successful: {result['semantic_identifier']}")
            logger.info(f"   Document ID: {result['document_id']}")
            logger.info(f"   Sections: {result['sections_count']}, Time: {result['processing_time_ms']:.0f}ms")
            logger.info(f"   Upload Method: {result['upload_method']}")
            return True
        else:
            logger.error(f"Test upload failed: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        logger.error(f"Test upload failed: {e}")
        return False


if __name__ == "__main__":
    # Test content with clear test markers
    test_content = """# [TEST-CORRECTED-IMPLEMENTATION] Onyx File Upload API Test

**THIS IS A TEST DOCUMENT - SAFE TO DELETE**

This document tests the corrected Onyx Cloud ingestion implementation using
the working file upload API endpoint identified in ONYX_CLOUD_API_GUIDE.md.

## Implementation Details

### What Changed
- Using `/api/user/file/upload` endpoint (confirmed working)
- Bearer token authentication (verified functional)
- Proper file handling with temporary files
- Structured error handling and retry logic

### API Research Results
- Official ingestion endpoint `/onyx-api/ingestion` returns HTML (session auth required)
- File upload endpoint `/api/user/file/upload` accepts Bearer tokens
- Returns proper JSON responses with document metadata
- Supports Onyx metadata headers in uploaded files

## Test Verification
This document verifies that:
1. File upload API integration works correctly
2. Bearer token authentication is accepted
3. Documents are properly formatted and uploaded
4. Metadata is preserved in the uploaded document
5. Error handling functions as expected

---
**Status**: CORRECTED IMPLEMENTATION BASED ON OFFICIAL DOCUMENTATION
**Safe to Delete**: YES
"""
    
    async def main():
        """Test the corrected ingestion functionality."""
        print("Testing corrected Onyx Cloud ingestion implementation...")
        success = await test_onyx_ingestion(test_content)
        if success:
            print("SUCCESS: Corrected Onyx Cloud ingestion test passed!")
        else:
            print("FAILED: Corrected Onyx Cloud ingestion test failed!")
        return success
    
    # Run the test
    asyncio.run(main())