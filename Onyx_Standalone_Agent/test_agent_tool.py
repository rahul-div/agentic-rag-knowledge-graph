#!/usr/bin/env python3
"""
Quick test script to verify the search tool is working properly
"""

import asyncio
from interactive_onyx_agent import agent, OnyxAgentDependencies, ensure_document_set
from onyx import OnyxService

async def test_agent():
    """Test the agent with a simple query."""
    
    print("🧪 Testing Onyx Agent Tool Integration")
    print("="*50)
    
    # Initialize dependencies
    onyx_service = OnyxService()
    deps = OnyxAgentDependencies(onyx_service=onyx_service)
    deps.document_set_id = ensure_document_set(deps)
    
    print(f"✅ Using document set: {deps.document_set_id}")
    
    # Test query
    test_query = "Which cafe did Aanya Sharma prefer?"
    print(f"🔍 Testing query: '{test_query}'")
    
    try:
        result = await agent.run(test_query, deps=deps)
        print("\n🎯 RESULT:")
        print("="*40)
        print(result.output)
        print("="*40)
        
        # Check if search tool was called
        if "search_documents" in str(result):
            print("✅ Search tool was likely called")
        else:
            print("❌ Search tool may not have been called")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())
