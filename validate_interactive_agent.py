#!/usr/bin/env python3
"""
Validation script for Interactive Onyx Agent

This script validates the agent setup and tests basic functionality
before starting the interactive session.
"""

import asyncio
import os
import sys
from datetime import datetime

# Local imports
from onyx import OnyxService
from interactive_onyx_agent import OnyxAgentDependencies, ensure_document_set, get_model


async def validate_environment():
    """Validate environment variables and dependencies."""
    print("🔧 ENVIRONMENT VALIDATION")
    print("="*40)
    
    # Check required environment variables
    required_vars = {
        "ONYX_API_KEY": "Onyx Cloud API authentication",
        "GOOGLE_API_KEY": "Google Gemini API (or OpenAI)",
        "OPENAI_API_KEY": "OpenAI GPT-4 API (alternative to Gemini)"
    }
    
    all_good = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            if var == "ONYX_API_KEY":
                print(f"✅ {var}: {'*' * 20}...{value[-4:]}")
            else:
                print(f"✅ {var}: Set ({description})")
        else:
            if var in ["GOOGLE_API_KEY", "OPENAI_API_KEY"]:
                continue  # At least one of these is required
            print(f"❌ {var}: Missing ({description})")
            all_good = False
    
    # Check LLM API keys
    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")):
        print("❌ LLM API: Missing (need either GOOGLE_API_KEY or OPENAI_API_KEY)")
        all_good = False
    else:
        print("✅ LLM API: Available")
    
    return all_good


async def validate_onyx_connection():
    """Validate Onyx Cloud connection and CC-pair 285."""
    print("\n🔗 ONYX CLOUD CONNECTION")
    print("="*40)
    
    try:
        # Initialize Onyx service
        print("🔧 Initializing Onyx service...")
        onyx_service = OnyxService()
        print("✅ Onyx service initialized")
        
        # Check CC-pair 285 status
        print("🔧 Verifying CC-pair 285 status...")
        cc_pair_ready = onyx_service.verify_cc_pair_status(285)
        
        if cc_pair_ready:
            print("✅ CC-pair 285: Ready for search")
        else:
            print("⚠️  CC-pair 285: May not be fully ready, but will proceed")
        
        return True, onyx_service
        
    except Exception as e:
        print(f"❌ Onyx connection failed: {e}")
        return False, None


async def validate_document_set(onyx_service):
    """Validate document set creation/access."""
    print("\n📂 DOCUMENT SET VALIDATION")
    print("="*40)
    
    try:
        # Create dependencies
        deps = OnyxAgentDependencies(onyx_service=onyx_service)
        
        print("🔧 Ensuring document set for CC-pair 285...")
        document_set_id = ensure_document_set(deps)
        
        print(f"✅ Document set ready: ID {document_set_id}")
        
        return True, document_set_id
        
    except Exception as e:
        print(f"❌ Document set validation failed: {e}")
        return False, None


async def validate_llm_model():
    """Validate LLM model initialization."""
    print("\n🤖 LLM MODEL VALIDATION")
    print("="*40)
    
    try:
        print("🔧 Initializing LLM model...")
        model_name = get_model()
        print(f"✅ Model configured: {model_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM model validation failed: {e}")
        return False


async def test_search_functionality(onyx_service, document_set_id):
    """Test basic search functionality."""
    print("\n🔍 SEARCH FUNCTIONALITY TEST")
    print("="*40)
    
    test_query = "Tell me about Aanya Sharma"
    
    try:
        print(f"🔧 Testing search with query: '{test_query}'")
        
        result = onyx_service.search_with_document_set_validated(
            test_query, document_set_id, max_retries=2
        )
        
        if result.get("success"):
            answer = result.get("answer", "")
            source_docs = result.get("source_documents", [])
            
            print("✅ Search successful!")
            print(f"📝 Answer length: {len(answer)} characters")
            print(f"📚 Source documents: {len(source_docs)}")
            
            if source_docs:
                print("📋 Top source:")
                top_doc = source_docs[0]
                doc_name = top_doc.get('semantic_identifier', 'Unknown')
                print(f"   - {doc_name}")
            
            return True
        else:
            print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False


async def main():
    """Run complete validation suite."""
    print("🎯 INTERACTIVE ONYX AGENT VALIDATION")
    print("="*50)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    validation_steps = []
    
    # Step 1: Environment validation
    env_ok = await validate_environment()
    validation_steps.append(("Environment", env_ok))
    
    if not env_ok:
        print("\n❌ Environment validation failed. Please fix the issues above.")
        return 1
    
    # Step 2: Onyx connection validation
    onyx_ok, onyx_service = await validate_onyx_connection()
    validation_steps.append(("Onyx Connection", onyx_ok))
    
    if not onyx_ok:
        print("\n❌ Onyx connection validation failed.")
        return 1
    
    # Step 3: Document set validation
    ds_ok, document_set_id = await validate_document_set(onyx_service)
    validation_steps.append(("Document Set", ds_ok))
    
    if not ds_ok:
        print("\n❌ Document set validation failed.")
        return 1
    
    # Step 4: LLM model validation
    llm_ok = await validate_llm_model()
    validation_steps.append(("LLM Model", llm_ok))
    
    if not llm_ok:
        print("\n❌ LLM model validation failed.")
        return 1
    
    # Step 5: Search functionality test
    search_ok = await test_search_functionality(onyx_service, document_set_id)
    validation_steps.append(("Search Test", search_ok))
    
    # Final summary
    print("\n🎯 VALIDATION SUMMARY")
    print("="*30)
    
    all_passed = True
    for step_name, result in validation_steps:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{step_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*50)
    
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ Ready to start interactive agent")
        print("\n🚀 To start the interactive session, run:")
        print("   python interactive_onyx_agent.py")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("🔧 Please fix the issues above before starting the agent")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
