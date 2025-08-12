# Suggested Commands for Development

## Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Testing Commands
```bash
# Run all tests (58 tests should pass)
pytest

# Run tests with coverage
pytest --cov=agent --cov=ingestion --cov-report=html

# Run specific test categories
pytest tests/agent/
pytest tests/ingestion/

# Run tests in verbose mode
pytest -v
```

## Application Commands
```bash
# Run document ingestion (required first step)
python -m ingestion.ingest

# Start API server (default port 8058)
python -m agent.api

# Start CLI interface
python cli.py

# Quick status check
python quick_start.py

# Health check
curl http://localhost:8058/health
```

## Development Tools
```bash
# Format code (if black is installed)
black .

# Lint code (if ruff is installed) 
ruff .

# Type checking (if mypy is installed)
mypy .
```

## Database Commands
```bash
# Test database connection
python -c "import asyncio; from agent.db_utils import get_db_pool; asyncio.run(get_db_pool())"

# Execute schema (PostgreSQL with pgvector)
psql -d "$DATABASE_URL" -f sql/schema.sql
```

## System Information (macOS)
```bash
# List files and directories
ls -la

# Search for files
find . -name "*.py" -type f

# Search in files
grep -r "pattern" .

# Git operations
git status
git add .
git commit -m "message"
```

## Important Notes
- Always activate virtual environment before running commands
- Use `python3` explicitly on Linux systems (as mentioned in CLAUDE.md)
- Run ingestion before starting the API server for meaningful responses
- Default port is 8058 for consistency across the project