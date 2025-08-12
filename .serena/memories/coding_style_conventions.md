# Code Style and Conventions

## Code Style Guidelines (from CLAUDE.md)
- **Primary Language**: Python
- **Style Guide**: Follow PEP8
- **Type Hints**: Use comprehensive type hints throughout
- **Formatting**: Use `black` formatter (when available)
- **Linting**: Use `ruff` linter (when available)
- **File Size**: Never create a file longer than 500 lines of code
- **Imports**: Prefer relative imports within packages

## Documentation Standards
- **Docstrings**: Required for every function using Google style:
  ```python
  def example():
      """
      Brief summary.

      Args:
          param1 (type): Description.

      Returns:
          type: Description.
      """
  ```
- **Comments**: Add inline `# Reason:` comments for complex logic explaining the why
- **Type Safety**: Use Pydantic models for validation and dataclasses for dependencies

## Architecture Patterns
- **Modularity**: Clear separation of concerns with reusable components
- **Async-First**: All database operations async with proper resource management
- **Error Handling**: Graceful degradation with comprehensive logging
- **Dependency Injection**: Clean dependency structure using dataclasses
- **Testing**: Unit tests for all components with mocked external dependencies

## Observed Patterns in Codebase
- **Agent Structure**: Uses Pydantic AI with tool decorators (no `description=` parameter)
- **Database**: AsyncPG connection pooling with transaction management
- **Models**: Pydantic models for data validation (e.g., ChunkResult, DocumentResult)
- **CLI**: Rich library for color-coded output and formatting
- **Configuration**: Environment-based with python-dotenv
- **Streaming**: Server-Sent Events for real-time responses

## Project Organization
- Modular structure with feature-based directories
- Clear separation between agent, ingestion, and API layers
- Comprehensive test coverage with fixtures and mocks
- Environment variables for configuration
- Git ignore patterns for Python projects