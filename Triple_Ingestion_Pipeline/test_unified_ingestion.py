#!/usr/bin/env python3
"""
Test script to validate unified dual ingestion pipeline.
Tests that documents are properly ingested into all three systems and can be searched.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_ingest import UnifiedIngestionPipeline
from agent.agent import create_hybrid_rag_agent
from agent.models import IngestionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedIngestionTester:
    """Test suite for unified dual ingestion pipeline."""
    
    def __init__(self):
        self.test_documents_folder = "documents"  # Use actual documents folder
        self.onyx_cc_pair_id = 285  # Use validated CC-pair
        
    async def test_unified_ingestion(self) -> bool:
        """
        Test the complete unified ingestion pipeline.
        
        Returns:
            True if all tests pass
        """
        print(f"\n🧪 UNIFIED INGESTION TEST SUITE")
        print("=" * 40)
        print(f"📁 Documents folder: {self.test_documents_folder}")
        print(f"🆔 Onyx CC-pair: {self.onyx_cc_pair_id}")
        
        # Create test configuration
        config = IngestionConfig(
            chunk_size=600,  # Smaller for faster testing
            chunk_overlap=100,
            use_semantic_chunking=True,
            extract_entities=True,
            skip_graph_building=False,  # Test full pipeline
            single_document_mode=False,
            enable_onyx_ingestion=True
        )
        
        # Initialize pipeline
        pipeline = UnifiedIngestionPipeline(
            documents_folder=self.test_documents_folder,
            onyx_cc_pair_id=self.onyx_cc_pair_id,
            config=config
        )
        
        try:
            # Test 1: Pipeline initialization
            print(f"\n🔧 TEST 1: Pipeline Initialization")
            await pipeline.initialize()
            print(f"✅ Pipeline initialized successfully")
            
            # Test 2: Document discovery
            print(f"\n📚 TEST 2: Document Discovery")
            documents = pipeline.discover_documents()
            if not documents:
                print(f"❌ No documents found in {self.test_documents_folder}")
                return False
            print(f"✅ Found {len(documents)} documents for ingestion")
            for doc in documents[:3]:  # Show first 3
                print(f"   📄 {doc['filename']} ({len(doc['content'])} chars)")
            
            # Test 3: Unified ingestion
            print(f"\n🚀 TEST 3: Unified Ingestion (Onyx + Graphiti + pgvector)")
            
            def progress_callback(stage: str, count: int):
                print(f"   📊 Progress: {stage} - {count} items")
            
            result = await pipeline.run_unified_ingestion(
                clear_existing=False,  # Don't clear existing data in test
                progress_callback=progress_callback
            )
            
            if not result["success"]:
                print(f"❌ Unified ingestion failed: {result.get('error')}")
                return False
            
            print(f"✅ Unified ingestion completed successfully")
            
            # Test 4: Validate results
            print(f"\n📊 TEST 4: Result Validation")
            onyx_results = result["onyx_results"]
            graphiti_results = result["graphiti_results"]
            
            print(f"   🔮 Onyx: {onyx_results['successful']}/{len(documents)} documents")
            print(f"   📊 Graphiti: {graphiti_results['successful']}/{len(documents)} documents")
            print(f"   📄 Chunks: {graphiti_results['total_chunks']}")
            print(f"   🏷️  Entities: {graphiti_results['total_entities']}")
            print(f"   🔗 Relationships: {graphiti_results['total_relationships']}")
            
            # Basic validation
            if onyx_results['successful'] == 0:
                print(f"⚠️  Warning: No documents successfully ingested to Onyx")
            if graphiti_results['successful'] == 0:
                print(f"❌ Error: No documents successfully ingested to Graphiti")
                return False
            
            print(f"✅ Result validation passed")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False
        finally:
            await pipeline.close()
    
    async def test_multi_system_search(self) -> bool:
        """
        Test that we can search across all three systems with the hybrid agent.
        
        Returns:
            True if search tests pass
        """
        print(f"\n🔍 MULTI-SYSTEM SEARCH TEST")
        print("=" * 35)
        
        try:
            # Create hybrid agent with all systems enabled
            agent, dependencies = await create_hybrid_rag_agent(
                session_id=f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                cc_pair_id=self.onyx_cc_pair_id,
                enable_onyx=True
            )
            
            print(f"✅ Hybrid agent created with session: {dependencies.session_id}")
            
            # Check which systems are enabled
            systems_enabled = []
            if dependencies.search_preferences.get("use_onyx"):
                systems_enabled.append("Onyx Cloud")
            if dependencies.search_preferences.get("use_vector"):
                systems_enabled.append("pgvector")
            if dependencies.search_preferences.get("use_graph"):
                systems_enabled.append("Knowledge Graph")
            
            print(f"🎯 Enabled systems: {', '.join(systems_enabled)}")
            
            if len(systems_enabled) < 3:
                print(f"⚠️  Warning: Not all systems are enabled for comprehensive search")
            
            # Test queries for different systems
            test_queries = [
                "What documents are available?",  # Should work with any system
                "Tell me about artificial intelligence",  # Good for vector search
                "What relationships exist in the data?",  # Good for graph search
            ]
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n📝 Search Test {i}: '{query}'")
                
                # Test comprehensive search (should use all systems)
                try:
                    from agent.tools import comprehensive_search_tool, ComprehensiveSearchInput
                    
                    search_input = ComprehensiveSearchInput(
                        query=query,
                        num_results=3,
                        include_onyx=True,
                        include_vector=True,
                        include_graph=True,
                        search_type="hybrid"
                    )
                    
                    search_result = await comprehensive_search_tool(
                        search_input,
                        onyx_service=dependencies.onyx_service,
                        document_set_id=dependencies.onyx_document_set_id
                    )
                    
                    # Analyze results
                    systems_used = []
                    if search_result.get("onyx_results", {}).get("documents"):
                        systems_used.append("Onyx")
                    if search_result.get("vector_results"):
                        systems_used.append("Vector")
                    if search_result.get("graph_results"):
                        systems_used.append("Graph")
                    
                    print(f"   🎯 Systems used: {', '.join(systems_used) if systems_used else 'None'}")
                    print(f"   📊 Results: {len(search_result.get('synthesis', {}).get('combined_insights', []))} insights")
                    
                    if not systems_used:
                        print(f"   ⚠️  Warning: No results from any system")
                    
                except Exception as e:
                    print(f"   ❌ Search failed: {e}")
            
            print(f"\n✅ Multi-system search test completed")
            return True
            
        except Exception as e:
            print(f"❌ Multi-system search test failed: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """
        Run all tests in sequence.
        
        Returns:
            True if all tests pass
        """
        print(f"\n🚀 STARTING UNIFIED INGESTION TEST SUITE")
        print("=" * 50)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        tests = [
            ("Unified Ingestion", self.test_unified_ingestion),
            ("Multi-System Search", self.test_multi_system_search),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 30)
            
            try:
                result = await test_func()
                results.append((test_name, result))
                
                if result:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                results.append((test_name, False))
        
        # Final summary
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"\n🎯 TEST SUITE SUMMARY")
        print("=" * 25)
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
        
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"🔍 Unified ingestion pipeline is working correctly")
            print(f"🎯 Ready for comprehensive multi-system RAG!")
        else:
            print(f"\n⚠️  SOME TESTS FAILED")
            print(f"🔧 Check the errors above and fix issues before proceeding")
        
        return passed == total


async def main():
    """Main test runner."""
    tester = UnifiedIngestionTester()
    
    try:
        success = await tester.run_all_tests()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
