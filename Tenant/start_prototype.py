#!/usr/bin/env python3
"""
Multi-Tenant RAG Prototype Startup Script
Simplified startup for rapid prototype testing and validation.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the Tenant directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def check_dependencies():
    """Check if all required dependencies are available."""
    try:
        # Test core imports
        import importlib.util

        deps = [
            ("fastapi", "FastAPI"),
            ("uvicorn", "Uvicorn"),
            ("httpx", "HTTP client"),
            ("asyncpg", "PostgreSQL driver"),
            ("neo4j", "Neo4j driver"),
        ]

        for dep, desc in deps:
            if importlib.util.find_spec(dep) is None:
                logger.error(f"❌ Missing {desc}: {dep}")
                return False

        logger.info("✅ Core dependencies available")

        # Test AI dependencies
        if importlib.util.find_spec("google.generativeai") is None:
            logger.error("❌ Missing Google AI")
            return False
        logger.info("✅ Google AI dependencies available")

        # Test environment
        from dotenv import load_dotenv

        load_dotenv()

        required_env_vars = [
            "GOOGLE_API_KEY",
            "NEO4J_URI",
            "NEO4J_USER",
            "NEO4J_PASSWORD",
            "CATALOG_DATABASE_URL",
        ]

        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.warning(f"⚠️  Missing environment variables: {missing_vars}")
            logger.warning("Using mock values for prototype testing")
        else:
            logger.info("✅ Environment variables configured")

        return True

    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        return False


async def start_prototype_api():
    """Start the prototype API server."""
    try:
        if not await check_dependencies():
            logger.error("Dependency check failed. Please install required packages.")
            return False

        # Import and start the API
        from prototype_api import create_app

        logger.info("🚀 Starting Multi-Tenant RAG Prototype API...")

        # Create the FastAPI app
        app = create_app()

        # Start the server
        import uvicorn

        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False,  # Disable reload for production testing
        )

        server = uvicorn.Server(config)
        logger.info("🌟 Prototype API server starting on http://0.0.0.0:8000")
        logger.info("📊 Health check: http://0.0.0.0:8000/health")
        logger.info("📚 API docs: http://0.0.0.0:8000/docs")

        await server.serve()

    except Exception as e:
        logger.error(f"❌ Failed to start prototype API: {e}")
        raise


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                Multi-Tenant RAG Prototype                    ║
    ║           Testing 3-4 Tenant Architecture                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    try:
        asyncio.run(start_prototype_api())
    except KeyboardInterrupt:
        logger.info("🛑 Prototype API shutdown requested")
    except Exception as e:
        logger.error(f"❌ Prototype startup failed: {e}")
        sys.exit(1)
