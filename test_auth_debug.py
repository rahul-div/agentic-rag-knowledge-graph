#!/usr/bin/env python3
"""
Onyx Cloud Authentication Debug Test

This script specifically tests the Bearer token authentication mechanism
to understand why API requests are being redirected to the login page.
"""

import os
import requests
import json
from datetime import datetime
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_bearer_auth_debug():
    """Debug Bearer token authentication issues."""
    
    base_url = os.getenv('ONYX_BASE_URL', 'https://cloud.onyx.app')
    api_key = os.getenv('ONYX_API_KEY')
    
    if not api_key:
        print("❌ ONYX_API_KEY not found in environment")
        return
    
    print("🔍 ONYX CLOUD AUTHENTICATION DEBUG")
    print("=" * 60)
    print(f"🌐 Base URL: {base_url}")
    print(f"🔑 API Key (last 8 chars): ...{api_key[-8:]}")
    print()
    
    # Test different authentication approaches
    auth_tests = [
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
            "name": "Authorization Header (no Bearer)",
            "headers": {
                'Authorization': api_key,
                'Content-Type': 'application/json'
            }
        }
    ]
    
    test_endpoints = [
        '/api/health',
        '/api/me', 
        '/onyx-api/ingestion'
    ]
    
    for endpoint in test_endpoints:
        print(f"🎯 Testing endpoint: {endpoint}")
        print("-" * 40)
        
        for auth_test in auth_tests:
            print(f"  🔐 Auth Method: {auth_test['name']}")
            
            try:
                url = f"{base_url.rstrip('/')}{endpoint}"
                response = requests.get(url, headers=auth_test['headers'], timeout=10)
                
                print(f"    📊 Status: {response.status_code}")
                print(f"    📋 Content-Type: {response.headers.get('content-type', 'unknown')}")
                
                # Check if response is HTML (login redirect)
                if 'text/html' in response.headers.get('content-type', ''):
                    print("    🌐 Response: HTML (likely login page redirect)")
                    if 'Log In to' in response.text:
                        print("    ❌ Authentication failed - redirected to login")
                    else:
                        print(f"    📄 HTML snippet: {response.text[:100]}...")
                elif response.headers.get('content-type', '').startswith('application/json'):
                    try:
                        json_data = response.json()
                        print(f"    ✅ JSON Response: {json.dumps(json_data, indent=2)[:150]}...")
                    except json.JSONDecodeError:
                        print(f"    ❌ Invalid JSON: {response.text[:100]}...")
                else:
                    print(f"    📄 Other response: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
            
            print()
        
        print()

def test_api_key_validation():
    """Test if the API key format is valid."""
    print("🔑 API KEY VALIDATION")
    print("=" * 60)
    
    api_key = os.getenv('ONYX_API_KEY', '')
    
    if not api_key:
        print("❌ No API key found")
        return
    
    print(f"📏 API Key Length: {len(api_key)} characters")
    print(f"🎯 First 10 chars: {api_key[:10]}...")
    print(f"🎯 Last 10 chars: ...{api_key[-10:]}")
    
    # Check for common API key patterns
    if api_key.startswith('sk-'):
        print("✅ Starts with 'sk-' (OpenAI-style)")
    elif api_key.startswith('onyx_'):
        print("✅ Starts with 'onyx_' (Onyx-specific)")
    elif len(api_key) > 50:
        print("✅ Long format key (likely valid)")
    else:
        print("⚠️  Unusual API key format")
    
    # Check for whitespace or special chars
    if api_key.strip() != api_key:
        print("❌ API key has leading/trailing whitespace")
    if '\n' in api_key or '\r' in api_key:
        print("❌ API key contains newline characters")
    if ' ' in api_key:
        print("❌ API key contains spaces")
        
    print()

def test_direct_api_endpoint():
    """Test the API endpoint with detailed request/response logging."""
    print("🚀 DIRECT API ENDPOINT TEST")
    print("=" * 60)
    
    base_url = os.getenv('ONYX_BASE_URL', 'https://cloud.onyx.app')
    api_key = os.getenv('ONYX_API_KEY')
    
    # Test with a minimal GET request first
    url = f"{base_url.rstrip('/')}/onyx-api/ingestion"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'Onyx-Python-Client/1.0'
    }
    
    print(f"📤 GET Request to: {url}")
    print(f"📋 Headers:")
    for key, value in headers.items():
        if key == 'Authorization':
            print(f"  {key}: Bearer ***{value.split(' ')[1][-8:] if len(value.split(' ')) > 1 else '***'}")
        else:
            print(f"  {key}: {value}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"\n📥 Response:")
        print(f"  📊 Status Code: {response.status_code}")
        print(f"  📋 Headers:")
        for key, value in response.headers.items():
            print(f"    {key}: {value}")
        
        print(f"\n📄 Response Body (first 500 chars):")
        print(response.text[:500])
        
        if response.status_code == 200 and 'application/json' in response.headers.get('content-type', ''):
            print("\n✅ Successful API response!")
            try:
                data = response.json()
                print(f"📄 JSON Data: {json.dumps(data, indent=2)}")
            except:
                print("❌ Failed to parse JSON response")
        elif 'text/html' in response.headers.get('content-type', ''):
            print("\n❌ Got HTML instead of JSON - authentication issue!")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print()

if __name__ == "__main__":
    test_api_key_validation()
    test_bearer_auth_debug() 
    test_direct_api_endpoint()
    
    print("🏁 AUTHENTICATION DEBUG COMPLETE")
    print("=" * 60)
    print("💡 If all endpoints return HTML login pages:")
    print("   - Your API key may be invalid or expired")
    print("   - The API endpoint may require different authentication")
    print("   - Contact Onyx Cloud support for API access verification")
