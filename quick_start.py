#!/usr/bin/env python3
"""
Quick start guide for the Hybrid Agentic RAG Knowledge Graph System.

This script provides a comprehensive status check and next steps for getting
the hybrid RAG system running with Onyx Cloud + Graphiti integration.
"""

import os
from dotenv import load_dotenv


def check_api_keys():
    """Check status of all required API keys."""
    status = {}

    # Google Gemini API (Required)
    google_api_key = os.getenv("GOOGLE_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    api_key = google_api_key or gemini_api_key

    if api_key and api_key not in [
        "your-google-api-key-here",
        "your-gemini-api-key-here",
    ]:
        status["gemini"] = f"✅ Configured (starts with {api_key[:10]}...)"
    else:
        status["gemini"] = "❌ Not configured"

    # Onyx Cloud API (Optional but recommended)
    onyx_api_key = os.getenv("ONYX_API_KEY")
    if onyx_api_key and onyx_api_key != "your_onyx_api_key_here":
        status["onyx"] = f"✅ Configured (starts with {onyx_api_key[:10]}...)"
    else:
        status["onyx"] = "❌ Not configured (enterprise features disabled)"

    return status


def check_database_config():
    """Check database configuration status."""
    database_url = os.getenv("DATABASE_URL")
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    db_status = {}
    if database_url and database_url != "your_database_url_here":
        db_status["postgresql"] = "✅ Configured"
    else:
        db_status["postgresql"] = "❌ Not configured"

    # Check Neo4j configuration
    if neo4j_uri and neo4j_uri != "bolt://localhost:7687":
        db_status["neo4j"] = f"✅ Configured ({neo4j_uri})"
    elif neo4j_user and neo4j_password:
        db_status["neo4j"] = "✅ Using default URI with custom credentials"
    else:
        db_status["neo4j"] = "⚠️  Using defaults (bolt://localhost:7687, neo4j/neo4j)"

    return db_status


def main():
    print("🤖 Hybrid Agentic RAG Knowledge Graph System")
    print("=" * 55)
    print("🔍 Onyx Cloud + 🧠 Graphiti Vector + 🕸️ Knowledge Graph")
    print()

    # Load environment variables
    load_dotenv()

    # Check API keys
    api_status = check_api_keys()
    db_status = check_database_config()

    print("📋 System Status:")
    print("-" * 25)

    print("🔑 API Keys:")
    print(f"   • Google Gemini: {api_status['gemini']}")
    print(f"   • Onyx Cloud:    {api_status['onyx']}")
    print()

    print("🗄️ Databases:")
    print(f"   • PostgreSQL:    {db_status['postgresql']}")
    print(f"   • Neo4j:         {db_status['neo4j']}")
    print()

    # Determine system readiness
    gemini_ready = "✅" in api_status["gemini"]
    postgresql_ready = "✅" in db_status["postgresql"]
    neo4j_ready = "✅" in db_status["neo4j"] or "⚠️" in db_status["neo4j"]
    basic_db_ready = postgresql_ready or neo4j_ready

    if gemini_ready and basic_db_ready:
        print("🎯 System Status: READY TO LAUNCH!")
        print("-" * 35)
        print()
        print("🚀 Quick Start Commands:")
        print("   1. Ingest documents:")
        print("      python -m ingestion.ingest")
        print()
        print("   2. Start the system (2 terminals needed):")
        print("      Terminal 1: ./start_api.sh")
        print("      Terminal 2: ./start_cli.sh")
        print()
        print("   3. Or start manually:")
        print("      Terminal 1: python comprehensive_agent_api.py")
        print("      Terminal 2: python comprehensive_agent_cli.py")
        print()

        onyx_ready = "✅" in api_status["onyx"]
        if onyx_ready:
            print("🏢 Enterprise Features: ENABLED")
            print("   • Onyx Cloud document search")
            print("   • Citation-based QA")
            print("   • Advanced enterprise search")
        else:
            print("🏠 Local Mode: Graphiti Only")
            print("   • Vector similarity search")
            print("   • Knowledge graph queries")
            print("   • Hybrid search capabilities")
        print()

    else:
        print("🔧 Setup Required:")
        print("-" * 20)

        if not gemini_ready:
            print("   1. 🔑 Configure Google Gemini API:")
            print("      • Get key: https://aistudio.google.com/")
            print("      • Set GOOGLE_API_KEY or GEMINI_API_KEY in .env")
            print("      • Example: GOOGLE_API_KEY=your_actual_api_key_here")
            print()

        if not basic_db_ready:
            print("   2. 🗄️ Configure Databases:")
            print("      PostgreSQL (for Graphiti Vector):")
            print("        • Set DATABASE_URL in .env")
            print(
                "        • Example: DATABASE_URL=postgresql://user:pass@localhost/dbname"
            )
            print("      Neo4j (for Knowledge Graph):")
            print("        • Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env")
            print("        • Example: NEO4J_URI=bolt://localhost:7687")
            print("        • See README.md for detailed setup")
            print()

        print("   3. 📄 Prepare Documents:")
        print("      • Add documents to documents/ folder")
        print("      • Supported: .md, .txt files")
        print()

    # Show current project architecture
    print("🏗️ System Architecture:")
    print("-" * 25)
    print("   🤖 Agent System:")
    print("      • comprehensive_agent_api.py  - FastAPI backend")
    print("      • comprehensive_agent_cli.py  - Interactive CLI")
    print("      • agent/agent.py              - Main Pydantic AI agent")
    print("      • agent/tools.py              - 10 specialized search tools")
    print()
    print("   🔍 Search Systems:")
    print("      • Onyx Cloud                  - Enterprise document search")
    print("      • Graphiti Vector             - Semantic similarity (768-dim)")
    print("      • Graphiti Knowledge Graph    - Temporal relationships")
    print()
    print("   📄 Data Pipeline:")
    print("      • ingestion/ingest.py         - Document processing pipeline")
    print("      • ingestion/chunker.py        - Semantic chunking")
    print("      • ingestion/embedder.py       - Gemini embeddings")
    print("      • ingestion/graph_builder.py  - Knowledge graph construction")
    print()

    print("🛠️ Development Tools:")
    print("-" * 25)
    print("   • start_api.sh                  - Automated API startup")
    print("   • start_cli.sh                  - Automated CLI startup")
    print("   • quick_start.py (this file)    - System status check")
    print("   • comprehensive_agent_api.py    - Direct API startup")
    print("   • comprehensive_agent_cli.py    - Direct CLI startup")
    print()

    print("📚 Documentation:")
    print("-" * 25)
    print("   • README.md                     - Comprehensive system guide")
    print("   • Implementation/               - Technical documentation")
    print("   • sql/schema.sql                - Database schema")
    print()

    print("🎮 Usage Examples:")
    print("-" * 25)
    print("   CLI Commands:")
    print("      /help     - Show all commands")
    print("      /health   - Check system status")
    print("      /status   - Session information")
    print("      /clear    - Clear conversation history")
    print("      /quit     - Exit gracefully")
    print()
    print("   Query Examples:")
    print("      'What documents are available in the system?'")
    print("      'Show me the timeline of recent decisions'")
    print("      'How do these systems integrate together?'")
    print("      'Find documents about [specific topic]'")
    print()

    print("🔗 Next Steps:")
    print("-" * 15)
    if gemini_ready and basic_db_ready:
        print("   1. Run document ingestion: python -m ingestion.ingest")
        print("   2. Start the API server:    ./start_api.sh")
        print("   3. Launch the CLI client:   ./start_cli.sh")
        print("   4. Try example queries and explore the system!")
    else:
        print("   1. Complete setup steps above")
        print("   2. Run: python quick_start.py (this script) to recheck")
        print("   3. See README.md for detailed instructions")
    print()


if __name__ == "__main__":
    main()
