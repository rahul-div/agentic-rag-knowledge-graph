#!/usr/bin/env python3
"""
Quick start guide for the Agentic RAG Knowledge Graph with Gemini API.

This script provides a summary of the setup status and next steps.
"""

import os
from dotenv import load_dotenv


def main():
    print("🚀 Agentic RAG Knowledge Graph - Gemini Edition")
    print("=" * 55)
    print()

    # Load environment variables
    load_dotenv()

    # Check API key status
    google_api_key = os.getenv("GOOGLE_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    api_key = google_api_key or gemini_api_key

    print("📋 Current Status:")
    print("-" * 20)

    if api_key and api_key not in [
        "your-google-api-key-here",
        "your-gemini-api-key-here",
    ]:
        print(f"✅ API Key: Configured (starts with {api_key[:10]}...)")
        print("✅ Environment: Ready")
        print()
        print("🎯 Ready to run! Try these commands:")
        print("   • python3 ingestion/ingest.py")
        print("   • python3 validate_env.py")
        print()
    else:
        print("❌ API Key: Not configured")
        print("❌ Environment: Needs setup")
        print()
        print("🔧 Setup Required:")
        print("   1. Get your Gemini API key from: https://aistudio.google.com/")
        print("   2. Run the setup script: python3 setup_api_keys.py")
        print("   3. Or manually edit .env file with your API key")
        print()
        print(
            "💡 The .env file currently has placeholder values that need to be replaced."
        )
        print()

    # Show file structure
    print("📁 Project Structure:")
    print("-" * 20)
    print("   • ingestion/ingest.py    - Main ingestion pipeline")
    print("   • ingestion/chunker.py   - Text chunking (Gemini-optimized)")
    print("   • ingestion/embedder.py  - Embedding generation")
    print("   • ingestion/graph_builder.py - Knowledge graph construction")
    print("   • setup_api_keys.py      - Interactive API key setup")
    print("   • validate_env.py        - Environment validation")
    print("   • .env                   - Configuration file")
    print()

    print("📚 Documentation:")
    print("-" * 20)
    print("   • README.md              - Project overview")
    print("   • CLAUDE.md              - Claude integration notes")
    print("   • PLANNING.md            - Development planning")
    print("   • TASK.md                - Current task details")
    print()


if __name__ == "__main__":
    main()
