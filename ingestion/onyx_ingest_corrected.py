"""
Onyx Cloud document ingestion module - CORRECTED BASED ON SLACK DISCUSSION

This module provides functionality to ingest documents directly into Onyx Cloud
using the CORRECT ingestion API flow as documented in the Slack discussion.

Based on slack_discussion.md findings from Onyx team members:
- Use /onyx-api/ingestion endpoint for programmatic document upload
- Set up proper connector/credential/document-set flow
- Use Bearer token authentication as confirmed by the team
"""

import os
import json
import logging
import asyncio
import time
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

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


class OnyxConnectorManager:
    """
    Manages Onyx Cloud connectors, credentials, and document sets.
    
    Based on Slack discussion recommendations for programmatic setup.
    """
    
    def __init__(self):
        """Initialize connector manager with Onyx service."""
        self.onyx_service = OnyxService()
        
    async def setup_file_connector(self, connector_name: str = "Hybrid_RAG_Connector") -> Dict[str, Any]:
        """
        Set up a file connector following the Slack discussion workflow.
        
        Returns connector details including connector_id and document_set_id
        """
        try:
            logger.info(f"🔧 Setting up file connector: {connector_name}")
            
            # Step 1: Create file connector (POST manage/admin/connector)
            connector_payload = {
                "name": connector_name,
                "source": "file",
                "connector_specific_config": {},
                "refresh_freq": None,
                "prune_freq": None,
                "indexing_start": None,
                "access_type": "public",  # or "private" for user-specific
                "groups": []
            }
            
            connector_response = self.onyx_service._make_request(
                "POST", 
                "/api/manage/admin/connector", 
                json=connector_payload
            )
            connector_id = connector_response.get("id")
            logger.info(f"✅ Created connector: {connector_id}")
            
            # Step 2: Create credential (POST manage/credentials) 
            # File connectors typically don't need special credentials
            credential_payload = {
                "credential_json": {},
                "admin_public": True
            }
            
            credential_response = self.onyx_service._make_request(
                "POST",
                "/api/manage/credentials", 
                json=credential_payload
            )
            credential_id = credential_response.get("id")
            logger.info(f"✅ Created credential: {credential_id}")
            
            # Step 3: Create connector-credential pair
            pair_payload = {
                "name": connector_name,
                "access_type": "public",
                "groups": [],
                "auto_sync_options": None
            }
            
            self.onyx_service._make_request(
                "PUT",
                f"/api/manage/connector/{connector_id}/credential/{credential_id}",
                json=pair_payload
            )
            logger.info(f"✅ Linked connector {connector_id} with credential {credential_id}")
            
            # Step 4: Create document set (POST manage/admin/document-set)
            document_set_payload = {
                "name": f"{connector_name}_DocumentSet",
                "description": f"Document set for {connector_name}",
                "cc_pair_ids": [{"connector_id": connector_id, "credential_id": credential_id}],
                "is_public": True,
                "users": [],
                "groups": []
            }
            
            doc_set_response = self.onyx_service._make_request(
                "POST",
                "/api/manage/admin/document-set",
                json=document_set_payload
            )
            document_set_id = doc_set_response.get("id")
            logger.info(f"✅ Created document set: {document_set_id}")
            
            return {
                "connector_id": connector_id,
                "credential_id": credential_id, 
                "document_set_id": document_set_id,
                "connector_name": connector_name
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to setup connector: {e}")
            raise OnyxIngestionError(f"Connector setup failed: {str(e)}", original_error=e)


class OnyxDocumentFormatter:
    """
    Handles document formatting for the Onyx ingestion API.
    
    Based on the official ingestion API format from slack discussion.
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
        metadata: Optional[Dict[str, Any]] = None,
        cc_pair_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Format a document for Onyx ingestion API.
        
        Following the official format from slack_discussion.md:
        {
          "document": {
            "id": "ingestion_document_1",
            "sections": [...],
            "source": "FILE",
            "semantic_identifier": "Document Title",
            "metadata": {...},
            "doc_updated_at": "2024-04-25T08:20:00Z"
          },
          "cc_pair_id": 1
        }
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
            
            # Format according to official ingestion API structure
            ingestion_payload = {
                "document": {
                    "id": document_id,
                    "sections": sections,
                    "source": "FILE",  # As used in examples
                    "semantic_identifier": semantic_identifier,
                    "metadata": formatted_metadata,
                    "doc_updated_at": datetime.now().isoformat() + "Z"
                }
            }
            
            # Add cc_pair_id if provided
            if cc_pair_id:
                ingestion_payload["cc_pair_id"] = cc_pair_id
            
            return ingestion_payload
            
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
                # Format sections according to official API spec
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
        """Format metadata for Onyx ingestion."""
        metadata = {
            "source_file": os.path.basename(file_path),
            "file_path": file_path,
            "file_size": len(content),
            "ingestion_date": datetime.now().isoformat(),
            "word_count": len(content.split()),
            "line_count": len(content.split("\n")),
            "ingestion_source": "hybrid_rag_system",
            "ingestion_method": "official_api"
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return metadata


class OnyxCloudIngestor:
    """
    Handles document ingestion to Onyx Cloud using the CORRECT ingestion API.
    
    Based on slack_discussion.md findings:
    - Uses /onyx-api/ingestion endpoint (confirmed by Onyx team)
    - Follows proper connector setup workflow
    - Uses Bearer token authentication
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0, timeout: int = 30):
        """Initialize Onyx Cloud ingestor with retry configuration."""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.onyx_service = OnyxService()
        self.formatter = OnyxDocumentFormatter()
        self.connector_manager = OnyxConnectorManager()
        
        # Cache for connector setup
        self._connector_setup = None
        
        logger.info(f"Initialized Onyx Cloud ingestor using official ingestion API")
    
    async def ensure_connector_setup(self) -> Dict[str, Any]:
        """Ensure connector is set up and return details."""
        if not self._connector_setup:
            try:
                self._connector_setup = await self.connector_manager.setup_file_connector()
                logger.info(f"✅ Connector setup complete: {self._connector_setup}")
            except Exception as e:
                logger.warning(f"⚠️ Connector setup failed, will try without cc_pair_id: {e}")
                self._connector_setup = {"connector_id": None}
        
        return self._connector_setup
    
    async def ingest_document(
        self,
        content: str,
        file_path: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a single document to Onyx Cloud using the official ingestion API.
        
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
        logger.info(f"Starting Onyx Cloud ingestion for: {os.path.basename(file_path)}")
        
        try:
            # Ensure connector setup
            connector_setup = await self.ensure_connector_setup()
            
            # Format document for ingestion API
            formatted_doc = await self.formatter.format_document(
                content=content,
                file_path=file_path,
                document_id=document_id,
                metadata=metadata,
                cc_pair_id=connector_setup.get("connector_id")
            )
            
            # Attempt ingestion with retry logic
            result = await self._ingest_with_retry(formatted_doc, file_path)
            
            logger.info(f"Successfully ingested to Onyx Cloud: {formatted_doc['document']['semantic_identifier']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to ingest document {file_path}: {e}")
            raise OnyxIngestionError(
                f"Document ingestion failed: {str(e)}",
                document_path=file_path,
                original_error=e
            )
    
    async def _ingest_with_retry(self, formatted_doc: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Perform ingestion with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Ingestion attempt {attempt + 1}/{self.max_retries + 1} for {os.path.basename(file_path)}")
                
                # Perform actual ingestion using official API
                ingestion_response = await self._ingest_via_official_api(formatted_doc)
                
                # Success - return the response
                return {
                    "success": True,
                    "document_id": ingestion_response.get("document_id", formatted_doc["document"]["id"]),
                    "semantic_identifier": formatted_doc["document"]["semantic_identifier"],
                    "sections_count": len(formatted_doc["document"]["sections"]),
                    "response": ingestion_response,
                    "attempts": attempt + 1,
                    "ingestion_method": "official_api"
                }
                
            except OnyxTimeoutError as e:
                last_exception = e
                logger.warning(f"Ingestion timeout on attempt {attempt + 1} for {os.path.basename(file_path)}: {e}")
                
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
                        f"Client error during ingestion: {str(e)}",
                        document_path=file_path,
                        retry_count=attempt,
                        original_error=e
                    )
                
                logger.warning(f"Ingestion API error on attempt {attempt + 1} for {os.path.basename(file_path)}: {e}")
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Unexpected ingestion error on attempt {attempt + 1} for {os.path.basename(file_path)}: {e}")
            
            # If we have more attempts, wait with exponential backoff
            if attempt < self.max_retries:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.info(f"Waiting {wait_time:.1f}s before retry attempt {attempt + 2}")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        raise OnyxIngestionError(
            f"Failed to ingest document after {self.max_retries + 1} attempts: {str(last_exception)}",
            document_path=file_path,
            retry_count=self.max_retries,
            original_error=last_exception
        )
    
    async def _ingest_via_official_api(self, formatted_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest document using the official /onyx-api/ingestion endpoint.
        
        This method uses the correct ingestion API as confirmed by the Onyx team.
        """
        try:
            logger.info(f"Ingesting via official API: {formatted_doc['document']['semantic_identifier']}")
            
            # Use the official ingestion API
            response_data = self.onyx_service._make_request(
                "POST", 
                "/onyx-api/ingestion", 
                json=formatted_doc,
                timeout=self.timeout
            )
            
            logger.info(f"Official ingestion API successful: {response_data}")
            return response_data
                    
        except requests.exceptions.Timeout:
            raise OnyxTimeoutError(f"Ingestion timed out after {self.timeout} seconds")
        except Exception as e:
            raise OnyxAPIError(f"Official ingestion API failed: {e}")


async def ingest_to_onyx(
    content: str,
    file_path: str,
    document_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Main function to ingest a document to Onyx Cloud using the OFFICIAL ingestion API.
    
    This is the corrected implementation based on slack_discussion.md research
    that uses the confirmed working /onyx-api/ingestion endpoint with proper setup.
    
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
            - ingestion_method: "official_api" to indicate the method used
    
    Raises:
        OnyxIngestionError: If ingestion fails after all retries
    """
    start_time = datetime.now()
    
    logger.info(f"Starting Onyx Cloud ingestion for: {os.path.basename(file_path)}")
    
    try:
        # Initialize ingestor with correct official API
        ingestor = OnyxCloudIngestor(max_retries=max_retries)
        
        # Perform ingestion using official API
        result = await ingestor.ingest_document(
            content=content,
            file_path=file_path,
            document_id=document_id,
            metadata=metadata
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        result["processing_time_ms"] = processing_time
        
        logger.info(f"Document successfully ingested to Onyx Cloud in {processing_time:.0f}ms")
        logger.info(f"   Document ID: {result['document_id']}")
        logger.info(f"   Semantic ID: {result['semantic_identifier']}")
        logger.info(f"   Sections: {result['sections_count']}, Attempts: {result['attempts']}")
        
        return result
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Onyx Cloud ingestion failed after {processing_time:.0f}ms: {e}")
        
        # Return detailed failure result instead of raising exception
        return {
            "success": False,
            "document_id": document_id or f"failed_{int(time.time())}",
            "semantic_identifier": os.path.basename(file_path),
            "sections_count": 0,
            "processing_time_ms": processing_time,
            "attempts": 1,
            "error": str(e),
            "ingestion_method": "official_api"
        }


async def test_onyx_ingestion(
    test_content: str,
    test_filename: str = "TEST_SAFE_TO_DELETE_official_api.md"
) -> bool:
    """
    Test Onyx Cloud ingestion with the corrected official API implementation.
    
    Args:
        test_content: Sample content to test with
        test_filename: Filename for the test document (clearly marked as test)
    
    Returns:
        Boolean indicating success of the test
    """
    logger.info(f"Testing CORRECTED Onyx Cloud ingestion with official API")
    
    try:
        # Create test file path with clear test identifier
        test_file_path = os.path.join("documents", test_filename)
        
        # Use clearly identifiable test metadata
        test_metadata = {
            "test_document": True,
            "safe_to_delete": True,
            "implementation": "official_ingestion_api",
            "based_on": "slack_discussion_findings",
            "test_timestamp": datetime.now().isoformat(),
            "warning": "THIS_IS_A_TEST_DOCUMENT_SAFE_TO_DELETE"
        }
        
        # Test ingestion with corrected implementation
        result = await ingest_to_onyx(
            content=test_content,
            file_path=test_file_path,
            document_id=f"TEST_OFFICIAL_API_{int(time.time())}",
            metadata=test_metadata
        )
        
        if result["success"]:
            logger.info(f"Test ingestion successful: {result['semantic_identifier']}")
            logger.info(f"   Document ID: {result['document_id']}")
            logger.info(f"   Sections: {result['sections_count']}, Time: {result['processing_time_ms']:.0f}ms")
            logger.info(f"   Ingestion Method: {result['ingestion_method']}")
            return True
        else:
            logger.error(f"Test ingestion failed: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        logger.error(f"Test ingestion failed: {e}")
        return False


if __name__ == "__main__":
    # Test content with clear test markers
    test_content = """# [TEST-OFFICIAL-API] Onyx Official Ingestion API Test

**THIS IS A TEST DOCUMENT - SAFE TO DELETE**

This document tests the CORRECTED Onyx Cloud ingestion implementation using
the official /onyx-api/ingestion endpoint as documented in slack_discussion.md.

## Implementation Changes

### What We Fixed
- Using `/onyx-api/ingestion` endpoint (official API)
- Proper connector/credential setup workflow
- Bearer token authentication (confirmed by Onyx team)  
- Official document structure format

### Slack Discussion Findings
- File upload API was not the correct approach
- Official ingestion API requires proper connector setup
- Onyx team confirmed the correct workflow
- API documentation improvements coming end of August 2025

## Test Verification
This document verifies that:
1. Official ingestion API integration works correctly
2. Connector setup workflow functions properly
3. Documents are properly formatted per official spec
4. Metadata is preserved in the ingested document
5. Error handling functions as expected

---
**Status**: CORRECTED IMPLEMENTATION BASED ON SLACK DISCUSSION
**Safe to Delete**: YES
"""
    
    async def main():
        """Test the corrected ingestion functionality."""
        print("Testing CORRECTED Onyx Cloud ingestion with official API...")
        success = await test_onyx_ingestion(test_content)
        if success:
            print("SUCCESS: Corrected Onyx Cloud ingestion test passed!")
        else:
            print("FAILED: Corrected Onyx Cloud ingestion test failed!")
        return success
    
    # Run the test
    asyncio.run(main())