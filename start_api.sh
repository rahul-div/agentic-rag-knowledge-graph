#!/bin/bash

# 🚀 Start API Server Script
# Automatically activates virtual environment and starts the FastAPI server

set -e  # Exit on any error

echo "🚀 Starting Hybrid RAG Agent API Server..."

# Check if we're in the correct directory
if [ ! -f "comprehensive_agent_api.py" ]; then
    echo "❌ Error: comprehensive_agent_api.py not found"
    echo "Please run this script from the project root directory:"
    echo "cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment (.venv) not found"
    echo "Please create a virtual environment first:"
    echo "python -m venv .venv"
    echo "source .venv/bin/activate"
    echo "pip install -r requirements_final.txt"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Verify Python is using the virtual environment
PYTHON_PATH=$(which python)
echo "✅ Using Python: $PYTHON_PATH"

# Check if required dependencies are installed
echo "🔍 Checking dependencies..."
if ! python -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    echo "⚠️  Some dependencies missing. Installing..."
    pip install -r requirements_final.txt
fi

# Start the API server
echo "🌟 Starting FastAPI server on port 8058..."
echo "📝 Logs will be displayed below. Press Ctrl+C to stop."
echo "🌐 API will be available at: http://localhost:8058"
echo "📋 Health check: http://localhost:8058/health"
echo ""

python comprehensive_agent_api.py
