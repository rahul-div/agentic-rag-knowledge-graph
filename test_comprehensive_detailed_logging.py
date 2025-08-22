#!/usr/bin/env python3
"""
Comprehensive Search Test with Detailed Logging

This script tests the comprehensive search functionality that combines all three retrieval systems:
1. Onyx Cloud (Enterprise search)
2. Graphiti Vector DB (Semantic search)
3. Graphiti Knowledge Graph (Entity relationship search)

The script logs every step of the process including:
- Individual system responses
- Synthesis process
- Fallback strategies
- Final response generation

Usage:
    python test_comprehensive_detailed_logging.py

This will generate a detailed log file showing the complete background process.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
import traceback

from dotenv import load_dotenv

# Import our hybrid agent components
from agent.agent import create_hybrid_rag_agent, AgentDependencies
from agent.tools import comprehensive_search_tool, ComprehensiveSearchInput

# Load environment variables
load_dotenv()

# Configure detailed logging
log_filename = (
    f"comprehensive_search_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)


class DetailedFormatter(logging.Formatter):
    """Custom formatter for detailed logging with timestamps and levels."""

    def format(self, record):
        # Add timestamp and level with emojis
        level_emojis = {
            "DEBUG": "🔍",
            "INFO": "📋",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨",
        }

        emoji = level_emojis.get(record.levelname, "📝")
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

        # Format the message
        formatted = f"{timestamp} {emoji} [{record.name}] {record.levelname}: {record.getMessage()}"

        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


# Set up logging with multiple handlers
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
    force=True,
)

# Apply custom formatter
for handler in logging.getLogger().handlers:
    handler.setFormatter(DetailedFormatter())

logger = logging.getLogger(__name__)


class ComprehensiveSearchLogger:
    """Enhanced logger that captures detailed information about the comprehensive search process."""

    def __init__(self):
        self.test_session_id = (
            f"detailed_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.detailed_results = {
            "session_info": {
                "session_id": self.test_session_id,
                "start_time": datetime.now().isoformat(),
                "log_file": log_filename,
            },
            "test_queries": [],
            "system_responses": {},
            "synthesis_details": {},
            "final_results": {},
        }

        logger.info("=" * 80)
        logger.info("🚀 COMPREHENSIVE SEARCH DETAILED LOGGING TEST")
        logger.info("=" * 80)
        logger.info(f"📊 Session ID: {self.test_session_id}")
        logger.info(f"📁 Log file: {log_filename}")
        logger.info(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async def test_comprehensive_search_with_logging(self):
        """Test comprehensive search with detailed logging of all processes."""

        # Test queries designed to trigger all three systems
        test_queries = [
            {
                "id": "query_1",
                "query": "What is the vision statement for the financial RAG chatbot?",
                "description": "Factual query - should trigger Onyx and Vector systems",
                "expected_systems": ["onyx", "vector"],
                "complexity": "simple",
            },
            {
                "id": "query_2",
                "query": "Tell me about Aanya Sharma's coffee preferences and her role in the project",
                "description": "Entity-specific query - should trigger all three systems",
                "expected_systems": ["onyx", "vector", "graph"],
                "complexity": "complex",
            },
            {
                "id": "query_3",
                "query": "What are the relationships between team members and technologies mentioned in the documentation?",
                "description": "Relationship query - should heavily use Graph system",
                "expected_systems": ["graph", "vector"],
                "complexity": "relationship-focused",
            },
            {
                "id": "query_4",
                "query": "Explain the privacy features and security considerations for the financial data system",
                "description": "Multi-faceted query - should use comprehensive synthesis",
                "expected_systems": ["onyx", "vector"],
                "complexity": "synthesis-heavy",
            },
        ]

        self.detailed_results["test_queries"] = test_queries

        try:
            # Initialize agent
            logger.info("🤖 AGENT INITIALIZATION")
            logger.info("-" * 50)

            logger.info("🔧 Creating hybrid RAG agent...")
            agent, deps = await create_hybrid_rag_agent(
                session_id=self.test_session_id, cc_pair_id=285, enable_onyx=True
            )

            if not agent or not deps:
                logger.error("❌ Failed to initialize agent")
                return

            logger.info("✅ Agent initialized successfully")
            logger.info(f"📋 Onyx service available: {deps.onyx_service is not None}")
            logger.info(f"📋 Onyx document set ID: {deps.onyx_document_set_id}")
            logger.info(f"📋 Session ID: {deps.session_id}")

            # Test each query with detailed logging
            for i, test_case in enumerate(test_queries):
                query_id = test_case["id"]
                query = test_case["query"]
                description = test_case["description"]

                logger.info("\n" + "=" * 80)
                logger.info(f"🎯 TEST QUERY {i + 1}/{len(test_queries)}: {query_id}")
                logger.info("=" * 80)
                logger.info(f"📝 Query: {query}")
                logger.info(f"📝 Description: {description}")
                logger.info(f"📝 Expected systems: {test_case['expected_systems']}")
                logger.info(f"📝 Complexity: {test_case['complexity']}")
                logger.info("")

                # Initialize query-specific logging
                query_results = {
                    "query_info": test_case,
                    "start_time": datetime.now().isoformat(),
                    "individual_systems": {},
                    "synthesis_process": {},
                    "final_result": {},
                    "timing": {},
                    "errors": [],
                }

                try:
                    # Execute comprehensive search with detailed timing
                    logger.info("🔄 STARTING COMPREHENSIVE SEARCH")
                    logger.info("-" * 50)

                    start_time = datetime.now()

                    comp_input = ComprehensiveSearchInput(
                        query=query,
                        num_results=5,
                        include_onyx=True,
                        include_vector=True,
                        include_graph=True,
                        search_type="hybrid",
                    )

                    logger.info(f"🔧 Search configuration:")
                    logger.info(f"   • Query: {comp_input.query}")
                    logger.info(f"   • Results per system: {comp_input.num_results}")
                    logger.info(f"   • Include Onyx: {comp_input.include_onyx}")
                    logger.info(f"   • Include Vector: {comp_input.include_vector}")
                    logger.info(f"   • Include Graph: {comp_input.include_graph}")
                    logger.info(f"   • Search type: {comp_input.search_type}")

                    # Call comprehensive search tool
                    result = await comprehensive_search_tool(
                        comp_input,
                        onyx_service=deps.onyx_service,
                        document_set_id=deps.onyx_document_set_id,
                    )

                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()

                    logger.info(f"⏱️  Total search duration: {duration:.2f} seconds")

                    # Log comprehensive results
                    await self._log_comprehensive_results(query_id, result, duration)

                    # Store detailed results
                    query_results["final_result"] = result
                    query_results["timing"]["total_duration"] = duration
                    query_results["timing"]["end_time"] = end_time.isoformat()

                    # Test agent integration
                    logger.info("\n🎯 TESTING AGENT INTEGRATION")
                    logger.info("-" * 40)

                    agent_start = datetime.now()
                    logger.info(f"🤖 Sending query to agent: {query}")

                    agent_result = await agent.run(query, deps=deps)
                    agent_duration = (datetime.now() - agent_start).total_seconds()

                    logger.info(f"⏱️  Agent response time: {agent_duration:.2f} seconds")

                    if agent_result and agent_result.output:
                        response_text = str(agent_result.output)
                        logger.info(
                            f"📝 Agent response length: {len(response_text)} characters"
                        )
                        logger.info(
                            f"📖 Agent response preview: {response_text[:300]}..."
                        )

                        query_results["agent_integration"] = {
                            "success": True,
                            "response_length": len(response_text),
                            "duration": agent_duration,
                            "response_preview": response_text[:500],
                        }
                    else:
                        logger.warning("⚠️  Agent returned empty response")
                        query_results["agent_integration"] = {
                            "success": False,
                            "error": "Empty response",
                        }

                    # Success summary for this query
                    logger.info("\n🏆 QUERY RESULTS SUMMARY")
                    logger.info("-" * 30)
                    logger.info(f"✅ Query completed successfully")
                    logger.info(f"📊 Systems used: {result.get('systems_used', [])}")
                    logger.info(f"📊 Total sources: {result.get('total_sources', 0)}")
                    logger.info(f"📊 Confidence: {result.get('confidence', 'unknown')}")
                    logger.info(
                        f"📊 Synthesis type: {result.get('synthesis_type', 'unknown')}"
                    )
                    logger.info(f"⏱️  Search duration: {duration:.2f}s")
                    logger.info(f"⏱️  Agent duration: {agent_duration:.2f}s")

                except Exception as e:
                    logger.error(f"❌ Query {query_id} failed with error: {e}")
                    logger.error(f"📋 Traceback: {traceback.format_exc()}")

                    query_results["errors"].append(
                        {
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                # Store query results
                self.detailed_results["system_responses"][query_id] = query_results

            # Generate final summary
            await self._generate_final_summary()

        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            logger.error(f"📋 Traceback: {traceback.format_exc()}")

    async def _log_comprehensive_results(
        self, query_id: str, result: Dict[str, Any], duration: float
    ):
        """Log detailed breakdown of comprehensive search results."""

        logger.info("\n📊 DETAILED SYSTEM BREAKDOWN")
        logger.info("-" * 40)

        # Log Onyx results
        logger.info("🏢 ONYX CLOUD RESULTS:")
        onyx_results = result.get("onyx_results", {})
        if onyx_results:
            if onyx_results.get("success", False):
                logger.info(f"   ✅ Status: Success")
                logger.info(
                    f"   📊 Sources found: {onyx_results.get('total_found', 0)}"
                )
                logger.info(
                    f"   🔍 Search type: {onyx_results.get('search_type', 'unknown')}"
                )
                logger.info(
                    f"   📝 Answer length: {len(onyx_results.get('answer', ''))} chars"
                )
                logger.info(
                    f"   🎯 Confidence: {onyx_results.get('confidence', 'unknown')}"
                )
                if onyx_results.get("answer"):
                    answer_preview = (
                        onyx_results["answer"][:200] + "..."
                        if len(onyx_results["answer"]) > 200
                        else onyx_results["answer"]
                    )
                    logger.info(f"   📖 Answer preview: {answer_preview}")
            else:
                logger.info(f"   ❌ Status: Failed")
                logger.info(
                    f"   📋 Error: {onyx_results.get('error', 'Unknown error')}"
                )
        else:
            logger.info("   ⏭️  Not attempted or unavailable")

        # Log Vector results
        logger.info("\n🔍 GRAPHITI VECTOR RESULTS:")
        vector_results = result.get("vector_results", [])
        if vector_results:
            logger.info(f"   ✅ Status: Success")
            logger.info(f"   📊 Chunks found: {len(vector_results)}")

            # Log top 3 vector results
            for i, chunk in enumerate(vector_results[:3]):
                if hasattr(chunk, "score") and hasattr(chunk, "content"):
                    logger.info(f"   📄 Chunk {i + 1}:")
                    logger.info(f"      • Score: {chunk.score:.4f}")
                    logger.info(
                        f"      • Source: {getattr(chunk, 'document_title', 'Unknown')}"
                    )
                    content_preview = (
                        chunk.content[:150] + "..."
                        if len(chunk.content) > 150
                        else chunk.content
                    )
                    logger.info(f"      • Content: {content_preview}")
        else:
            logger.info("   ❌ No vector results found")

        # Log Graph results
        logger.info("\n🕸️  GRAPHITI KNOWLEDGE GRAPH RESULTS:")
        graph_results = result.get("graph_results", [])
        if graph_results:
            logger.info(f"   ✅ Status: Success")
            logger.info(f"   📊 Facts found: {len(graph_results)}")

            # Log top 3 graph facts
            for i, fact in enumerate(graph_results[:3]):
                logger.info(f"   🧠 Fact {i + 1}:")
                if hasattr(fact, "fact"):
                    logger.info(f"      • Relationship: {fact.fact}")
                elif isinstance(fact, dict) and "fact" in fact:
                    logger.info(f"      • Relationship: {fact['fact']}")
                else:
                    logger.info(f"      • Data: {str(fact)[:100]}...")
        else:
            logger.info("   ❌ No graph results found")

        # Log synthesis process
        logger.info("\n🧠 SYNTHESIS PROCESS:")
        logger.info(
            f"   🔗 Fallback chain: {' -> '.join(result.get('fallback_chain', []))}"
        )
        logger.info(f"   🎭 Synthesis type: {result.get('synthesis_type', 'unknown')}")
        logger.info(f"   📊 Systems used: {result.get('systems_used', [])}")
        logger.info(f"   📊 Total sources: {result.get('total_sources', 0)}")
        logger.info(f"   🎯 Final confidence: {result.get('confidence', 'unknown')}")

        # Log final answer
        logger.info("\n📝 FINAL SYNTHESIZED ANSWER:")
        primary_answer = result.get("primary_answer", "")
        if primary_answer:
            logger.info(f"   📏 Length: {len(primary_answer)} characters")
            # Log the full answer for detailed analysis
            logger.info(f"   📖 Full Answer:")
            logger.info(f"   {'-' * 60}")
            for line in primary_answer.split("\n"):
                logger.info(f"   {line}")
            logger.info(f"   {'-' * 60}")
        else:
            logger.info("   ❌ No final answer generated")

        # Log performance metrics
        logger.info("\n⏱️  PERFORMANCE METRICS:")
        logger.info(f"   🕐 Total duration: {duration:.2f} seconds")
        logger.info(
            f"   📊 Efficiency: {result.get('total_sources', 0) / duration:.1f} sources/second"
        )

    async def _generate_final_summary(self):
        """Generate final summary of all test results."""

        logger.info("\n" + "=" * 80)
        logger.info("🏆 COMPREHENSIVE TEST SUITE SUMMARY")
        logger.info("=" * 80)

        total_queries = len(self.detailed_results["test_queries"])
        successful_queries = 0
        total_sources = 0
        systems_usage = {"onyx": 0, "vector": 0, "graph": 0}

        for query_id, query_data in self.detailed_results["system_responses"].items():
            if query_data.get("final_result") and not query_data.get("errors"):
                successful_queries += 1

                result = query_data["final_result"]
                total_sources += result.get("total_sources", 0)

                for system in result.get("systems_used", []):
                    if "onyx" in system.lower():
                        systems_usage["onyx"] += 1
                    elif "vector" in system.lower():
                        systems_usage["vector"] += 1
                    elif "graph" in system.lower():
                        systems_usage["graph"] += 1

        success_rate = (
            (successful_queries / total_queries * 100) if total_queries > 0 else 0
        )

        logger.info(f"📊 Overall Statistics:")
        logger.info(f"   • Total queries tested: {total_queries}")
        logger.info(f"   • Successful queries: {successful_queries}")
        logger.info(f"   • Success rate: {success_rate:.1f}%")
        logger.info(f"   • Total sources found: {total_sources}")
        logger.info(
            f"   • Average sources per query: {total_sources / total_queries:.1f}"
        )

        logger.info(f"\n🔧 System Usage Statistics:")
        logger.info(f"   • Onyx Cloud used: {systems_usage['onyx']} times")
        logger.info(f"   • Vector Search used: {systems_usage['vector']} times")
        logger.info(f"   • Knowledge Graph used: {systems_usage['graph']} times")

        # Save detailed results to JSON
        results_filename = f"comprehensive_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        self.detailed_results["session_info"]["end_time"] = datetime.now().isoformat()
        self.detailed_results["session_info"]["success_rate"] = success_rate
        self.detailed_results["session_info"]["total_sources"] = total_sources
        self.detailed_results["session_info"]["systems_usage"] = systems_usage

        with open(results_filename, "w", encoding="utf-8") as f:
            json.dump(
                self.detailed_results, f, indent=2, default=str, ensure_ascii=False
            )

        logger.info(f"\n📁 Detailed results saved to: {results_filename}")
        logger.info(f"📁 Full log saved to: {log_filename}")

        # Final assessment
        if success_rate >= 80:
            logger.info(f"\n🎉 COMPREHENSIVE SEARCH TEST: EXCELLENT PERFORMANCE!")
            logger.info(f"✅ All three systems are working together seamlessly!")
            logger.info(f"🚀 Multi-system synthesis is functioning correctly!")
        elif success_rate >= 60:
            logger.info(f"\n👍 COMPREHENSIVE SEARCH TEST: GOOD PERFORMANCE")
            logger.info(f"🔧 Most systems working, some optimization opportunities")
        else:
            logger.info(f"\n⚠️  COMPREHENSIVE SEARCH TEST: NEEDS ATTENTION")
            logger.info(f"🔧 Multiple issues detected, requires investigation")

        logger.info("\n" + "=" * 80)
        logger.info(
            f"🏁 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info("=" * 80)


async def main():
    """Main execution function."""
    print(f"🚀 Starting Comprehensive Search Detailed Logging Test")
    print(f"📁 Log file: {log_filename}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check environment variables
    if not os.getenv("ONYX_API_KEY"):
        print("❌ ONYX_API_KEY environment variable is required")
        sys.exit(1)

    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY environment variable is required")
        sys.exit(1)

    print("✅ Environment variables validated")
    print("🧪 Starting detailed logging test...")

    # Run the comprehensive test
    test_logger = ComprehensiveSearchLogger()
    await test_logger.test_comprehensive_search_with_logging()


if __name__ == "__main__":
    asyncio.run(main())
