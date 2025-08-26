#!/bin/bash

# 🚀 Start CLI Client Script
# Automatically activates virtual environment and starts the CLI client

set -e  # Exit on any error

echo "💬 Starting Hybrid RAG Agent CLI Client..."

# Check if we're in the correct directory
if [ ! -f "comprehensive_agent_cli.py" ]; then
    echo "❌ Error: comprehensive_agent_cli.py not found"
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

# Check if API server is running
echo "🔍 Checking if API server is running..."
if ! curl -s http://localhost:8058/health >/dev/null 2>&1; then
    echo "⚠️  API server not detected on port 8058"
    echo "Please start the API server first:"
    echo "  ./start_api.sh"
    echo "Or manually:"
    echo "  source .venv/bin/activate"
    echo "  python comprehensive_agent_api.py"
    echo ""
    echo "Continuing anyway in case API is starting up..."
fi

# Check if required dependencies are installed
echo "🔍 Checking dependencies..."
if ! python -c "import aiohttp, rich" 2>/dev/null; then
    echo "⚠️  Some dependencies missing. Installing..."
    pip install -r requirements_final.txt
fi

# Start the CLI client
echo "🌟 Starting CLI client..."
echo "📝 Type '/help' for available commands"
echo "🚪 Type '/quit' to exit"
echo ""

python comprehensive_agent_cli.py
