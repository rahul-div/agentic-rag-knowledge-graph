#!/usr/bin/env python3
"""
Onyx Test Document Cleanup Utility

This utility helps identify and manage test documents in Onyx Cloud.
It can list test documents and provide information for manual cleanup.

Usage:
    python cleanup_onyx_tests.py --list
    python cleanup_onyx_tests.py --info
"""

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def list_test_patterns():
    """List the patterns used for test documents."""
    print("🔍 Test Document Identification Patterns")
    print("=" * 50)
    print("")
    print("Test documents created by this system can be identified by:")
    print("")
    print("📄 DOCUMENT TITLES:")
    print("   • Contains: '[TEST-SAFE-TO-DELETE]'")
    print("   • Format: '[TEST-SAFE-TO-DELETE] Onyx Integration Test [timestamp]'")
    print("")
    print("🆔 DOCUMENT IDs:")
    print("   • Start with: 'TEST_SAFE_TO_DELETE_'")
    print("   • Format: 'TEST_SAFE_TO_DELETE_[timestamp]'")
    print("")
    print("🏷️  METADATA TAGS:")
    print("   • test_document: true")
    print("   • safe_to_delete: true")
    print("   • created_by: hybrid_rag_test_suite")
    print("   • purpose: api_integration_test")
    print("   • warning: THIS_IS_A_TEST_DOCUMENT")
    print("")
    print("📅 CREATED TIMESTAMPS:")
    print("   • All test documents include creation timestamps")
    print("   • Format: ISO 8601 (e.g., 2025-08-11T14:30:00.123456)")


def cleanup_instructions():
    """Provide cleanup instructions for Onyx Cloud UI."""
    print("🗑️  Manual Cleanup Instructions for Onyx Cloud UI")
    print("=" * 55)
    print("")
    print("To clean up test documents in your Onyx Cloud interface:")
    print("")
    print("1. 🔐 LOG INTO ONYX CLOUD")
    print("   • Go to your Onyx Cloud URL")
    print("   • Log in with your credentials")
    print("")
    print("2. 📋 ACCESS DOCUMENT MANAGEMENT")
    print("   • Navigate to the Documents or Admin section")
    print("   • Look for document listing/management interface")
    print("")
    print("3. 🔍 IDENTIFY TEST DOCUMENTS")
    print("   • Search for titles containing '[TEST-SAFE-TO-DELETE]'")
    print("   • Filter by tags: 'test_document' or 'safe_to_delete'")
    print("   • Look for document IDs starting with 'TEST_SAFE_TO_DELETE_'")
    print("")
    print("4. ✅ VERIFY BEFORE DELETION")
    print("   • Double-check the document contains test content")
    print("   • Verify it has the warning: 'THIS IS A TEST DOCUMENT'")
    print("   • Confirm metadata shows 'safe_to_delete: true'")
    print("")
    print("5. 🗑️  DELETE TEST DOCUMENTS")
    print("   • Select the identified test documents")
    print("   • Use the delete/remove function in the UI")
    print("   • Confirm deletion when prompted")
    print("")
    print("⚠️  SAFETY REMINDERS:")
    print("   • Only delete documents clearly marked as test documents")
    print("   • Never delete documents without the test patterns")
    print("   • When in doubt, don't delete - ask for help")
    print("")
    print("🔄 AUTOMATIC PREVENTION:")
    print("   • All test documents are clearly labeled")
    print("   • Multiple identification methods are used")
    print("   • Timestamps help identify recent test runs")


def show_info():
    """Show general information about the test system."""
    print("ℹ️  Onyx Cloud Test System Information")
    print("=" * 45)
    print("")
    print("📋 ABOUT THE TEST SYSTEM:")
    print("   The hybrid RAG system includes safe testing capabilities")
    print("   for verifying Onyx Cloud integration without affecting")
    print("   production data.")
    print("")
    print("🛡️  SAFETY FEATURES:")
    print("   • Test documents are clearly labeled and marked")
    print("   • Multiple identification patterns prevent confusion")
    print("   • No production data is ever used in tests")
    print("   • All test content is harmless and generic")
    print("")
    print("🧪 WHAT TESTS CREATE:")
    print("   • Sample documents with test content")
    print("   • Clear identification in titles and metadata")
    print("   • Timestamps for tracking test runs")
    print("   • No sensitive or production information")
    print("")
    print("🔄 BEST PRACTICES:")
    print("   • Run tests in isolation")
    print("   • Clean up test documents after validation")
    print("   • Monitor for any unexpected behavior")
    print("   • Keep production and test environments separate")


def main():
    """Main function for the cleanup utility."""
    parser = argparse.ArgumentParser(
        description="Onyx Test Document Cleanup Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup_onyx_tests.py --list     # Show test document patterns
  python cleanup_onyx_tests.py --info     # Show system information
        """
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List test document identification patterns'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show general information about the test system'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Show cleanup instructions for Onyx Cloud UI'
    )
    
    args = parser.parse_args()
    
    if not any([args.list, args.info, args.cleanup]):
        # Default action if no arguments provided
        parser.print_help()
        print()
        print("Choose an option to get started:")
        print("  --list     See how to identify test documents")
        print("  --info     Learn about the test system")
        print("  --cleanup  Get cleanup instructions")
        return
    
    if args.list:
        list_test_patterns()
        print()
    
    if args.info:
        show_info()
        print()
    
    if args.cleanup:
        cleanup_instructions()
        print()


if __name__ == "__main__":
    main()
