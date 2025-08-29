# Agentic RAG with Knowledge Graph - Project Overview

## Purpose
This project builds a comprehensive **hybrid RAG system** that intelligently combines **two distinct retrieval paths**: **Onyx Cloud enterprise search** and **Local Path: Dual Storage** (pgvector + Neo4j + Graphiti) into a unified intelligent agent platform. The system provides deep insights and relationship analysis across multiple data sources with automatic tool selection and fallback mechanisms.

## Key Features
- **Hybrid Search**: Combines vector similarity search with knowledge graph traversal
- **Temporal Knowledge**: Tracks how information changes over time using Neo4j + Graphiti
- **Streaming Responses**: Real-time AI responses with Server-Sent Events
- **Flexible LLM Providers**: Support for OpenAI, Ollama, OpenRouter, Gemini
- **Agent Transparency**: Shows which tools the agent uses for each query
- **Production Ready**: Comprehensive testing (58/58 tests passing), logging, and error handling

## Architecture Components
1. **Agent System** (`/agent`): Pydantic AI agent with tools and API endpoints
2. **Ingestion System** (`/ingestion`): Document processing pipeline with semantic chunking
3. **Database Layer** (`/sql`): PostgreSQL schema with pgvector extension
4. **CLI Interface** (`/cli.py`): Interactive command-line interface with streaming
5. **Tests** (`/tests`): Comprehensive unit and integration tests

## Current Status
✅ All core functionality completed and tested
✅ 58/58 tests passing
✅ Production ready
✅ Comprehensive documentation
✅ Flexible provider system implemented
✅ CLI with agent transparency features
✅ Neo4j + Graphiti integration with OpenAI-compatible clients