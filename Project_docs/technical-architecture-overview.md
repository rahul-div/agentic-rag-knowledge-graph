# 🛠 Technical Architecture Overview: RAG Chatbot for Financial Data

## 1. System Overview
A local, privacy-first RAG (Retrieval-Augmented Generation) chatbot designed to help financial beginners query historical NIFTY index data through natural language interaction. The system operates entirely offline after initial setup, ensuring complete data privacy while providing accurate, beginner-friendly responses to financial queries.

## 2. System Boundaries
- **In-Scope:**
  - Web Interface Module (Flask + Modern JS frontend)
  - Document Processing Module (CSV/PDF/TXT parsing and validation)
  - RAG Engine Module (Embeddings, vector search, LLM integration)
  - Data Storage Module (Chroma DB + JSON persistence)
  - Application Core Module (Startup/shutdown, configuration, orchestration)

- **Out-Scope:**
  - External API integrations
  - Real-time market data feeds
  - Multi-user authentication systems
  - Cloud deployment infrastructure
  - Advanced financial analytics engines

## 3. Overall Architecture & Integration
- **Chosen Architecture:** Monolithic Python Application with Modular Design
- **Module Integration Points:**
  - **Flask Web Server:** Central orchestrator handling HTTP requests and routing
  - **Shared Data Layer:** JSON files and Chroma DB accessible by all modules
  - **Event-Driven Processing:** Document upload triggers processing pipeline
  - **In-Memory State Management:** Application state shared across modules

## 4. System-Wide Technology Decisions
| Layer           | Technology                | Rationale                                         | Applies To Modules        |
|-----------------|---------------------------|---------------------------------------------------|---------------------------|
| Runtime         | Python 3.8+               | Mature ecosystem, excellent AI/ML libraries      | All modules               |
| Web Framework   | Flask                     | Lightweight, simple, minimal dependencies        | Web Interface Module      |
| Frontend        | HTML + Vanilla JS (ES6+)  | No build process, minimal dependencies          | Web Interface Module      |
| Vector Database | Chroma DB                 | Local vector storage, RAG-optimized             | RAG Engine, Data Storage  |
| Data Storage    | JSON Files                | Simple, human-readable, no additional deps      | Data Storage Module       |
| Embeddings      | SentenceTransformers      | Local processing, good accuracy                  | RAG Engine Module         |
| LLM             | Local LLM (TBD)           | Privacy-first, offline operation                 | RAG Engine Module         |
| Environment     | Python venv + requirements| Reproducible, isolated environment              | All modules               |

## 5. Cross-Module Data Flows
1. **Document Upload Flow:** Web Interface → Document Processing → Data Storage → RAG Engine (embeddings)
2. **Query Processing Flow:** Web Interface → RAG Engine → Data Storage (retrieval) → RAG Engine (response) → Web Interface
3. **Multi-Document Integration:** Document Processing → Data Storage (merge) → RAG Engine (re-indexing)
4. **Application Lifecycle:** Application Core → All Modules (initialization/shutdown)

## 6. System-Wide Non-Functional Requirements
- **Performance:** Query response time <5s, document processing <2min, memory usage <4GB RAM
- **Reliability:** 100% data accuracy for historical queries, graceful error handling, data integrity preservation
- **Security:** Local-only processing, no external data transmission, file system permissions
- **Usability:** Beginner-friendly interface, clear error messages, intuitive workflow
- **Maintainability:** Modular design, clear interfaces, comprehensive documentation

## 7. Integration Dependencies & External Services
- **External Dependencies:** None (fully local operation after setup)
- **Python Libraries:** Flask, Chroma DB, SentenceTransformers, pandas, PyPDF2, local LLM library
- **System Dependencies:** Python 3.8+, file system access, 4GB RAM, 2GB storage
- **Network Requirements:** Internet for initial setup only, offline operation thereafter

## 8. Module Architecture Map
- **Web Interface Module:** `technical/web-interface.md` - Flask backend + HTML/JS frontend
- **Document Processing Module:** `technical/document-processing.md` - File parsing and validation
- **RAG Engine Module:** `technical/rag-engine.md` - Embeddings, search, and response generation
- **Data Storage Module:** `technical/data-storage.md` - Chroma DB and JSON persistence
- **Application Core Module:** `technical/application-core.md` - Configuration and lifecycle management

## 9. System-Wide Risks & Mitigations
- **Risk:** Local LLM performance and accuracy limitations
  - **Mitigation:** Model selection criteria, fallback responses, accuracy validation framework

- **Risk:** Document format variations breaking parser
  - **Mitigation:** Robust parsing with error handling, format validation, user feedback

- **Risk:** Memory constraints with large datasets
  - **Mitigation:** Chunked processing, memory monitoring, dataset size limits

- **Risk:** User interface complexity for beginners
  - **Mitigation:** Progressive disclosure, guided workflows, comprehensive help text

- **Risk:** 100% accuracy requirement challenges
  - **Mitigation:** Data validation layers, explicit confidence scoring, clear limitation communication

## 10. Development & Deployment Strategy
- **Development Approach:** Module-first development with clear interfaces
- **Testing Strategy:** Unit tests per module, integration tests for workflows, accuracy validation
- **Deployment Model:** Single Python application with virtual environment
- **Documentation:** Module specifications, API documentation, user setup guide

## 11. Future Extensibility Considerations
- **Phase 2 Expansion:** Modular design allows easy addition of overseas market data modules
- **Scalability Paths:** Clear separation allows future microservices migration if needed
- **Integration Points:** Well-defined module interfaces support additional data sources
- **Performance Optimization:** Modular architecture enables targeted performance improvements
