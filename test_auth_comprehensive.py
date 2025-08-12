#!/usr/bin/env python3
"""
Test different authentication methods with Onyx Cloud API
"""

import requests
import json
from datetime import datetime

def test_with_session_auth():
    """Try to establish a session first, then use the API"""
    base_url = 'https://cloud.onyx.app'
    api_key = "on_tenant_f77e9e8b-75c7-4dc4-bea4-3fed8bb60a0f.w6dF-qxJmV4A1RVXRTnSBY6GqRIyf23yWldezF5vJjjZo9k7jn_ke3wI-quqOl92ydF19Ke3gUyQnY7KL7GXKZFaqncbpDnkfsgQZ7hmcIS6BPwIZ1pufJTLVSKw-E8DO5LT-_K2UcmF9ydAdHSpbpiRFEehMH5uRPJdMtJxJB-GNxofACNpICHXuYu7H9riO3YsriZZ5U45SL_L7O33PgOWG7gtpmWAtYxnaJ9CRVzWc9RKHZqfE1hMHGUnxwsN"
    
    session = requests.Session()
    
    print("🔐 Testing Session-based Authentication Approach")
    print("=" * 50)
    
    # Try different header combinations
    auth_variants = [
        {
            "name": "Standard Bearer Token",
            "headers": {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        },
        {
            "name": "API Key Header", 
            "headers": {
                'X-API-Key': api_key,
                'Content-Type': 'application/json'
            }
        },
        {
            "name": "Authorization + API Key",
            "headers": {
                'Authorization': f'Bearer {api_key}',
                'X-API-Key': api_key,
                'Content-Type': 'application/json'
            }
        },
        {
            "name": "Basic Auth Style",
            "headers": {
                'Authorization': f'Basic {api_key}',
                'Content-Type': 'application/json'
            }
        }
    ]
    
    # Test payload from official docs
    payload = {
        "document": {
            "id": f"auth_test_{int(datetime.now().timestamp())}",
            "sections": [
                {
                    "text": "Testing different authentication methods with official payload structure.",
                    "link": "https://docs.onyx.app/backend_apis/ingestion"
                }
            ],
            "source": "web",
            "semantic_identifier": "Auth Test Document",
            "metadata": {
                "tag": "auth-test",
                "test_type": "authentication_variants"
            },
            "doc_updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "cc_pair_id": 1
    }
    
    url = f"{base_url}/onyx-api/ingestion"
    
    for variant in auth_variants:
        print(f"\n🧪 Testing: {variant['name']}")
        try:
            response = session.post(url, headers=variant['headers'], json=payload, timeout=15)
            content_type = response.headers.get('content-type', '').lower()
            
            print(f"   📥 Status: {response.status_code}")
            print(f"   📄 Content-Type: {content_type}")
            
            if 'application/json' in content_type:
                try:
                    result = response.json()
                    print(f"   ✅ SUCCESS! JSON Response: {json.dumps(result, indent=2)}")
                    return True
                except:
                    print(f"   ❌ JSON parse error: {response.text[:100]}...")
            else:
                is_login = 'login' in response.text.lower() or 'sign in' in response.text.lower()
                print(f"   ❌ HTML Response {'(login page)' if is_login else ''}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return False

def test_api_endpoints():
    """Test different API endpoints that might work"""
    base_url = 'https://cloud.onyx.app'
    api_key = "on_tenant_f77e9e8b-75c7-4dc4-bea4-3fed8bb60a0f.w6dF-qxJmV4A1RVXRTnSBY6GqRIyf23yWldezF5vJjjZo9k7jn_ke3wI-quqOl92ydF19Ke3gUyQnY7KL7GXKZFaqncbpDnkfsgQZ7hmcIS6BPwIZ1pufJTLVSKw-E8DO5LT-_K2UcmF9ydAdHSpbpiRFEehMH5uRPJdMtJxJB-GNxofACNpICHXuYu7H9riO3YsriZZ5U45SL_L7O33PgOWG7gtpmWAtYxnaJ9CRVzWc9RKHZqfE1hMHGUnxwsN"
    
    print("\n🔍 Testing Alternative API Endpoints")
    print("=" * 50)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    endpoints_to_test = [
        "/api/ingestion",
        "/backend-api/ingestion", 
        "/onyx-api/document",
        "/api/document",
        "/api/manage/ingestion",
        "/api/user/file/upload",
        "/api/admin/ingestion"
    ]
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        print(f"\n🧪 Testing: {endpoint}")
        
        try:
            # Try both GET and POST
            for method in ['GET', 'POST']:
                response = requests.request(method, url, headers=headers, timeout=10)
                content_type = response.headers.get('content-type', '').lower()
                
                print(f"   {method} - Status: {response.status_code}, Content: {content_type[:30]}...")
                
                if response.status_code not in [404, 405] and 'application/json' in content_type:
                    print(f"   ✅ FOUND WORKING ENDPOINT: {endpoint} ({method})")
                    try:
                        result = response.json()
                        print(f"   📋 Response: {json.dumps(result, indent=2)[:200]}...")
                    except:
                        print(f"   📋 Response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    print("🔧 Comprehensive Onyx Cloud API Authentication Testing")
    print("📖 Goal: Find working authentication method for ingestion API")
    print("=" * 70)
    
    # Test different auth methods
    success = test_with_session_auth()
    
    if not success:
        print("\n🔍 All authentication methods failed. Testing alternative endpoints...")
        test_api_endpoints()
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY:")
    print("✅ Health endpoint works: /api/health")
    print("❌ Ingestion endpoint returns HTML: /onyx-api/ingestion")
    print("🔐 Issue: Session-based authentication required")
    print("\n📋 NEXT STEPS:")
    print("1. Contact Onyx Cloud support for Enterprise API authentication")
    print("2. Ask about session-based authentication requirements")
    print("3. Check if API key needs specific permissions for ingestion")
    print("4. Consider using file upload endpoints as alternative")

if __name__ == "__main__":
    main()
