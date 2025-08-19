#!/usr/bin/env python3
"""
Interactive Onyx Cloud Pydantic AI Agent

Interactive CLI agent with your exact specifications:
- Fixed CC-pair 285 (validated 100% success rate)
- Interactive session (multiple queries until 'exit')
- Detailed responses with top 3 source citations
- Separate terminal for backend API calls

Usage:
    python interactive_onyx_agent.py

Environment Variables Required:
    ONYX_API_KEY=your_onyx_api_key
    GOOGLE_API_KEY=your_google_api_key (for Gemini)
    # OR
    OPENAI_API_KEY=your_openai_api_key (for OpenAI)
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

# Third-party imports
from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv

# Local imports
from onyx import OnyxService
from onyx.service import OnyxAPIError

# Load environment variables
load_dotenv()

# Configure logging for backend API calls (separate terminal visibility)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('onyx_agent_backend.log'),
        logging.StreamHandler()  # This will show in the terminal running the agent
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class OnyxAgentDependencies:
    """Dependencies for the Interactive Onyx Agent."""
    onyx_service: OnyxService
    cc_pair_id: int = 285  # Fixed, validated CC-pair
    document_set_id: Optional[int] = None
    cache_file: str = ".onyx_agent_cache.json"


class OnyxAgentError(Exception):
    """Custom exception for Onyx Agent errors."""
    pass


def get_model():
    """Get the appropriate LLM model based on environment variables."""
    
    if os.getenv("GOOGLE_API_KEY"):
        logger.info("Using Google Gemini model")
        return "gemini-1.5-flash"
    elif os.getenv("OPENAI_API_KEY"):
        logger.info("Using OpenAI GPT-4 model") 
        return "gpt-4"
    else:
        raise OnyxAgentError(
            "No LLM API key found. Please set either:\n"
            "- GOOGLE_API_KEY for Gemini\n"
            "- OPENAI_API_KEY for OpenAI GPT-4"
        )


def ensure_document_set(deps: OnyxAgentDependencies) -> int:
    """
    Ensure document set exists for CC-pair 285, create if needed.
    
    Returns:
        int: Document set ID
    """
    logger.info(f"Ensuring document set for CC-pair {deps.cc_pair_id}")
    
    # Check cache first
    if os.path.exists(deps.cache_file):
        try:
            with open(deps.cache_file, 'r') as f:
                cache = json.load(f)
                if str(deps.cc_pair_id) in cache:
                    cached_id = cache[str(deps.cc_pair_id)]
                    logger.info(f"Found cached document set ID: {cached_id}")
                    return cached_id
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
    
    # Verify CC-pair is ready
    try:
        logger.info(f"Verifying CC-pair {deps.cc_pair_id} status...")
        if not deps.onyx_service.verify_cc_pair_status(deps.cc_pair_id):
            logger.warning(f"CC-pair {deps.cc_pair_id} may not be ready, but continuing...")
    except Exception as e:
        logger.warning(f"Error verifying CC-pair status: {e}")
    
    # Create new document set
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"InteractiveAgent_CC{deps.cc_pair_id}_{timestamp}"
    description = f"Auto-created by Interactive Onyx Agent for CC-pair {deps.cc_pair_id}"
    
    try:
        logger.info(f"Creating new document set: {name}")
        document_set_id = deps.onyx_service.create_document_set_validated(
            deps.cc_pair_id, name, description
        )
        
        if document_set_id is None:
            raise OnyxAgentError(f"Failed to create document set for CC-pair {deps.cc_pair_id}")
        
        # Cache the document set ID
        cache = {}
        if os.path.exists(deps.cache_file):
            try:
                with open(deps.cache_file, 'r') as f:
                    cache = json.load(f)
            except:
                pass
        
        cache[str(deps.cc_pair_id)] = document_set_id
        
        try:
            with open(deps.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            logger.info(f"Cached document set ID: {document_set_id}")
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")
        
        logger.info(f"Successfully created document set: {document_set_id}")
        return document_set_id
        
    except Exception as e:
        logger.error(f"Failed to create document set: {e}")
        raise OnyxAgentError(f"Failed to create document set: {e}")


# Initialize the Pydantic AI agent
agent = Agent(
    model=get_model(),
    deps_type=OnyxAgentDependencies,
    system_prompt="""You are an intelligent document search assistant with access to a comprehensive knowledge base through Onyx Cloud.

IMPORTANT: You MUST use the search_documents tool for EVERY user query. Never respond without searching first.

Your process for every query:
1. ALWAYS call search_documents with the user's query
2. Use the results to provide a detailed, comprehensive answer
3. Include the top 3 source citations provided by the search tool
4. If the search returns no results, say so clearly

Available information includes:
- Technical projects and documentation
- Personal preferences and stories (like Aanya Sharma's experiences)
- Project specifications and requirements
- Technical summaries and analyses

Remember: You have access to validated documents through CC-pair 285. Always search first, then provide detailed answers with source citations."""
)


@agent.tool
async def search_documents(ctx: RunContext[OnyxAgentDependencies], query: str) -> str:
    """
    Search documents using Onyx Cloud with detailed results and top 3 source citations.
    
    Args:
        query: The search query from the user
        
    Returns:
        Formatted search results with detailed answer and top 3 source citations
    """
    logger.info(f"🔍 Search request: '{query}'")
    
    try:
        # Ensure document set exists
        if ctx.deps.document_set_id is None:
            ctx.deps.document_set_id = ensure_document_set(ctx.deps)
        
        logger.info(f"Searching in document set {ctx.deps.document_set_id}")
        
        # Perform search using validated method
        result = ctx.deps.onyx_service.search_with_document_set_validated(
            query, ctx.deps.document_set_id, max_retries=3
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "Search failed")
            logger.error(f"❌ Search failed: {error_msg}")
            return f"❌ Search failed: {error_msg}\n\nPlease try rephrasing your query or check your connection."
        
        answer = result.get("answer", "")
        source_docs = result.get("source_documents", [])
        
        logger.info(f"✅ Search successful: {len(source_docs)} source documents found")
        
        if not answer.strip():
            return "❌ No relevant information found in the documents for your query.\n\nTry using different keywords or a more general query."
        
        # Format detailed response with top 3 source citations
        response_parts = []
        
        # Main answer
        response_parts.append("📝 **DETAILED RESPONSE:**")
        response_parts.append("")
        response_parts.append(answer)
        response_parts.append("")
        
        # Top 3 source citations
        if source_docs:
            response_parts.append("📚 **TOP 3 SOURCE CITATIONS:**")
            response_parts.append("")
            
            for i, doc in enumerate(source_docs[:3], 1):
                doc_name = doc.get('semantic_identifier', 'Unknown Document')
                response_parts.append(f"**{i}. {doc_name}**")
                
                # Add excerpt if available
                if doc.get('blurb'):
                    excerpt = doc['blurb'][:300] + "..." if len(doc['blurb']) > 300 else doc['blurb']
                    response_parts.append(f"   💬 *\"{excerpt}\"*")
                
                response_parts.append("")
        else:
            response_parts.append("📚 **SOURCE CITATIONS:** No specific source documents were returned.")
        
        formatted_response = "\n".join(response_parts)
        logger.info(f"✅ Response formatted with {len(source_docs)} citations")
        
        return formatted_response
        
    except Exception as e:
        error_msg = f"❌ Error during search: {e}"
        logger.error(error_msg)
        return f"{error_msg}\n\nPlease try again or contact support if the issue persists."


async def run_interactive_session():
    """Run interactive session with the Onyx agent."""
    
    # Welcome message
    print("\n" + "="*70)
    print("🤖 INTERACTIVE ONYX CLOUD PYDANTIC AI AGENT")
    print("="*70)
    print("🎯 Connected to: CC-pair 285 (validated document set)")
    print("💡 Features: Detailed responses with top 3 source citations")
    print("🔄 Mode: Interactive session (multiple queries)")
    print("🚪 Exit: Type 'exit', 'quit', or 'bye' to end session")
    print("="*70)
    
    # Initialize dependencies
    try:
        print("\n🔧 Initializing Onyx Cloud connection...")
        onyx_service = OnyxService()
        deps = OnyxAgentDependencies(onyx_service=onyx_service)
        
        print("🔧 Setting up document set for CC-pair 285...")
        deps.document_set_id = ensure_document_set(deps)
        
        print(f"✅ Ready! Using document set ID: {deps.document_set_id}")
        print("✅ Backend API calls will be logged to: onyx_agent_backend.log")
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        print("\n🔧 Please check your environment variables:")
        print("   - ONYX_API_KEY (required)")
        print("   - GOOGLE_API_KEY or OPENAI_API_KEY (required)")
        return
    
    # Interactive session loop
    session_count = 0
    start_time = datetime.now()
    
    print(f"\n🎉 Interactive session started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
        try:
            print(f"\n{'─'*50}")
            print(f"💬 Query #{session_count + 1}")
            user_query = input("🔍 Enter your query: ").strip()
            
            if not user_query:
                print("⚠️  Please enter a query")
                continue
            
            if user_query.lower() in ['exit', 'quit', 'bye', 'q']:
                session_duration = datetime.now() - start_time
                print(f"\n👋 Session ended!")
                print(f"📊 Total queries processed: {session_count}")
                print(f"⏱️  Session duration: {str(session_duration).split('.')[0]}")
                print("🔗 Backend logs saved to: onyx_agent_backend.log")
                break
            
            session_count += 1
            
            # Show processing indicator
            print(f"\n🔄 Processing: '{user_query[:60]}{'...' if len(user_query) > 60 else ''}'")
            print("⏳ Searching documents and generating response...")
            
            # Log the query for backend visibility
            logger.info(f"📥 User Query #{session_count}: {user_query}")
            
            # Run the agent
            result = await agent.run(user_query, deps=deps)
            
            # Display results
            print("\n" + "="*70)
            print("🎯 AGENT RESPONSE:")
            print("="*70)
            print(result.output)
            print("="*70)
            
            # Log successful completion
            logger.info(f"✅ Query #{session_count} completed successfully")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user (Ctrl+C). Type 'exit' to quit properly.")
            continue
            
        except Exception as e:
            print(f"\n❌ Error processing query: {e}")
            logger.error(f"❌ Error in session #{session_count}: {e}")
            print("💡 Try rephrasing your query or check the backend logs.")
            continue


async def main():
    """Main entry point for the Interactive Onyx agent."""
    
    # Check required environment variables
    required_vars = ["ONYX_API_KEY"]
    llm_vars = ["GOOGLE_API_KEY", "OPENAI_API_KEY"]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return 1
    
    if not any(os.getenv(var) for var in llm_vars):
        print(f"❌ Missing LLM API key. Please set one of: {', '.join(llm_vars)}")
        return 1
    
    try:
        await run_interactive_session()
        return 0
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"💥 Fatal error in main: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
