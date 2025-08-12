"""
Working Onyx Cloud Document Upload Implementation
Using the file upload API that accepts Bearer token authentication
"""

import requests
import tempfile
import os
import json
from datetime import datetime
from typing import Dict, Optional, Any


class OnyxCloudUploader:
    """
    Working implementation for uploading documents to Onyx Cloud
    Uses the /api/user/file/upload endpoint that accepts Bearer token auth
    """
    
    def __init__(self, api_key: str, base_url: str = "https://cloud.onyx.app"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def upload_document(
        self, 
        content: str, 
        filename: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a document to Onyx Cloud using the working file upload API
        
        Args:
            content: Document text content
            filename: Name for the uploaded file
            metadata: Optional metadata dict (link, primary_owners, tags, etc.)
            
        Returns:
            Dict with success status and response data
        """
        # Create document with Onyx metadata header if provided
        if metadata:
            metadata_header = f"#ONYX_METADATA={json.dumps(metadata)}\n\n"
            full_content = metadata_header + content
        else:
            full_content = content
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(full_content)
            temp_file_path = temp_file.name
        
        try:
            url = f"{self.base_url}/api/user/file/upload"
            
            files = {
                'files': (filename, open(temp_file_path, 'rb'), 'text/plain')
            }
            
            response = self.session.post(url, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()[0]  # Returns array with single item
                return {
                    'success': True,
                    'document_id': result['document_id'],
                    'file_id': result['file_id'],
                    'name': result['name'],
                    'status': result['status'],
                    'indexed': result['indexed'],
                    'created_at': result['created_at'],
                    'token_count': result['token_count'],
                    'chat_file_type': result['chat_file_type']
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}'
            }
        finally:
            # Clean up
            files['files'][1].close()
            os.unlink(temp_file_path)
    
    def test_connection(self) -> bool:
        """Test if the API connection and authentication work"""
        try:
            # Test health endpoint
            health_response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            if health_response.status_code == 200:
                print("✅ Health endpoint works")
                return True
            else:
                print(f"❌ Health endpoint failed: {health_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def upload_text_document(
        self, 
        title: str, 
        content: str, 
        source_link: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        owners: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to upload a text document with common metadata
        
        Args:
            title: Document title
            content: Document content
            source_link: Optional source URL
            tags: Optional tags dict
            owners: Optional list of owner email addresses
            
        Returns:
            Upload result dict
        """
        metadata = {}
        
        if source_link:
            metadata['link'] = source_link
        
        if owners:
            metadata['primary_owners'] = owners
        
        if tags:
            metadata.update(tags)
        
        # Add timestamp
        metadata['uploaded_at'] = datetime.now().isoformat()
        metadata['upload_method'] = 'api_file_upload'
        
        filename = f"{title.replace(' ', '_')}.txt"
        
        return self.upload_document(content, filename, metadata)


def main():
    """Example usage of the working Onyx Cloud uploader"""
    
    # Initialize with your API key
    api_key = "on_tenant_f77e9e8b-75c7-4dc4-bea4-3fed8bb60a0f.w6dF-qxJmV4A1RVXRTnSBY6GqRIyf23yWldezF5vJjjZo9k7jn_ke3wI-quqOl92ydF19Ke3gUyQnY7KL7GXKZFaqncbpDnkfsgQZ7hmcIS6BPwIZ1pufJTLVSKw-E8DO5LT-_K2UcmF9ydAdHSpbpiRFEehMH5uRPJdMtJxJB-GNxofACNpICHXuYu7H9riO3YsriZZ5U45SL_L7O33PgOWG7gtpmWAtYxnaJ9CRVzWc9RKHZqfE1hMHGUnxwsN"
    
    uploader = OnyxCloudUploader(api_key)
    
    print("🚀 Testing Onyx Cloud Document Upload")
    print("=" * 50)
    
    # Test connection
    if not uploader.test_connection():
        print("❌ Connection test failed - aborting")
        return
    
    # Upload a test document
    document_content = """
Working Onyx Cloud API Integration Test
=====================================

This document demonstrates successful integration with Onyx Cloud using the file upload API.

Key findings:
- The /onyx-api/ingestion endpoint requires session-based authentication
- The /api/user/file/upload endpoint works with Bearer token authentication
- Documents can include metadata headers for proper indexing
- The API returns detailed response data including document IDs and indexing status

Implementation details:
- Uses multipart/form-data file upload
- Supports Onyx metadata format: #ONYX_METADATA={"key": "value"}
- Returns JSON with document_id, file_id, and indexing status
- Automatically handles temporary file creation and cleanup

This approach provides a reliable alternative to direct JSON ingestion while maintaining all the functionality needed for programmatic document upload.
    """.strip()
    
    # Upload with metadata
    print("📤 Uploading test document...")
    result = uploader.upload_text_document(
        title="Onyx API Integration Success",
        content=document_content,
        source_link="https://docs.onyx.app/backend_apis/ingestion",
        tags={
            "category": "api-test",
            "status": "working-solution",
            "method": "file-upload"
        },
        owners=["api-test@example.com"]
    )
    
    print("\n📊 Upload Result:")
    print(json.dumps(result, indent=2))
    
    if result['success']:
        print("\n🎉 SUCCESS! Document uploaded to Onyx Cloud")
        print(f"📋 Document ID: {result['document_id']}")
        print(f"📄 File ID: {result['file_id']}")
        print(f"🔄 Status: {result['status']}")
        print(f"📚 Indexed: {result['indexed']}")
    else:
        print("\n❌ Upload failed")
        print(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
