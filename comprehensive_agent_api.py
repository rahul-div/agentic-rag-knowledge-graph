#!/usr/bin/env python3
"""
Comprehensive Hybrid RAG Agent API Server

FastAPI backend for the hybrid agentic RAG system combining:
- 🏢 Onyx Cloud enterprise search
- 🔍 Graphiti vector similarity search
- 🕸️ Graphiti knowledge graph search

Features:
- Intelligent tool selection based on query complexity
- Real-time streaming responses
- Detailed logging for development/debugging
- Session management for conversation continuity
- Health monitoring for all three systems

Usage:
    python comprehensive_agent_api.py

Then connect via CLI:
    python comprehensive_agent_cli.py
"""

import os
import json
import logging
import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

# Import agent components
from agent.agent import create_hybrid_rag_agent, AgentDependencies
from agent.db_utils import initialize_database, close_database, test_connection
from agent.graph_utils import initialize_graph, close_graph, test_graph_connection

# Load environment variables
load_dotenv()

# Configure comprehensive logging for development visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output for terminal visibility
        logging.FileHandler("comprehensive_agent_api.log"),  # File logging
    ],
)
logger = logging.getLogger(__name__)

# Application configuration
APP_ENV = os.getenv("APP_ENV", "development")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8058))  # Different port to avoid conflicts

# Set debug logging for development
if APP_ENV == "development":
    logger.setLevel(logging.DEBUG)
    # Enable debug for agent components
    logging.getLogger("agent").setLevel(logging.DEBUG)
    logging.getLogger("onyx").setLevel(logging.DEBUG)


# Pydantic models for API
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(
        None, description="Session ID for conversation continuity"
    )
    user_id: str = Field(default="api_user", description="User identifier")
    search_type: str = Field(default="hybrid", description="Search type preference")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID")
    tools_used: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tools called by agent"
    )
    total_sources: int = Field(default=0, description="Total sources found")
    systems_used: List[str] = Field(
        default_factory=list, description="Systems that provided results"
    )
    confidence: str = Field(default="medium", description="Response confidence level")
    response_time: float = Field(..., description="Response time in seconds")


class HealthStatus(BaseModel):
    """Health status model."""

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Health check timestamp"
    )
    systems: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Individual system status"
    )
    agent_ready: bool = Field(default=False, description="Whether agent is ready")


class StreamDelta(BaseModel):
    """Streaming response delta."""

    type: str = Field(..., description="Delta type (text, tool_call, etc.)")
    content: str = Field(default="", description="Content for this delta")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


# Global agent instance
global_agent = None
global_dependencies = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global global_agent, global_dependencies

    logger.info("🚀 Starting Comprehensive Hybrid RAG Agent API Server")
    logger.info("=" * 60)

    try:
        # Initialize databases
        logger.info("📊 Initializing databases...")
        await initialize_database()
        await initialize_graph()

        # Test database connections
        logger.info("🔍 Testing database connections...")
        db_status = await test_connection()
        graph_status = await test_graph_connection()

        if not db_status:
            logger.warning(
                "⚠️ PostgreSQL connection failed - some features may be limited"
            )
        if not graph_status:
            logger.warning(
                "⚠️ Neo4j connection failed - graph search will be unavailable"
            )

        # Initialize hybrid agent with all systems
        logger.info("🤖 Initializing Hybrid RAG Agent...")
        session_id = f"api_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            global_agent, global_dependencies = await create_hybrid_rag_agent(
                session_id=session_id,
                cc_pair_id=285,  # Validated CC-pair
                enable_onyx=True,
            )

            # Log final system status
            systems_enabled = []
            if global_dependencies.search_preferences.get("use_onyx"):
                systems_enabled.append("🏢 Onyx Cloud")
            if global_dependencies.search_preferences.get("use_vector"):
                systems_enabled.append("🔍 Graphiti Vector")
            if global_dependencies.search_preferences.get("use_graph"):
                systems_enabled.append("🕸️ Knowledge Graph")

            logger.info("✅ Hybrid RAG Agent initialized successfully!")
            logger.info(f"🎯 Active systems: {', '.join(systems_enabled)}")
            logger.info(f"📍 Session ID: {session_id}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize agent: {e}")
            # Create minimal agent for testing
            global_dependencies = AgentDependencies(session_id=session_id)
            global_dependencies.search_preferences = {
                "use_onyx": False,
                "use_vector": True,
                "use_graph": True,
            }
            logger.warning("⚠️ Running in limited mode (Graphiti only)")

        logger.info("=" * 60)
        logger.info(f"🌐 API Server ready at http://{APP_HOST}:{APP_PORT}")
        logger.info("📡 Connect via CLI: python comprehensive_agent_cli.py")
        logger.info("=" * 60)

        yield  # Server is running

    finally:
        # Cleanup
        logger.info("🔄 Shutting down Comprehensive Hybrid RAG Agent API")
        await close_database()
        await close_graph()
        logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Comprehensive Hybrid RAG Agent API",
    description="AI agent combining Onyx Cloud, vector search, and knowledge graph for intelligent information retrieval",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Helper functions
async def execute_agent_with_logging(
    message: str, session_id: str, user_id: str = "api_user"
) -> tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Execute agent with comprehensive logging.

    Returns:
        Tuple of (response, tools_used, metadata)
    """
    global global_agent, global_dependencies

    if not global_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    start_time = datetime.now()
    logger.info(f"🔍 Processing query from user {user_id}")
    logger.info(f"📝 Query: {message}")
    logger.info(f"🆔 Session: {session_id}")

    try:
        # Update session ID in dependencies
        global_dependencies.session_id = session_id

        # Execute agent
        logger.info("🤖 Executing hybrid RAG agent...")
        result = await global_agent.run(message, deps=global_dependencies)

        response_time = (datetime.now() - start_time).total_seconds()

        # Extract tools used and metadata
        tools_used = []
        metadata = {
            "response_time": response_time,
            "session_id": session_id,
            "systems_used": [],
            "total_sources": 0,
            "confidence": "medium",
        }

        # Try to extract tool information from result
        try:
            if hasattr(result, "all_messages"):
                for message_obj in result.all_messages():
                    if hasattr(message_obj, "parts"):
                        for part in message_obj.parts:
                            if hasattr(part, "tool_name"):
                                tools_used.append(
                                    {
                                        "tool_name": part.tool_name,
                                        "args": getattr(part, "args", {}),
                                        "result_summary": str(
                                            getattr(part, "content", "")
                                        )[:200],
                                    }
                                )
        except Exception as e:
            logger.debug(f"Could not extract tool information: {e}")

        response_text = str(result.data) if hasattr(result, "data") else str(result)

        # Log successful completion
        logger.info(f"✅ Query processed successfully in {response_time:.2f}s")
        logger.info(f"🛠️ Tools used: {len(tools_used)}")
        logger.info(f"📊 Response length: {len(response_text)} characters")

        return response_text, tools_used, metadata

    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Agent execution failed after {response_time:.2f}s: {e}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


def extract_metadata_from_response(
    response: str, tools_used: List[Dict]
) -> Dict[str, Any]:
    """Extract metadata from agent response and tools."""
    metadata = {"systems_used": [], "total_sources": 0, "confidence": "medium"}

    # Analyze tools used to determine systems
    for tool in tools_used:
        tool_name = tool.get("tool_name", "")
        if "onyx" in tool_name.lower():
            if "Onyx Cloud" not in metadata["systems_used"]:
                metadata["systems_used"].append("Onyx Cloud")
        elif "vector" in tool_name.lower():
            if "Graphiti Vector" not in metadata["systems_used"]:
                metadata["systems_used"].append("Graphiti Vector")
        elif "graph" in tool_name.lower():
            if "Knowledge Graph" not in metadata["systems_used"]:
                metadata["systems_used"].append("Knowledge Graph")
        elif "comprehensive" in tool_name.lower():
            # Comprehensive search uses multiple systems
            for system in ["Onyx Cloud", "Graphiti Vector", "Knowledge Graph"]:
                if system not in metadata["systems_used"]:
                    metadata["systems_used"].append(system)

    # Estimate confidence based on systems used and response length
    num_systems = len(metadata["systems_used"])
    response_length = len(response)

    if num_systems >= 2 and response_length > 200:
        metadata["confidence"] = "high"
    elif num_systems >= 1 and response_length > 100:
        metadata["confidence"] = "medium"
    else:
        metadata["confidence"] = "low"

    return metadata


# API Endpoints
@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Comprehensive health check for all systems."""
    logger.info("🏥 Health check requested")

    systems = {}
    overall_status = "healthy"
    agent_ready = global_agent is not None

    # Check database connections
    try:
        db_status = await test_connection()
        systems["postgresql"] = {
            "status": "healthy" if db_status else "unhealthy",
            "description": "Vector database for document chunks",
        }
        if not db_status:
            overall_status = "degraded"
    except Exception as e:
        systems["postgresql"] = {"status": "error", "description": f"Error: {str(e)}"}
        overall_status = "degraded"

    # Check Neo4j
    try:
        graph_status = await test_graph_connection()
        systems["neo4j"] = {
            "status": "healthy" if graph_status else "unhealthy",
            "description": "Knowledge graph database",
        }
        if not graph_status:
            overall_status = "degraded"
    except Exception as e:
        systems["neo4j"] = {"status": "error", "description": f"Error: {str(e)}"}
        overall_status = "degraded"

    # Check Onyx integration
    if global_dependencies and global_dependencies.search_preferences.get("use_onyx"):
        systems["onyx_cloud"] = {
            "status": "healthy",
            "description": f"Document set: {global_dependencies.onyx_document_set_id}",
        }
    else:
        systems["onyx_cloud"] = {
            "status": "disabled",
            "description": "Onyx integration not available",
        }

    # Check agent status
    systems["hybrid_agent"] = {
        "status": "healthy" if agent_ready else "initializing",
        "description": "Hybrid RAG agent with tool selection",
    }

    if not agent_ready:
        overall_status = "initializing"

    logger.info(f"🏥 Health check complete: {overall_status}")

    return HealthStatus(status=overall_status, systems=systems, agent_ready=agent_ready)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint for the hybrid RAG agent."""
    start_time = datetime.now()

    # Generate session ID if not provided
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"

    logger.info("=" * 60)
    logger.info("🔄 NEW CHAT REQUEST")
    logger.info("=" * 60)

    try:
        # Execute agent
        response, tools_used, base_metadata = await execute_agent_with_logging(
            message=request.message, session_id=session_id, user_id=request.user_id
        )

        # Extract additional metadata
        metadata = extract_metadata_from_response(response, tools_used)
        response_time = (datetime.now() - start_time).total_seconds()

        result = ChatResponse(
            response=response,
            session_id=session_id,
            tools_used=tools_used,
            total_sources=metadata.get("total_sources", 0),
            systems_used=metadata.get("systems_used", []),
            confidence=metadata.get("confidence", "medium"),
            response_time=response_time,
        )

        logger.info("=" * 60)
        logger.info("✅ CHAT REQUEST COMPLETED")
        logger.info(f"📊 Systems used: {metadata.get('systems_used', [])}")
        logger.info(f"⏱️ Total time: {response_time:.2f}s")
        logger.info("=" * 60)

        return result

    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        logger.error("=" * 60)
        logger.error("❌ CHAT REQUEST FAILED")
        logger.error(f"⏱️ Failed after: {response_time:.2f}s")
        logger.error(f"🚨 Error: {str(e)}")
        logger.error("=" * 60)
        raise e


@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """Streaming chat endpoint for real-time responses."""
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"

    logger.info("🌊 Starting streaming chat session")
    logger.info(f"📝 Query: {request.message}")

    async def generate_stream():
        """Generate streaming response."""
        try:
            # Send initial status
            yield f"data: {json.dumps(StreamDelta(type='status', content='Processing query...').dict())}\n\n"

            # Execute agent
            response, tools_used, metadata = await execute_agent_with_logging(
                message=request.message, session_id=session_id, user_id=request.user_id
            )

            # Send tools information
            if tools_used:
                yield f"data: {json.dumps(StreamDelta(type='tools', content=f'Used {len(tools_used)} tools', metadata={'tools': tools_used}).dict())}\n\n"

            # Stream response in chunks
            chunk_size = 50
            for i in range(0, len(response), chunk_size):
                chunk = response[i : i + chunk_size]
                yield f"data: {json.dumps(StreamDelta(type='text', content=chunk).dict())}\n\n"
                await asyncio.sleep(0.1)  # Small delay for streaming effect

            # Send completion signal
            completion_metadata = extract_metadata_from_response(response, tools_used)
            yield f"data: {json.dumps(StreamDelta(type='complete', content='', metadata=completion_metadata).dict())}\n\n"

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            yield f"data: {json.dumps(StreamDelta(type='error', content=error_msg).dict())}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/systems/status")
async def get_systems_status():
    """Get detailed status of all integrated systems."""
    logger.info("📊 Systems status requested")

    status = {
        "timestamp": datetime.now().isoformat(),
        "agent_session": global_dependencies.session_id
        if global_dependencies
        else None,
        "systems": {},
    }

    if global_dependencies:
        prefs = global_dependencies.search_preferences

        status["systems"]["onyx_cloud"] = {
            "enabled": prefs.get("use_onyx", False),
            "document_set_id": global_dependencies.onyx_document_set_id,
            "status": "ready" if prefs.get("use_onyx") else "disabled",
        }

        status["systems"]["graphiti_vector"] = {
            "enabled": prefs.get("use_vector", False),
            "status": "ready" if prefs.get("use_vector") else "disabled",
        }

        status["systems"]["knowledge_graph"] = {
            "enabled": prefs.get("use_graph", False),
            "status": "ready" if prefs.get("use_graph") else "disabled",
        }

    return status


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with detailed logging."""
    logger.error(
        f"🚨 Unhandled exception in {request.method} {request.url}: {str(exc)}"
    )
    logger.error(f"🚨 Exception type: {type(exc).__name__}")

    return HTTPException(
        status_code=500,
        detail={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__,
        },
    )


# Development server
if __name__ == "__main__":
    print("🚀 Starting Comprehensive Hybrid RAG Agent API Server")
    print("=" * 60)
    print(f"📍 Host: {APP_HOST}")
    print(f"🔗 Port: {APP_PORT}")
    print(f"🌐 URL: http://{APP_HOST}:{APP_PORT}")
    print("📡 Connect via CLI: python comprehensive_agent_cli.py")
    print("=" * 60)

    uvicorn.run(
        "comprehensive_agent_api:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True if APP_ENV == "development" else False,
        log_level="info",
    )
