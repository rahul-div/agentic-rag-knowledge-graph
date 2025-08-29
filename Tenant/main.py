"""
Multi-Tenant RAG System - Main Application Entry Point
"""

import os
import logging
import uvicorn
from typing import Optional

# Import our multi-tenant components
from .multi_tenant_api import create_app


# Configuration class
class Config:
    """Configuration management for the multi-tenant RAG system."""

    # Database
    NEON_CONNECTION_STRING: Optional[str] = os.getenv("NEON_CONNECTION_STRING")

    # Neo4j
    NEO4J_URI: Optional[str] = os.getenv("NEO4J_URI")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: Optional[str] = os.getenv("NEO4J_PASSWORD")

    # JWT
    JWT_SECRET_KEY: Optional[str] = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Application
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration variables."""
        required_vars = [
            ("NEON_CONNECTION_STRING", cls.NEON_CONNECTION_STRING),
            ("NEO4J_URI", cls.NEO4J_URI),
            ("NEO4J_PASSWORD", cls.NEO4J_PASSWORD),
            ("JWT_SECRET_KEY", cls.JWT_SECRET_KEY),
        ]

        missing = [var_name for var_name, var_value in required_vars if not var_value]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")

        # Additional validation
        if cls.APP_ENV not in ["development", "staging", "production"]:
            raise ValueError(
                f"Invalid APP_ENV: {cls.APP_ENV}. Must be development, staging, or production"
            )


def setup_logging(log_level: str = "info") -> None:
    """Configure application logging."""
    level = getattr(logging, log_level.upper())

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("multi_tenant_rag.log", mode="a"),
        ],
    )

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("fastapi").setLevel(level)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)  # Reduce database noise


def create_application():
    """Create and configure the FastAPI application."""
    # Setup logging first
    setup_logging(Config.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")

        # Create the FastAPI application
        app = create_app(
            neon_connection_string=Config.NEON_CONNECTION_STRING,
            neo4j_uri=Config.NEO4J_URI,
            neo4j_user=Config.NEO4J_USER,
            neo4j_password=Config.NEO4J_PASSWORD,
            jwt_secret_key=Config.JWT_SECRET_KEY,
            title="Multi-Tenant RAG API",
            version="1.0.0",
        )

        logger.info("Multi-tenant RAG application created successfully")
        logger.info(f"Environment: {Config.APP_ENV}")
        logger.info(f"Host: {Config.APP_HOST}:{Config.APP_PORT}")

        return app

    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise


# Create the application instance
app = create_application()


def main():
    """Main entry point for running the application."""
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting Multi-Tenant RAG System")

        # Run the application
        uvicorn.run(
            "main:app",
            host=Config.APP_HOST,
            port=Config.APP_PORT,
            reload=(Config.APP_ENV == "development"),
            log_level=Config.LOG_LEVEL.lower(),
            access_log=True,
            server_header=False,  # Security: hide server info
            date_header=False,  # Security: hide date header
        )

    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        raise


if __name__ == "__main__":
    main()
