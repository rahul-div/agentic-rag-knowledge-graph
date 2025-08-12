#!/usr/bin/env python3
"""
Test Onyx Cloud API with Official Payload Structure
Based on: https://docs.onyx.app/backend_apis/ingestion
"""

import requests
import json
import sys
from datetime import datetime

def get_api_key():
    """Get API key from environment or prompt"""
    import os
    api_key = os.getenv('ONYX_API_KEY')
    if not api_key:
        print("🔑 ONYX_API_KEY not found in environment.")
        api_key = input("Please enter your Onyx Cloud API key: ").strip()
    return api_key

def test_official_onyx_payload():
    """Test with the exact payload structure from official documentation"""
    
    # Configuration
    base_url = 'https://cloud.onyx.app'
    api_key = get_api_key()
    
    if not api_key:
        print("❌ ERROR: No API key provided")
        return False
    
    print(f"🔗 Testing Onyx Cloud at: {base_url}")
    print(f"🔑 Using API Key: {api_key[:10]}...")
    
    # Official payload structure from docs.onyx.app/backend_apis/ingestion
    url = f"{base_url.rstrip('/')}/onyx-api/ingestion"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'OnyxCloudTest/1.0'
    }
    
    # Use the EXACT payload from official documentation
    payload = {
        "document": {
            "id": f"official_test_{int(datetime.now().timestamp())}",
            "sections": [
                {
                    "text": "This is a test document using the official Onyx API payload structure from docs.onyx.app/backend_apis/ingestion. This document tests programmatic ingestion capabilities.",
                    "link": "https://docs.onyx.app/backend_apis/ingestion"
                },
                {
                    "text": "This is a second section to test multi-section document ingestion as documented in the official API documentation.",
                    "link": "https://docs.onyx.app/introduction"
                }
            ],
            "source": "web",  # Using 'web' as shown in official docs
            "semantic_identifier": "Official Onyx API Test Document",
            "metadata": {
                "tag": "test",
                "topics": ["onyx", "api", "official-payload"],
                "test_type": "official_documentation_structure",
                "created_at": datetime.now().isoformat()
            },
            "doc_updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "cc_pair_id": 1  # Using 1 as shown in official docs
    }
    
    print(f"\n📤 Sending POST request to: {url}")
    print(f"🔍 Payload structure follows official docs exactly")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        print(f"📄 Content Type: {content_type}")
        
        if 'application/json' in content_type:
            try:
                result = response.json()
                print(f"✅ JSON Response: {json.dumps(result, indent=2)}")
                
                if response.status_code == 200:
                    print("🎉 SUCCESS: Document ingested successfully!")
                    return True
                else:
                    print(f"⚠️  Non-200 status but valid JSON response")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"📝 Raw response: {response.text[:500]}...")
                return False
        else:
            # HTML response - likely authentication issue
            print(f"❌ Received HTML response instead of JSON")
            print(f"📝 Response preview: {response.text[:200]}...")
            
            # Check if it's a login page
            if 'login' in response.text.lower() or 'sign in' in response.text.lower():
                print("🔐 ISSUE: Response appears to be a login page")
                print("💡 This suggests session-based authentication is required")
                print("🔧 SOLUTION: Contact Onyx Cloud support for proper API key configuration")
            
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint to verify connectivity"""
    base_url = 'https://cloud.onyx.app'
    url = f"{base_url.rstrip('/')}/api/health"
    
    print(f"🏥 Testing health endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"📥 Health Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Health Response: {json.dumps(result, indent=2)}")
                return True
            except:
                print(f"✅ Health Response: {response.text}")
                return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_alternative_endpoints():
    """Test the GET endpoint to list ingested documents"""
    base_url = 'https://cloud.onyx.app'
    api_key = get_api_key()
    
    url = f"{base_url.rstrip('/')}/onyx-api/ingestion"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n📋 Testing GET endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📥 GET Response Status: {response.status_code}")
        
        content_type = response.headers.get('content-type', '').lower()
        print(f"📄 Content Type: {content_type}")
        
        if 'application/json' in content_type:
            try:
                result = response.json()
                print(f"✅ Documents list: {json.dumps(result, indent=2)}")
                return True
            except:
                print(f"✅ Response: {response.text}")
                return True
        else:
            print(f"❌ HTML response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ GET request error: {e}")
        return False

def main():
    print("🚀 Starting Onyx Cloud API Test with Official Payload Structure")
    print("📖 Based on: https://docs.onyx.app/backend_apis/ingestion")
    print("=" * 70)
    
    # Test basic connectivity first
    print("\n1️⃣ Testing basic connectivity...")
    health_ok = test_health_endpoint()
    
    if not health_ok:
        print("❌ Health check failed - but continuing with ingestion test")
    
    print("\n2️⃣ Testing GET endpoint for existing documents...")
    test_alternative_endpoints()
    
    print("\n3️⃣ Testing ingestion API with official payload...")
    success = test_official_onyx_payload()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 RESULT: Ingestion API test SUCCESSFUL!")
        print("✅ Official payload structure works correctly")
    else:
        print("❌ RESULT: Ingestion API test FAILED")
        print("🔧 Next steps:")
        print("   1. Verify API key has ingestion permissions")
        print("   2. Contact Onyx Cloud support for authentication guidance") 
        print("   3. Check if Enterprise features require different auth")
        print("   4. Try authenticating via web UI first to establish session")

if __name__ == "__main__":
    main()
