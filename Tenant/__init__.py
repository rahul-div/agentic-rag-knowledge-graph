"""
Multi-Tenant RAG System

A production-ready, multi-tenant Retrieval-Augmented Generation (RAG) system
with complete data isolation using Neon PostgreSQL + pgvector and Neo4j + Graphiti.

Key Features:
- Complete tenant isolation using Row-Level Security (RLS)
- Vector search with pgvector
- Knowledge graph capabilities with Graphiti
- JWT-based authentication and authorization
- FastAPI REST API with comprehensive endpoints
- Pydantic AI agent with tenant-aware tools
- Industry-standard security and scalability patterns

Components:
- tenant_manager: Database operations with tenant isolation
- multi_tenant_graphiti: Graph operations with namespace isolation
- multi_tenant_agent: AI agent with tenant-aware tools
- multi_tenant_api: FastAPI application with authentication
- auth_middleware: JWT authentication and security middleware
"""

__version__ = "1.0.0"
__author__ = "Multi-Tenant RAG Team"
__license__ = "MIT"

# Core components
from .tenant_manager import TenantManager, Tenant, Document, Chunk
from .multi_tenant_graphiti import (
    TenantGraphitiClient,
    GraphEpisode,
    GraphEntity,
    GraphRelationship,
)
from .multi_tenant_agent import MultiTenantRAGAgent, TenantContext, RAGResult
from .auth_middleware import JWTManager, TenantAuth, TenantSecurityManager

# API application
from .multi_tenant_api import create_app

# Main application
from .main import app, Config

__all__ = [
    # Core classes
    "TenantManager",
    "Tenant",
    "Document",
    "Chunk",
    "TenantGraphitiClient",
    "GraphEpisode",
    "GraphEntity",
    "GraphRelationship",
    "MultiTenantRAGAgent",
    "TenantContext",
    "RAGResult",
    # Authentication
    "JWTManager",
    "TenantAuth",
    "TenantSecurityManager",
    # Application
    "create_app",
    "app",
    "Config",
    # Version info
    "__version__",
    "__author__",
    "__license__",
]


def get_version():
    """Get the current version of the multi-tenant RAG system."""
    return __version__


def get_info():
    """Get system information."""
    return {
        "name": "Multi-Tenant RAG System",
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "description": "Production-ready multi-tenant RAG with complete data isolation",
        "components": [
            "Neon PostgreSQL with pgvector",
            "Neo4j with Graphiti",
            "FastAPI with JWT auth",
            "Pydantic AI agent",
            "Row-Level Security (RLS)",
            "Namespace isolation",
        ],
    }
