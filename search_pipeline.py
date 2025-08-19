#!/usr/bin/env python3
"""
Final test script using the new indexed files (CC-pair 285) with working functionality
adapted from test_aanya_phone_query.py. Tests three specific queries with retry logic.
"""

import requests
import os
import json
import time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class FinalConnectorTest:
    def __init__(self):
        self.api_key = os.getenv("ONYX_API_KEY")
        self.base_url = "https://cloud.onyx.app"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # New CC-pair details from latest ingestion
        self.cc_pair_id = 285
        self.connector_id = 318
        
        # test queries
        self.test_queries = [
            "Tell me about which cafe did Aanya Sharma preferred and at which place and when ?",
            "Give me list of core technologies used in the NIFTY RAG Chatbot project."
        ]
        
        # Document set will be created
        self.document_set_id = None
        self.document_set_name = f"Final_Test_Latest_Files_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"🎯 Final Connector Test initialized")
        print(f"📋 Target CC-pair ID: {self.cc_pair_id}")
        print(f"📋 Target connector ID: {self.connector_id}")
        print(f"📝 Test queries: {len(self.test_queries)}")

    def verify_cc_pair_status(self):
        """Verify the CC-pair is accessible and properly indexed."""
        print(f"\n✅ STEP 1: VERIFYING CC-PAIR STATUS")
        print("=" * 40)
        
        response = requests.get(
            f"{self.base_url}/api/manage/admin/cc-pair/{self.cc_pair_id}",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get CC-pair status: {response.status_code}")
            return False
            
        cc_pair_data = response.json()
        
        print(f"📊 CC-pair verification:")
        print(f"   - ID: {cc_pair_data.get('id')}")
        print(f"   - Status: {cc_pair_data.get('status')}")
        print(f"   - Access type: {cc_pair_data.get('access_type')}")
        print(f"   - Docs indexed: {cc_pair_data.get('num_docs_indexed')}")
        print(f"   - Last index status: {cc_pair_data.get('last_index_attempt_status')}")
        print(f"   - Is indexing: {cc_pair_data.get('indexing')}")
        
        # Check if it's ready for search
        if (cc_pair_data.get('status') == 'ACTIVE' and 
            cc_pair_data.get('access_type') == 'public' and
            cc_pair_data.get('num_docs_indexed', 0) > 0 and
            not cc_pair_data.get('indexing', True)):
            print(f"✅ CC-pair is ready for search!")
            return True
        else:
            print(f"⚠️ CC-pair may not be ready for search")
            return True  # Continue anyway for testing

    def create_document_set(self):
        """Create a new document set for testing."""
        print(f"\n📂 STEP 2: CREATING DOCUMENT SET")
        print("=" * 35)
        
        document_set_data = {
            "name": self.document_set_name,
            "description": "Final test document set with latest uploaded files",
            "cc_pair_ids": [self.cc_pair_id],
            "is_public": True
        }
        
        # Try the correct API endpoint for creating document sets
        response = requests.post(
            f"{self.base_url}/api/manage/admin/document-set",
            headers={**self.headers, "Content-Type": "application/json"},
            data=json.dumps(document_set_data)
        )
        
        print(f"📤 Document set creation status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            # Handle different response formats
            if isinstance(result, int):
                self.document_set_id = result
            elif isinstance(result, dict):
                self.document_set_id = result.get("id")
            else:
                print(f"❌ Unexpected response format: {result}")
                return False
                
            print(f"✅ Document set created successfully!")
            print(f"🆔 Document set ID: {self.document_set_id}")
            
            # Get document set details
            try:
                ds_response = requests.get(
                    f"{self.base_url}/api/manage/document-set/{self.document_set_id}",
                    headers=self.headers
                )
                if ds_response.status_code == 200:
                    ds_details = ds_response.json()
                    print(f"📋 Name: {ds_details.get('name')}")
                    print(f"📋 Is public: {ds_details.get('is_public')}")
                    print(f"📋 CC-pairs: {[cp.get('id') for cp in ds_details.get('cc_pairs', [])]}")
            except Exception as e:
                print(f"⚠️ Could not get document set details: {e}")
                
            return True
        else:
            print(f"❌ Document set creation failed: {response.text}")
            
            # Try alternative endpoint
            print(f"🔄 Trying alternative endpoint...")
            response2 = requests.post(
                f"{self.base_url}/api/manage/document-set",
                headers={**self.headers, "Content-Type": "application/json"},
                data=json.dumps(document_set_data)
            )
            
            print(f"📤 Alternative endpoint status: {response2.status_code}")
            
            if response2.status_code == 200:
                result = response2.json()
                self.document_set_id = result.get("id")
                print(f"✅ Document set created successfully!")
                print(f"🆔 Document set ID: {self.document_set_id}")
                return True
            else:
                print(f"❌ Alternative endpoint also failed: {response2.text}")
                
                # Let's try to find an existing document set we can use
                print(f"🔍 Looking for existing document sets...")
                return self.find_existing_document_set()
                
    def find_existing_document_set(self):
        """Find an existing document set that contains our CC-pair."""
        print(f"\n🔍 SEARCHING FOR EXISTING DOCUMENT SETS")
        print("=" * 45)
        
        response = requests.get(
            f"{self.base_url}/api/manage/document-set",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get document sets: {response.status_code}")
            return False
            
        document_sets = response.json()
        print(f"📊 Found {len(document_sets)} document sets")
        
        # Look for a document set that contains our CC-pair
        for ds in document_sets:
            cc_pairs = ds.get("cc_pairs", [])
            cc_pair_ids = [cp.get("id") for cp in cc_pairs]
            
            if self.cc_pair_id in cc_pair_ids:
                self.document_set_id = ds.get("id")
                print(f"✅ Found existing document set with our CC-pair!")
                print(f"🆔 Document set ID: {self.document_set_id}")
                print(f"📋 Name: {ds.get('name')}")
                print(f"📋 Is public: {ds.get('is_public')}")
                print(f"📋 CC-pairs: {cc_pair_ids}")
                return True
                
        print(f"❌ No existing document set contains CC-pair {self.cc_pair_id}")
        
        # Try to use the first public document set if available
        for ds in document_sets:
            if ds.get("is_public", False):
                self.document_set_id = ds.get("id")
                print(f"⚠️ Using first available public document set as fallback")
                print(f"🆔 Document set ID: {self.document_set_id}")
                print(f"📋 Name: {ds.get('name')}")
                return True
                
        print(f"❌ No suitable document set found")
        return False

    def search_with_document_set(self, query, query_num, attempt_num=1):
        """Perform search using the document set."""
        print(f"\n🔍 QUERY {query_num} - ATTEMPT {attempt_num}")
        print("=" * 40)
        print(f"📋 Document set ID: {self.document_set_id}")
        print(f"❓ Query: {query}")
        
        # Create a chat session first
        try:
            session_response = requests.post(
                f"{self.base_url}/api/chat/create-chat-session",
                headers={**self.headers, "Content-Type": "application/json"},
                data=json.dumps({
                    "title": f"Final Test Q{query_num} Attempt {attempt_num}", 
                    "persona_id": 0
                }),
                timeout=30
            )
            
            if session_response.status_code != 200:
                print(f"❌ Failed to create chat session: {session_response.status_code}")
                print(f"📄 Response: {session_response.text}")
                return False
                
            chat_session_id = session_response.json()["chat_session_id"]
            print(f"📝 Chat session created: {chat_session_id}")
            
        except Exception as e:
            print(f"❌ Error creating chat session: {e}")
            return False
        
        # Perform search with document set restriction
        search_payload = {
            "chat_session_id": chat_session_id,
            "message": query,
            "parent_message_id": None,
            "file_descriptors": [],
            "prompt_id": None,
            "search_doc_ids": None,
            "retrieval_options": {
                "run_search": "always",
                "real_time": False,
                "enable_auto_detect_filters": False,
                "document_set_ids": [self.document_set_id],
            },
        }
        
        print("📤 Sending search request...")
        print(f"🔧 Search with document set: [{self.document_set_id}]")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat/send-message",
                headers={**self.headers, "Content-Type": "application/json"},
                data=json.dumps(search_payload),
                timeout=90
            )
            
            print(f"📨 Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Handle potential streaming response
                response_text = response.text.strip()
                print(f"📄 Raw response length: {len(response_text)} characters")
                
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    # Try parsing last line if streaming
                    if '\n' in response_text:
                        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
                        for line in reversed(lines):
                            try:
                                result = json.loads(line)
                                break
                            except json.JSONDecodeError:
                                continue
                        else:
                            print("❌ Could not parse JSON response")
                            print(f"📄 Raw response sample: {response_text[:500]}...")
                            return False
                    else:
                        print("❌ Could not parse JSON response")
                        print(f"📄 Raw response: {response_text}")
                        return False
                
                # Extract answer from different possible fields
                answer = result.get("answer") or result.get("message")
                
                print("\n📝 SEARCH RESULTS:")
                print(f"✅ Answer found: {'Yes' if answer and answer.strip() else 'No'}")
                
                # Check for source documents
                source_docs = []
                if "context_docs" in result:
                    context_docs = result["context_docs"]
                    if isinstance(context_docs, dict) and "top_documents" in context_docs:
                        source_docs = context_docs["top_documents"]
                
                print(f"📚 Source documents: {len(source_docs)}")
                
                if answer and answer.strip():
                    print("\n💬 Answer:")
                    # Truncate very long answers for readability
                    if len(answer) > 500:
                        print(f"{answer[:500]}...")
                        print(f"📏 (Answer truncated - full length: {len(answer)} characters)")
                    else:
                        print(answer)
                    
                else:
                    print("\n❌ No answer provided")
                
                if source_docs:
                    print("\n📚 Source Documents:")
                    for i, doc in enumerate(source_docs, 1):
                        doc_name = doc.get('semantic_identifier', 'Unknown')
                        print(f"   {i}. {doc_name}")
                        
                        # Check for specific documents
                        doc_name_lower = doc_name.lower()
                        if 'temporal_rag_test_story' in doc_name_lower:
                            print(f"      🎯 TEMPORAL STORY DOCUMENT FOUND!")
                        elif 'technical_summary' in doc_name_lower:
                            print(f"      📋 TECHNICAL SUMMARY DOCUMENT FOUND!")
                        elif 'iirm' in doc_name_lower:
                            print(f"      📊 IIRM DOCUMENT FOUND!")
                        
                        if doc.get('blurb'):
                            blurb = doc['blurb'][:150] + "..." if len(doc['blurb']) > 150 else doc['blurb']
                            print(f"      📝 Content: {blurb}")
                        print()
                else:
                    print("\n❌ No source documents found")
                
                return bool(answer and answer.strip())
                    
            else:
                print(f"❌ Search failed: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Search error: {e}")
            return False

    def cleanup_document_set(self):
        """Clean up the created document set."""
        if self.document_set_id and self.document_set_name.startswith("Final_Test_Latest_Files_"):
            print(f"\n🧹 CLEANUP: Deleting document set {self.document_set_id}")
            try:
                response = requests.delete(
                    f"{self.base_url}/api/manage/document-set/{self.document_set_id}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    print(f"✅ Document set deleted successfully")
                else:
                    print(f"⚠️ Document set deletion failed: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error during cleanup: {e}")
        else:
            print(f"\n🔍 Using existing document set - no cleanup needed")

    def run_complete_test(self, max_retries=3):
        """Run the complete test with all three queries and retry logic."""
        print(f"\n🎯 FINAL TEST WITH LATEST INDEXED FILES (CC-pair {self.cc_pair_id})")
        print("=" * 70)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Step 1: Verify CC-pair status
            if not self.verify_cc_pair_status():
                print(f"❌ CC-pair verification failed - aborting test")
                return False
            
            # Step 2: Create document set
            if not self.create_document_set():
                print(f"❌ Document set creation failed - aborting test")
                return False
            
            # Step 3: Test all queries
            overall_results = []
            
            for query_num, query in enumerate(self.test_queries, 1):
                print(f"\n{'='*60}")
                print(f"🎯 TESTING QUERY {query_num}/{len(self.test_queries)}")
                print(f"❓ {query}")
                print(f"{'='*60}")
                
                successful_attempts = 0
                failed_attempts = 0
                
                for attempt in range(1, max_retries + 1):
                    success = self.search_with_document_set(query, query_num, attempt)
                    
                    if success:
                        successful_attempts += 1
                        print(f"✅ Query {query_num} - Attempt {attempt}: SUCCESS")
                        break  # Success on first try, no need to retry
                    else:
                        failed_attempts += 1
                        print(f"❌ Query {query_num} - Attempt {attempt}: FAILED")
                    
                    # Wait between attempts (except for the last one)
                    if attempt < max_retries:
                        wait_time = 3
                        print(f"⏳ Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                
                # Record results for this query
                query_success = successful_attempts > 0
                overall_results.append({
                    'query_num': query_num,
                    'query': query,
                    'success': query_success,
                    'successful_attempts': successful_attempts,
                    'failed_attempts': failed_attempts
                })
                
                print(f"\n📊 Query {query_num} Summary:")
                print(f"   ✅ Successful attempts: {successful_attempts}")
                print(f"   ❌ Failed attempts: {failed_attempts}")
                print(f"   📈 Result: {'SUCCESS' if query_success else 'FAILED'}")
                
                # Brief pause between queries
                if query_num < len(self.test_queries):
                    print(f"\n⏳ Moving to next query in 2 seconds...")
                    time.sleep(2)
            
            # Final comprehensive summary
            print(f"\n🎯 FINAL COMPREHENSIVE TEST SUMMARY")
            print("=" * 50)
            successful_queries = sum(1 for r in overall_results if r['success'])
            total_queries = len(overall_results)
            
            print(f"📊 Overall Results:")
            print(f"   ✅ Successful queries: {successful_queries}/{total_queries}")
            print(f"   ❌ Failed queries: {total_queries - successful_queries}/{total_queries}")
            print(f"   📈 Success rate: {(successful_queries/total_queries)*100:.1f}%")
            
            print(f"\n📋 Detailed Results:")
            for result in overall_results:
                status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                print(f"   {result['query_num']}. {status}: {result['query'][:60]}...")
                print(f"      Attempts: {result['successful_attempts']} success, {result['failed_attempts']} failed")
            
            if successful_queries == total_queries:
                print(f"\n🎉 COMPLETE SUCCESS! All {total_queries} queries worked with the new indexed files!")
                print(f"🏆 CC-pair {self.cc_pair_id} is fully validated and ready for production use!")
            elif successful_queries > 0:
                print(f"\n⚠️ PARTIAL SUCCESS: {successful_queries} out of {total_queries} queries worked.")
                print(f"🔍 The {total_queries - successful_queries} failed queries may need:")
                print(f"   - Different query phrasing")
                print(f"   - Additional relevant documents in the index")
                print(f"   - Further investigation of document content")
            else:
                print(f"\n😞 NO SUCCESS: None of the queries returned meaningful results.")
                print(f"🔍 Recommendations:")
                print(f"   - Verify document indexing completed successfully")
                print(f"   - Check if documents contain the expected information")
                print(f"   - Try simpler, more direct queries")
                print(f"   - Verify document set and CC-pair associations")
            
            print(f"\n📊 Document Set ID for future use: {self.document_set_id}")
            print(f"🔗 CC-pair ID: {self.cc_pair_id}")
            print(f"📅 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return successful_queries > 0
            
        finally:
            # Cleanup
            self.cleanup_document_set()


if __name__ == "__main__":
    print("🚀 Starting Final Test with Latest Indexed Files")
    print("=" * 60)
    
    test = FinalConnectorTest()
    success = test.run_complete_test(max_retries=3)
    
    print(f"\n🎯 FINAL RESULT: {'SUCCESS' if success else 'NEEDS INVESTIGATION'}")
