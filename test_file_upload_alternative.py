#!/usr/bin/env python3
"""
Test Onyx Cloud File Upload API as Alternative to Direct Ingestion
"""

import requests
import json
import tempfile
import os
from datetime import datetime

def test_file_upload_api():
    """Test the file upload API that accepts our authentication"""
    base_url = 'https://cloud.onyx.app'
    api_key = "on_tenant_f77e9e8b-75c7-4dc4-bea4-3fed8bb60a0f.w6dF-qxJmV4A1RVXRTnSBY6GqRIyf23yWldezF5vJjjZo9k7jn_ke3wI-quqOl92ydF19Ke3gUyQnY7KL7GXKZFaqncbpDnkfsgQZ7hmcIS6BPwIZ1pufJTLVSKw-E8DO5LT-_K2UcmF9ydAdHSpbpiRFEehMH5uRPJdMtJxJB-GNxofACNpICHXuYu7H9riO3YsriZZ5U45SL_L7O33PgOWG7gtpmWAtYxnaJ9CRVzWc9RKHZqfE1hMHGUnxwsN"
    
    print("📁 Testing File Upload API as Alternative")
    print("🔗 Endpoint: /api/user/file/upload")
    print("=" * 50)
    
    # Create a test document with metadata header
    document_content = """#ONYX_METADATA={"link": "https://docs.onyx.app/backend_apis/ingestion", "primary_owners": ["api-test@example.com"], "tag": "api-test", "test_type": "file_upload_alternative"}

Test Document via File Upload API
==================================

This document is being uploaded via the /api/user/file/upload endpoint as an alternative to the direct ingestion API that's currently returning HTML login pages.

Content:
- Testing programmatic document upload
- Using file upload instead of direct JSON ingestion
- Following Onyx metadata format for file uploads
- Timestamp: """ + datetime.now().isoformat() + """

This approach may work around the session-based authentication issue we're experiencing with the /onyx-api/ingestion endpoint.
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write(document_content)
        temp_file_path = temp_file.name
    
    try:
        url = f"{base_url}/api/user/file/upload"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            # Don't set Content-Type for multipart/form-data - requests will set it
        }
        
        # Prepare file for upload
        files = {
            'files': ('test_document.txt', open(temp_file_path, 'rb'), 'text/plain')
        }
        
        print(f"📤 Uploading file to: {url}")
        print(f"📄 File size: {len(document_content)} characters")
        print(f"🏷️  Metadata included in file header")
        
        response = requests.post(url, headers=headers, files=files, timeout=30)
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        content_type = response.headers.get('content-type', '').lower()
        print(f"📄 Content Type: {content_type}")
        
        if 'application/json' in content_type:
            try:
                result = response.json()
                print(f"✅ JSON Response: {json.dumps(result, indent=2)}")
                
                if response.status_code in [200, 201]:
                    print("🎉 SUCCESS: File uploaded successfully!")
                    return True
                elif response.status_code == 422:
                    print("⚠️  Validation error - check required fields")
                    return False
                else:
                    print(f"⚠️  Unexpected status: {response.status_code}")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"📝 Raw response: {response.text}")
                return False
        else:
            print(f"❌ Non-JSON response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    finally:
        # Clean up temporary file
        files['files'][1].close()
        os.unlink(temp_file_path)

def test_link_creation_api():
    """Test the create-from-link API"""
    base_url = 'https://cloud.onyx.app'
    api_key = "on_tenant_f77e9e8b-75c7-4dc4-bea4-3fed8bb60a0f.w6dF-qxJmV4A1RVXRTnSBY6GqRIyf23yWldezF5vJjjZo9k7jn_ke3wI-quqOl92ydF19Ke3gUyQnY7KL7GXKZFaqncbpDnkfsgQZ7hmcIS6BPwIZ1pufJTLVSKw-E8DO5LT-_K2UcmF9ydAdHSpbpiRFEehMH5uRPJdMtJxJB-GNxofACNpICHXuYu7H9riO3YsriZZ5U45SL_L7O33PgOWG7gtpmWAtYxnaJ9CRVzWc9RKHZqfE1hMHGUnxwsN"
    
    print("\n🔗 Testing Link Creation API")
    print("🔗 Endpoint: /api/user/file/create-from-link")
    print("=" * 50)
    
    url = f"{base_url}/api/user/file/create-from-link"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test with a public URL
    payload = {
        "link": "https://docs.onyx.app/backend_apis/ingestion"
    }
    
    print(f"📤 Creating document from URL: {payload['link']}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📥 Response Status: {response.status_code}")
        content_type = response.headers.get('content-type', '').lower()
        print(f"📄 Content Type: {content_type}")
        
        if 'application/json' in content_type:
            try:
                result = response.json()
                print(f"✅ JSON Response: {json.dumps(result, indent=2)}")
                
                if response.status_code in [200, 201]:
                    print("🎉 SUCCESS: Document created from link!")
                    return True
                else:
                    return False
                    
            except json.JSONDecodeError:
                print(f"📝 Response: {response.text}")
                return response.status_code in [200, 201]
        else:
            print(f"❌ Non-JSON response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False

def main():
    print("🚀 Testing Alternative Onyx Cloud Upload Methods")
    print("📝 Since /onyx-api/ingestion requires session auth, trying file-based approaches")
    print("=" * 80)
    
    # Test file upload
    file_success = test_file_upload_api()
    
    # Test link creation
    link_success = test_link_creation_api()
    
    print("\n" + "=" * 80)
    print("📊 RESULTS:")
    print(f"   📁 File Upload API: {'✅ SUCCESS' if file_success else '❌ FAILED'}")
    print(f"   🔗 Link Creation API: {'✅ SUCCESS' if link_success else '❌ FAILED'}")
    
    if file_success or link_success:
        print("\n🎉 FOUND WORKING ALTERNATIVE!")
        print("💡 Use file upload or link creation instead of direct ingestion")
    else:
        print("\n❌ All methods failed - session authentication required")
        print("📞 Contact Onyx Cloud support for proper API setup")

if __name__ == "__main__":
    main()
