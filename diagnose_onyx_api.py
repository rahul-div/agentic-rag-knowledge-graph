#!/usr/bin/env python3
"""
Onyx Cloud API Diagnostic Tool

This tool helps diagnose connectivity and authentication issues with Onyx Cloud API.
It performs a series of tests to identify the root cause of API problems.

Usage:
    python diagnose_onyx_api.py
"""

import os
import requests
import json
import logging
from datetime import datetime
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add the project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from onyx.config import get_onyx_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_environment_config():
    """Test if environment variables are properly configured."""
    logger.info("=" * 60)
    logger.info("🔧 TESTING ENVIRONMENT CONFIGURATION")
    logger.info("=" * 60)
    
    try:
        config = get_onyx_config()
        
        logger.info("✅ Environment configuration loaded successfully")
        logger.info(f"   🌐 Base URL: {config['base_url']}")
        logger.info(f"   🔑 API Key: {'*' * (len(config['api_key']) - 8) + config['api_key'][-8:] if len(config['api_key']) > 8 else '*****'}")
        logger.info(f"   ⏱️  Timeout: {config['timeout']} seconds")
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Failed to load environment configuration: {e}")
        logger.error("💡 Make sure your .env file contains:")
        logger.error("   ONYX_API_KEY=your_api_key_here")
        logger.error("   ONYX_BASE_URL=your_onyx_url_here")
        return None


def test_basic_connectivity(base_url):
    """Test basic connectivity to the Onyx server."""
    logger.info("=" * 60)
    logger.info("🌐 TESTING BASIC CONNECTIVITY")
    logger.info("=" * 60)
    
    try:
        # Test basic HTTP connectivity (without authentication)
        test_url = base_url.rstrip('/')
        logger.info(f"Testing connectivity to: {test_url}")
        
        response = requests.get(test_url, timeout=10)
        logger.info(f"✅ Server responded with status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Basic connectivity successful")
        elif response.status_code in [401, 403]:
            logger.info("✅ Server reachable (authentication required)")
        else:
            logger.warning(f"⚠️  Unexpected status code: {response.status_code}")
        
        # Check response headers
        logger.info("📋 Response headers:")
        for header, value in response.headers.items():
            if header.lower() in ['server', 'content-type', 'x-powered-by']:
                logger.info(f"   {header}: {value}")
        
        return True
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("💡 Check if the base URL is correct and the server is running")
        return False
    except requests.exceptions.Timeout as e:
        logger.error(f"❌ Connection timed out: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def test_api_endpoints(base_url, api_key):
    """Test specific API endpoints."""
    logger.info("=" * 60)
    logger.info("🔌 TESTING API ENDPOINTS")
    logger.info("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test endpoints based on the official Onyx GitHub repository structure
    test_endpoints = [
        # Basic endpoints
        ('/api/health', 'GET', None),
        ('/api/me', 'GET', None),
        
        # Document ingestion (the main endpoint we care about)
        ('/onyx-api/ingestion', 'GET', None),  # GET to check if endpoint exists
        
        # Test POST with proper payload structure from the repo
        ('/onyx-api/ingestion', 'POST', {
            "document": {
                "id": f"test_doc_{int(datetime.now().timestamp())}",
                "sections": [
                    {
                        "text": "Test document content for API endpoint verification",
                        "link": None
                    }
                ],
                "source": "FILE",
                "semantic_identifier": "test_api_endpoint.txt",
                "title": "API Endpoint Test Document",
                "doc_updated_at": datetime.now().isoformat() + "Z"
            },
            "cc_pair_id": None  # Uses default connector-credential pair
        })
    ]
    
    logger.info("🔍 Testing endpoints based on Onyx GitHub repository structure:")
    
    for endpoint, method, payload in test_endpoints:
        url = base_url.rstrip('/') + endpoint
        logger.info(f"🎯 Testing {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=payload, timeout=10)
            else:
                logger.warning(f"⚠️  Unsupported method: {method}")
                continue
            
            logger.info(f"   📊 Status: {response.status_code}")
            logger.info(f"   📋 Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            # Try to parse response
            try:
                if response.text:
                    if 'application/json' in response.headers.get('content-type', ''):
                        response_data = response.json()
                        logger.info(f"   📄 Response: {json.dumps(response_data, indent=2)[:200]}...")
                    else:
                        logger.warning(f"   📄 Non-JSON Response: {response.text[:100]}...")
                else:
                    logger.warning("   📄 Response: Empty body")
            except json.JSONDecodeError:
                logger.warning(f"   📄 Invalid JSON Response: {response.text[:100]}...")
                if 'html' in response.text.lower():
                    logger.warning("   🌐 Response appears to be HTML (webpage instead of API)")
            
            if response.status_code < 400:
                logger.info("   ✅ Success")
            elif response.status_code == 401:
                logger.error("   ❌ Authentication failed - check your API key")
            elif response.status_code == 403:
                logger.error("   ❌ Access forbidden - check permissions")
            elif response.status_code == 404:
                logger.error("   ❌ Endpoint not found - check your base URL or API version")
            else:
                logger.error(f"   ❌ API error: {response.status_code}")
            
        except Exception as e:
            logger.error(f"   ❌ Request failed: {e}")
        
        logger.info("")


def test_ingestion_api_specifically(base_url, api_key):
    """Test the ingestion API specifically with detailed debugging."""
    logger.info("=" * 60)
    logger.info("📤 TESTING INGESTION API SPECIFICALLY")
    logger.info("=" * 60)
    
    # Based on official Onyx GitHub repo: backend/onyx/server/onyx_api/ingestion.py
    # The correct endpoint is POST /onyx-api/ingestion with Bearer token
    url = base_url.rstrip('/') + '/onyx-api/ingestion'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    logger.info("🔍 API endpoint confirmed from Onyx GitHub repository:")
    logger.info("   📂 File: backend/onyx/server/onyx_api/ingestion.py")
    logger.info("   🎯 Endpoint: POST /onyx-api/ingestion")
    logger.info("   🔐 Auth: Bearer token in Authorization header")
    
    # Create payload following the exact IngestionDocument model from the repo
    payload = {
        "document": {
            "id": f"diagnostic_test_{int(datetime.now().timestamp())}",
            "sections": [
                {
                    "text": "This is a diagnostic test document for Onyx Cloud API connectivity. Safe to delete.",
                    "link": None
                }
            ],
            "source": "FILE",  # Changed from "api" to "FILE" as per the repo code
            "semantic_identifier": "onyx_diagnostic_test.txt",
            "title": "Onyx API Diagnostic Test Document",
            "metadata": {
                "test": "diagnostic",
                "created_by": "onyx_diagnostic_tool",
                "timestamp": datetime.now().isoformat()
            },
            "doc_updated_at": datetime.now().isoformat() + "Z"  # Added Z for UTC
        },
        "cc_pair_id": None  # Uses DEFAULT_CC_PAIR_ID as per the repo code
    }
    
    logger.info(f"🌐 Testing URL: {url}")
    logger.info(f"🔑 Headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}, indent=2)}")
    logger.info(f"📄 Payload structure follows IngestionDocument model from Onyx repo")
    
    try:
        logger.info("📤 Sending POST request to Onyx Cloud...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        logger.info(f"✅ Request completed successfully")
        logger.info(f"📊 Status Code: {response.status_code}")
        logger.info(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            logger.info("🎉 SUCCESS! Ingestion API is working correctly")
            try:
                response_json = response.json()
                logger.info(f"📄 Response: {json.dumps(response_json, indent=2)}")
                logger.info(f"📄 Document ID: {response_json.get('document_id', 'N/A')}")
                logger.info("✅ Document successfully ingested into Onyx Cloud")
            except json.JSONDecodeError:
                logger.warning("⚠️  Response body is not JSON, but status is 200")
                logger.info(f"📄 Raw response: '{response.text}'")
        elif response.status_code == 401:
            logger.error("❌ AUTHENTICATION FAILED (401)")
            logger.error("🔐 Your API key is invalid or expired")
            logger.error("💡 Check your ONYX_API_KEY in the .env file")
        elif response.status_code == 403:
            logger.error("❌ AUTHORIZATION FAILED (403)")
            logger.error("🚫 Your API key doesn't have ingestion permissions")
            logger.error("💡 Contact your Onyx administrator for proper permissions")
        elif response.status_code == 404:
            logger.error("❌ ENDPOINT NOT FOUND (404)")
            logger.error("🌐 The ingestion endpoint doesn't exist at this URL")
            logger.error("💡 Check your ONYX_BASE_URL - should be: https://cloud.onyx.app")
        else:
            logger.error(f"❌ API ERROR ({response.status_code})")
            
        logger.info(f"📄 Raw Response Body: '{response.text}'")
        
        if response.text:
            try:
                response_json = response.json()
                logger.info(f"📄 Parsed JSON Response: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse JSON response: {e}")
                logger.error("⚠️  This indicates the API returned non-JSON content")
                if 'html' in response.text.lower():
                    logger.error("🌐 Response appears to be HTML - likely hitting a web page instead of API")
                    logger.error("💡 Check if your ONYX_BASE_URL is correct for the API endpoint")
        else:
            logger.error("❌ Empty response body received")
        
    except requests.exceptions.ConnectTimeout:
        logger.error("❌ CONNECTION TIMEOUT - API server not responding")
        logger.error("💡 Check if the base URL is correct and server is online")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ CONNECTION ERROR: {e}")
        logger.error("💡 Check network connectivity and base URL")
    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")


def main():
    """Main diagnostic function."""
    logger.info("🔍 ONYX CLOUD API DIAGNOSTIC TOOL")
    logger.info(f"⏰ Started at: {datetime.now().isoformat()}")
    
    # Test 1: Environment configuration
    config = test_environment_config()
    if not config:
        return
    
    # Test 2: Basic connectivity
    if not test_basic_connectivity(config['base_url']):
        return
    
    # Test 3: API endpoints
    test_api_endpoints(config['base_url'], config['api_key'])
    
    # Test 4: Specific ingestion API test
    test_ingestion_api_specifically(config['base_url'], config['api_key'])
    
    logger.info("=" * 60)
    logger.info("🏁 DIAGNOSTIC COMPLETE")
    logger.info("=" * 60)
    logger.info("💡 If you see authentication errors, check your API key")
    logger.info("💡 If you see 404 errors, check your base URL")
    logger.info("💡 If you see empty responses, contact Onyx support")


if __name__ == "__main__":
    main()
