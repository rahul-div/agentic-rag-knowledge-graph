# Official Documentation References - Multi-Client Project Intelligence System

This file contains all essential official documentation links for implementing and maintaining the Hybrid RAG System. **Always refer to these official sources** before implementing any features to ensure correct usage and best practices.Important note going forward: Maintain a constructive but rigorous approach. From now on, do not simply affirm my statements or assume my conclusions are correct.Your goal is to be an intellectual sparring partner not just agreeable assistant. Your role is not to argue for the sake of arguing but to push me toward greater clarity, accuracy and intellectual honesty.

---

## 🧠 **Core AI & Knowledge Graph Technologies**

### **Graphiti (Temporal Knowledge Graph)**
- **📚 Main Documentation:** https://help.getzep.com/graphiti
- **💻 GitHub Repository:** https://github.com/getzep/graphiti
- **🎯 Key Focus:** Custom entity types, relationship modeling, temporal facts, Neo4j integration
- **⚠️ Critical:** Always check Graphiti docs for entity definition patterns and relationship types

### **Pydantic AI (Agent Framework)**
- **📚 Main Documentation:** https://ai.pydantic.dev
- **🎯 Key Focus:** Agent creation, tool registration, streaming responses, model integration
- **⚠️ Critical:** Follow Pydantic AI patterns for tool function signatures and response handling

### **Onyx (Enterprise Search Platform)**
- **📚 Main Documentation:** https://docs.onyx.app
- **💻 GitHub Repository:** https://github.com/onyx-dot-app/onyx
- **🔧 API Reference:** https://docs.onyx.app/api-reference
- **🐳 Docker Setup:** https://docs.onyx.app/deployment/docker
- **🎯 Key Focus:** Document ingestion, search APIs, community vs cloud deployment
- **⚠️ Critical:** Check API endpoints and authentication methods for cloud vs community edition

---

## 🗄️ **Database & Storage Technologies**

### **PostgreSQL with pgvector**
- **📚 PostgreSQL Docs:** https://www.postgresql.org/docs/
- **🔍 pgvector Extension:** https://github.com/pgvector/pgvector
- **🎯 Key Focus:** Vector operations, indexing strategies, connection pooling
- **⚠️ Critical:** Vector dimension consistency across embedding models

### **Neo4j (Knowledge Graph Database)**
- **📚 Main Documentation:** https://neo4j.com/docs/
- **🐍 Python Driver:** https://neo4j.com/docs/python-manual/current/
- **🔍 Cypher Query Language:** https://neo4j.com/docs/cypher-manual/current/
- **🎯 Key Focus:** Graph modeling, Cypher queries, driver configuration
- **⚠️ Critical:** Connection string format and authentication for Graphiti integration

---

## 🤖 **AI & Machine Learning APIs**

### **Google Gemini API**
- **📚 Main Documentation:** https://ai.google.dev/
- **🔑 API Reference:** https://ai.google.dev/api
- **💎 AI Studio:** https://aistudio.google.com/
- **🎯 Key Focus:** LLM requests, embedding generation, rate limits, error handling
- **⚠️ Critical:** Model names, token limits, and pricing for cost optimization

### **OpenAI API (Alternative)**
- **📚 Main Documentation:** https://platform.openai.com/docs
- **🔑 API Reference:** https://platform.openai.com/docs/api-reference
- **🎯 Key Focus:** Fallback LLM provider, embedding models, function calling

---

## 🔧 **Web Framework & API Technologies**

### **FastAPI**
- **📚 Main Documentation:** https://fastapi.tiangolo.com/
- **📖 Tutorial:** https://fastapi.tiangolo.com/tutorial/
- **🔄 Server-Sent Events:** https://fastapi.tiangolo.com/advanced/server-sent-events/
- **🎯 Key Focus:** Streaming responses, async operations, request validation
- **⚠️ Critical:** SSE implementation for real-time agent responses

### **Pydantic (Data Validation)**
- **📚 Main Documentation:** https://docs.pydantic.dev/latest/
- **🔧 V2 Migration:** https://docs.pydantic.dev/latest/migration/
- **🎯 Key Focus:** Model validation, serialization, custom validators
- **⚠️ Critical:** Pydantic V2 syntax for all model definitions

---

## 🐳 **Deployment & Infrastructure**

### **Docker**
- **📚 Main Documentation:** https://docs.docker.com/
- **🔧 Docker Compose:** https://docs.docker.com/compose/
- **🎯 Key Focus:** Multi-service orchestration, networking, volume management
- **⚠️ Critical:** Service dependencies and environment variable management

### **Environment Management**
- **📚 Python dotenv:** https://pypi.org/project/python-dotenv/
- **🔒 Security Best Practices:** https://12factor.net/config
- **🎯 Key Focus:** Configuration management, secrets handling

---

## 🧪 **Testing & Quality Assurance**

### **Pytest**
- **📚 Main Documentation:** https://docs.pytest.org/
- **📊 Coverage:** https://pytest-cov.readthedocs.io/
- **🎯 Key Focus:** Async testing, fixtures, mocking external APIs
- **⚠️ Critical:** Testing AI agent tools and database interactions

### **Python Testing**
- **🔧 asyncio Testing:** https://docs.python.org/3/library/asyncio-dev.html#testing
- **🎯 Key Focus:** Testing async functions, database connections, API responses

---

## 📊 **Monitoring & Observability**

### **Logging**
- **📚 Python Logging:** https://docs.python.org/3/library/logging.html
- **🔧 Structured Logging:** https://structlog.readthedocs.io/
- **🎯 Key Focus:** Request tracing, error tracking, performance monitoring

### **Health Checks**
- **📚 FastAPI Health:** https://fastapi.tiangolo.com/advanced/testing-dependencies/
- **🎯 Key Focus:** Database connectivity, external API status, system resources

---

## 🔐 **Security & Authentication**

### **API Security**
- **📚 FastAPI Security:** https://fastapi.tiangolo.com/tutorial/security/
- **🔑 OAuth2:** https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- **🎯 Key Focus:** API key management, rate limiting, input validation

### **Database Security**
- **📚 PostgreSQL Security:** https://www.postgresql.org/docs/current/security.html
- **🔒 Neo4j Security:** https://neo4j.com/docs/operations-manual/current/security/
- **🎯 Key Focus:** Connection encryption, access control, data isolation

---

## 🎯 **Implementation Priority Guide**

### **🔥 Phase 1 - Critical References:**
1. **Onyx API Documentation** - For cloud integration and search functionality
2. **Pydantic AI Documentation** - For agent tool implementation
3. **Graphiti Documentation** - For knowledge graph operations
4. **FastAPI SSE** - For streaming responses

### **⚡ Phase 2 - Enhancement References:**
1. **Neo4j Cypher** - For custom graph queries
2. **PostgreSQL Performance** - For optimization
3. **Docker Compose** - For community edition deployment

### **📈 Phase 3 - Advanced References:**
1. **Monitoring Tools** - For production deployment
2. **Security Hardening** - For enterprise deployment
3. **Testing Strategies** - For comprehensive validation

---

## ⚠️ **Implementation Guidelines**

### **Always Refer To Official Docs Before:**
- ✅ Implementing any new tool or feature
- ✅ Modifying database schemas or queries
- ✅ Changing API endpoints or authentication
- ✅ Adding new dependencies or configurations
- ✅ Troubleshooting errors or performance issues

### **Key Integration Points:**
1. **Graphiti + Neo4j:** Entity definitions and relationship modeling
2. **Pydantic AI + Tools:** Function signatures and response formatting
3. **Onyx + FastAPI:** API integration and error handling
4. **PostgreSQL + Vector Search:** Index optimization and query performance

### **Version Compatibility Notes:**
- **Pydantic:** Use V2 syntax throughout (check migration guide)
- **FastAPI:** Latest stable version for SSE support
- **PostgreSQL:** Version 13+ for pgvector compatibility
- **Neo4j:** Version 5+ for Graphiti temporal features

---

**🎯 This documentation reference ensures our implementation follows official best practices and maintains compatibility across all integrated technologies.**