#!/usr/bin/env python3
"""
UNIFIED TRIPLE INGESTION SYSTEM - COMPLETE IMPLEMENTATION
Ingests documents into all three systems with flexible Onyx Cloud options:

1. ONYX CLOUD - THREE OPTIONS:
   Option A: Use existing CC-pair 285 (faster, reuses infrastructure)
   Option B: Create new connector each time (standalone, isolated, validated workflow)
   Option C: Skip Onyx ingestion entirely (when documents already indexed in Onyx)

2. GRAPHITI (for knowledge graph and entity relationships)

3. PGVECTOR (for semantic embeddings and similarity search)

This provides comprehensive coverage for advanced RAG capabilities with flexible Onyx handling.
"""

import argparse
import logging
import time
import asyncio
import os
import json
import glob
from datetime import datetime
from pathlib import Path
import sys
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
from ingestion.ingest import DocumentIngestionPipeline, validate_gemini_configuration
from ingestion.onyx_ingest import bulk_ingest_to_onyx, OnyxIngestionError
from onyx_cloud_integration import OnyxCloudIntegration
from agent.models import IngestionConfig

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('unified_ingestion.log')
    ]
)
logger = logging.getLogger(__name__)


class UnifiedTripleIngestionPipeline:
    """
    Unified pipeline that ingests documents into all three systems:
    - Onyx Cloud (with flexible options)
    - Graphiti Knowledge Graph
    - pgvector embeddings
    """
    
    def __init__(self, documents_folder: str, onyx_mode: str = "existing", 
                 clear_local_data: bool = False, verbose: bool = False):
        """
        Initialize the unified ingestion pipeline.
        
        Args:
            documents_folder: Path to documents to ingest
            onyx_mode: "existing" (use CC-pair 285), "new" (create new connector), or "skip" (skip Onyx)
            clear_local_data: Whether to clear Graphiti + pgvector before ingesting
            verbose: Enable verbose logging
        """
        self.documents_folder = Path(documents_folder)
        self.onyx_mode = onyx_mode
        self.clear_local_data = clear_local_data
        self.verbose = verbose
        
        # Onyx configuration
        self.onyx_cc_pair_id = 285  # For existing mode
        
        # Initialize components
        self.graphiti_pipeline = None
        self.onyx_integration = None
        self._initialized = False
        
        # Results tracking
        self.results = {
            "onyx": {"status": "pending", "documents": 0, "details": ""},
            "graphiti": {"status": "pending", "documents": 0, "chunks": 0, "entities": 0, "relationships": 0},
            "pgvector": {"status": "pending", "documents": 0, "chunks": 0}
        }
        
        # Setup logging level
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info(f"🚀 Unified Triple Ingestion Pipeline initialized")
        logger.info(f"   📁 Documents: {self.documents_folder}")
        logger.info(f"   🔮 Onyx mode: {self.onyx_mode}")
        logger.info(f"   🧹 Clear local: {self.clear_local_data}")
    
    async def initialize(self):
        """Initialize all ingestion components."""
        if self._initialized:
            return
        
        logger.info("🔧 Initializing ingestion components...")
        
        # Validate environment
        validate_gemini_configuration()
        
        # Initialize Graphiti pipeline (handles both Graphiti + pgvector)
        # NOTE: Explicitly set single_document_mode=False to process ALL documents
        config = IngestionConfig(single_document_mode=False)
        self.graphiti_pipeline = DocumentIngestionPipeline(
            config=config,
            documents_folder=str(self.documents_folder),
            clean_before_ingest=False  # We handle cleaning separately
        )
        await self.graphiti_pipeline.initialize()
        
        # Initialize Onyx integration for new connector mode
        if self.onyx_mode == "new":
            self.onyx_integration = OnyxCloudIntegration()
        elif self.onyx_mode == "skip":
            logger.info("🔮 Onyx ingestion will be SKIPPED - assuming documents already indexed")
        
        self._initialized = True
        logger.info("✅ All components initialized")
    
    def get_document_files(self) -> List[Path]:
        """Get all document files from the documents folder."""
        if not self.documents_folder.exists():
            logger.error(f"❌ Documents folder not found: {self.documents_folder}")
            return []
        
        # Supported file extensions
        extensions = ['*.md', '*.txt', '*.json', '*.pdf', '*.docx', '*.xlsx', '*.pptx', '*.csv']
        files = []
        
        for ext in extensions:
            files.extend(self.documents_folder.glob(ext))
        
        logger.info(f"📁 Found {len(files)} documents to process:")
        for i, file_path in enumerate(files, 1):
            size = file_path.stat().st_size
            logger.info(f"   {i}. {file_path.name} ({size} bytes)")
        
        return files
    
    async def clear_local_data_if_requested(self):
        """Clear local data (Graphiti + pgvector) if requested."""
        if not self.clear_local_data:
            return
        
        logger.info("🧹 CLEARING LOCAL DATA (Graphiti + pgvector)")
        logger.info("   ⚠️  Onyx Cloud data is NEVER modified - completely safe!")
        
        try:
            await self.graphiti_pipeline._clean_databases()
            logger.info("✅ Local data cleared successfully")
        except Exception as e:
            logger.error(f"❌ Failed to clear local data: {e}")
            raise
    
    async def ingest_to_onyx_existing(self, files: List[Path]) -> bool:
        """Ingest documents to Onyx Cloud using existing CC-pair 285."""
        logger.info(f"🔮 ONYX CLOUD INGESTION (Existing CC-pair {self.onyx_cc_pair_id})")
        logger.info("=" * 50)
        
        try:
            # Prepare documents in the format expected by bulk_ingest_to_onyx
            documents = []
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    documents.append({
                        'content': content,
                        'file_path': str(file_path),
                        'metadata': {
                            'filename': file_path.name,
                            'size': file_path.stat().st_size,
                            'extension': file_path.suffix
                        }
                    })
                except Exception as e:
                    logger.error(f"❌ Failed to read file {file_path}: {e}")
                    continue
            
            if not documents:
                logger.error("❌ No documents could be prepared for Onyx ingestion")
                return False
            
            # Use the corrected bulk_ingest_to_onyx function
            results = await bulk_ingest_to_onyx(
                documents=documents,
                cc_pair_id=self.onyx_cc_pair_id
            )
            
            # Process results
            successful_uploads = sum(1 for r in results if r.get("success", False))
            failed_uploads = len(results) - successful_uploads
            
            if successful_uploads > 0:
                self.results["onyx"]["status"] = "success" if failed_uploads == 0 else "partial"
                self.results["onyx"]["documents"] = successful_uploads
                self.results["onyx"]["details"] = f"CC-pair {self.onyx_cc_pair_id}, {successful_uploads}/{len(results)} successful"
                
                logger.info(f"✅ Onyx Cloud: {successful_uploads} documents uploaded successfully")
                if failed_uploads > 0:
                    logger.warning(f"⚠️  Onyx Cloud: {failed_uploads} documents failed")
                return True
            else:
                self.results["onyx"]["status"] = "failed"
                self.results["onyx"]["details"] = f"All {len(results)} uploads failed"
                
                logger.error(f"❌ Onyx Cloud ingestion failed: All uploads failed")
                return False
                
        except Exception as e:
            self.results["onyx"]["status"] = "failed"
            self.results["onyx"]["details"] = str(e)
            logger.error(f"❌ Onyx Cloud ingestion error: {e}")
            return False
    
    async def skip_onyx_ingestion(self, files: List[Path]) -> bool:
        """Skip Onyx ingestion - documents assumed to be already indexed."""
        logger.info("🔮 ONYX CLOUD INGESTION (SKIPPED)")
        logger.info("=" * 35)
        logger.info("📋 Assumption: Documents already indexed in Onyx Cloud")
        logger.info("🔍 Hybrid search will still access Onyx during queries")
        logger.info("⚡ This saves 30-60 minutes of indexing time!")
        
        # Mark Onyx as successful but skipped
        self.results["onyx"]["status"] = "skipped"
        self.results["onyx"]["documents"] = len(files)
        self.results["onyx"]["details"] = "Ingestion skipped - documents assumed pre-indexed"
        
        logger.info(f"⏭️  Onyx Cloud: Skipped ingestion for {len(files)} documents")
        logger.info("✅ Onyx will still be available for hybrid search")
        
        return True  # Always return True since we're intentionally skipping
    
    async def ingest_to_onyx_new_connector(self, files: List[Path]) -> bool:
        """Ingest documents to Onyx Cloud using new connector workflow."""
        logger.info("🔮 ONYX CLOUD INGESTION (New Connector)")
        logger.info("=" * 40)
        
        try:
            # Run the complete validated workflow
            success = self.onyx_integration.run_complete_workflow()
            
            if success:
                # For new connector mode, we know it processed all files in the documents folder
                uploaded_count = len(files)
                
                self.results["onyx"]["status"] = "success"
                self.results["onyx"]["documents"] = uploaded_count
                self.results["onyx"]["details"] = f"New connector {self.onyx_integration.connector_id}"
                
                logger.info(f"✅ Onyx Cloud: {uploaded_count} documents processed with new connector")
                logger.info(f"🔗 Access your connector at: https://cloud.onyx.app/admin/connector/{self.onyx_integration.connector_id}")
                return True
            else:
                self.results["onyx"]["status"] = "failed"
                self.results["onyx"]["details"] = "New connector workflow failed"
                logger.error("❌ Onyx Cloud new connector workflow failed")
                return False
                
        except Exception as e:
            self.results["onyx"]["status"] = "failed"
            self.results["onyx"]["details"] = str(e)
            logger.error(f"❌ Onyx Cloud new connector error: {e}")
            return False
    
    async def ingest_to_graphiti_pgvector(self, files: List[Path]) -> bool:
        """Ingest documents to Graphiti + pgvector."""
        logger.info("🧠 GRAPHITI + PGVECTOR INGESTION")
        logger.info("=" * 35)
        
        try:
            # Use the existing ingest_documents method that processes files from the documents folder
            results = await self.graphiti_pipeline.ingest_documents()
            
            # Extract results
            total_chunks = sum(r.chunks_created for r in results)
            total_errors = sum(len(r.errors) for r in results)
            entities_count = sum(r.entities_extracted for r in results)
            relationships_count = sum(r.relationships_created for r in results)
            processed_files = len([r for r in results if r.chunks_created > 0])
            
            # Update results
            if total_errors < len(files):  # Some success
                self.results["graphiti"]["status"] = "success" if total_errors == 0 else "partial"
                self.results["pgvector"]["status"] = "success" if total_errors == 0 else "partial"
            else:
                self.results["graphiti"]["status"] = "failed"
                self.results["pgvector"]["status"] = "failed"
            
            self.results["graphiti"]["documents"] = processed_files
            self.results["graphiti"]["chunks"] = total_chunks
            self.results["graphiti"]["entities"] = entities_count
            self.results["graphiti"]["relationships"] = relationships_count
            
            self.results["pgvector"]["documents"] = processed_files
            self.results["pgvector"]["chunks"] = total_chunks
            
            logger.info(f"✅ Graphiti + pgvector: {processed_files} documents processed")
            logger.info(f"   📊 Total chunks: {total_chunks}")
            logger.info(f"   🔗 Total relationships: {relationships_count}")
            logger.info(f"   🏷️  Total entities: {entities_count}")
            
            return total_errors == 0
            
        except Exception as e:
            self.results["graphiti"]["status"] = "failed"
            self.results["pgvector"]["status"] = "failed"
            logger.error(f"❌ Graphiti + pgvector ingestion error: {e}")
            return False
    
    async def run_complete_ingestion(self):
        """Run the complete unified ingestion pipeline."""
        start_time = datetime.now()
        logger.info("🎯 UNIFIED TRIPLE INGESTION STARTING")
        logger.info("=" * 50)
        logger.info(f"📅 Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Initialize components
            await self.initialize()
            
            # Get document files
            files = self.get_document_files()
            if not files:
                logger.error("❌ No documents found to process")
                return False
            
            # Clear local data if requested
            await self.clear_local_data_if_requested()
            
            # Track individual results
            onyx_success = False
            graphiti_success = False
            
            # 1. Ingest to Onyx Cloud
            logger.info(f"\n🔮 STEP 1: ONYX CLOUD INGESTION ({self.onyx_mode.upper()} MODE)")
            if self.onyx_mode == "existing":
                onyx_success = await self.ingest_to_onyx_existing(files)
            elif self.onyx_mode == "new":
                onyx_success = self.ingest_to_onyx_new_connector(files)
            elif self.onyx_mode == "skip":
                onyx_success = await self.skip_onyx_ingestion(files)
            else:
                logger.error(f"❌ Invalid Onyx mode: {self.onyx_mode}")
                self.results["onyx"]["status"] = "failed"
                self.results["onyx"]["details"] = f"Invalid mode: {self.onyx_mode}"
            
            # 2. Ingest to Graphiti + pgvector
            logger.info(f"\n🧠 STEP 2: GRAPHITI + PGVECTOR INGESTION")
            graphiti_success = await self.ingest_to_graphiti_pgvector(files)
            
            # Calculate final results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Print comprehensive summary
            self.print_final_summary(start_time, end_time, duration, len(files))
            
            # Return overall success
            return onyx_success and graphiti_success
            
        except Exception as e:
            logger.error(f"❌ Unified ingestion failed: {e}")
            return False
    
    def print_final_summary(self, start_time: datetime, end_time: datetime, 
                          duration: float, total_files: int):
        """Print comprehensive final summary."""
        print(f"\n🎯 UNIFIED INGESTION COMPLETE")
        print("=" * 50)
        print(f"📅 Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📚 Total documents: {total_files}")
        
        # Onyx results
        onyx = self.results["onyx"]
        if onyx["status"] == "skipped":
            onyx_icon = "⏭️"
        else:
            onyx_icon = "✅" if onyx["status"] == "success" else "⚠️" if onyx["status"] == "partial" else "❌"
        print(f"\n🔮 ONYX CLOUD INGESTION ({self.onyx_mode.upper()}):")
        print(f"   {onyx_icon} Status: {onyx['status'].title()}")
        print(f"   📄 Documents: {onyx['documents']}")
        print(f"   📋 Details: {onyx['details']}")
        
        # Graphiti results
        graphiti = self.results["graphiti"]
        graphiti_icon = "✅" if graphiti["status"] == "success" else "⚠️" if graphiti["status"] == "partial" else "❌"
        print(f"🧠 GRAPHITI KNOWLEDGE GRAPH:")
        print(f"   {graphiti_icon} Status: {graphiti['status'].title()}")
        print(f"   📄 Documents: {graphiti['documents']}")
        print(f"   📊 Chunks: {graphiti['chunks']}")
        print(f"   🏷️  Entities: {graphiti['entities']}")
        print(f"   🔗 Relationships: {graphiti['relationships']}")
        
        # pgvector results  
        pgvector = self.results["pgvector"]
        pgvector_icon = "✅" if pgvector["status"] == "success" else "⚠️" if pgvector["status"] == "partial" else "❌"
        print(f"🔍 PGVECTOR EMBEDDINGS:")
        print(f"   {pgvector_icon} Status: {pgvector['status'].title()}")
        print(f"   📄 Documents: {pgvector['documents']}")
        print(f"   📊 Chunks: {pgvector['chunks']}")
        
        # Overall status
        successful_systems = [r for r in self.results.values() if r["status"] in ["success", "skipped"]]
        all_success = len(successful_systems) == len(self.results)
        
        if all_success:
            if self.onyx_mode == "skip":
                print(f"\n🎉 GRAPHITI + PGVECTOR SUCCESSFULLY UPDATED!")
                print(f"🔍 Ready for hybrid search (Onyx assumed pre-indexed)!")
            else:
                print(f"\n🎉 ALL THREE SYSTEMS SUCCESSFULLY UPDATED!")
                print(f"🔍 Ready for comprehensive multi-system search!")
        else:
            print(f"\n⚠️  PARTIAL SUCCESS - Some systems updated")
            print(f"🔍 Available systems can still be used for search")
        
        print("=" * 50)
        
        # Success message
        successful_systems = [r for r in self.results.values() if r["status"] in ["success", "skipped"]]
        all_success = len(successful_systems) == len(self.results)
        
        if all_success:
            if self.onyx_mode == "skip":
                print(f"\n🎉 GRAPHITI + PGVECTOR INGESTION SUCCESSFUL!")
                print(f"🔍 Ready for hybrid search with pre-indexed Onyx!")
            else:
                print(f"\n🎉 UNIFIED INGESTION SUCCESSFUL!")
                print(f"🔍 All systems ready for comprehensive multi-system search")


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Unified Triple Ingestion Pipeline - Onyx Cloud + Graphiti + pgvector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use existing CC-pair 285 (default, faster)
  python unified_ingest_complete.py --documents documents

  # Create new Onyx connector each time
  python unified_ingest_complete.py --documents documents --onyx-mode new

  # Skip Onyx ingestion (when documents already indexed in Onyx)
  python unified_ingest_complete.py --documents documents --onyx-mode skip

  # Clear local data before ingesting
  python unified_ingest_complete.py --documents documents --clear

  # Skip Onyx with verbose logging and clear local data
  python unified_ingest_complete.py --documents documents --onyx-mode skip --clear --verbose

  # Full workflow with all options
  python unified_ingest_complete.py --documents documents --onyx-mode new --clear --verbose
        """
    )
    
    parser.add_argument(
        "--documents",
        type=str,
        default="documents",
        help="Path to documents folder (default: documents)"
    )
    
    parser.add_argument(
        "--onyx-mode",
        choices=["existing", "new", "skip"],
        default="existing",
        help="Onyx ingestion mode: 'existing' uses CC-pair 285 (faster), 'new' creates fresh connector (isolated), 'skip' skips Onyx entirely (when already indexed)"
    )
    
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data in Graphiti + pgvector before ingesting (Onyx Cloud is never modified)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging for detailed progress tracking"
    )
    
    args = parser.parse_args()
    
    # Print startup banner
    print("🚀 UNIFIED TRIPLE INGESTION PIPELINE")
    print("=" * 40)
    print("📊 Systems: Onyx Cloud + Graphiti + pgvector")
    print(f"📁 Documents: {args.documents}")
    print(f"🔮 Onyx mode: {args.onyx_mode}")
    print(f"🧹 Clear local: {args.clear}")
    print(f"📝 Verbose: {args.verbose}")
    print("=" * 40)
    
    # Run the ingestion pipeline
    async def run_pipeline():
        pipeline = UnifiedTripleIngestionPipeline(
            documents_folder=args.documents,
            onyx_mode=args.onyx_mode,
            clear_local_data=args.clear,
            verbose=args.verbose
        )
        
        success = await pipeline.run_complete_ingestion()
        
        if success:
            print(f"\n✅ Pipeline completed successfully!")
            return 0
        else:
            print(f"\n❌ Pipeline completed with errors!")
            return 1
    
    # Run async pipeline
    try:
        exit_code = asyncio.run(run_pipeline())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
