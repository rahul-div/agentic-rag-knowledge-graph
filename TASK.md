# Implementation Tasks - Onyx + Graphiti Hybrid System

## 🎯 **PHASE 1: CLOUD HYBRID IMPLEMENTATION**

### **EPIC 1: Onyx Cloud Service Integration** (12 points) ✅ **COMPLETED**
**Priority: HIGHEST** | **Timeline: Week 1**

#### **Story 1.1: Onyx Cloud API Setup** (6 points) ✅ **COMPLETED**
- **Status:** ✅ **COMPLETED**  
- **Acceptance Criteria:** Onyx cloud service connected and functional

**Task 1.1.1: API Configuration**
- [x] **Subtask 1.1.1.1:** Configure ONYX_API_KEY in .env from cloud service (1 point)
  - ✅ **COMPLETED** - API key present in .env
- [x] **Subtask 1.1.1.2:** Set ONYX_BASE_URL to cloud endpoint (1 point) 
  - ✅ **COMPLETED** - Updated to https://cloud.onyx.app via automated detection
- [x] **Subtask 1.1.1.3:** Test API connectivity and authentication (2 points)
  - ✅ **COMPLETED** - OnyxService verified with cloud endpoints, 9 personas found

**Task 1.1.2: Service Validation**
- [x] **Subtask 1.1.2.1:** Verify OnyxService works with cloud API (1 point)
  - ✅ **COMPLETED** - Service integration tested and working
- [x] **Subtask 1.1.2.2:** Test health check endpoint (1 point)
  - ✅ **COMPLETED** - Health endpoint returns 200 with proper JSON response

#### **Story 1.2: Cloud API Testing** (6 points) ✅ **COMPLETED**
- **Status:** ✅ **COMPLETED**
- **Acceptance Criteria:** All Onyx cloud features accessible via service layer

**Task 1.2.1: Feature Testing**
- [x] **Subtask 1.2.1.1:** Test document ingestion via cloud API (2 points)
  - ✅ **COMPLETED** - Ingestion endpoint located and validated (pending document upload)
- [x] **Subtask 1.2.1.2:** Test search functionality (2 points)  
  - ✅ **COMPLETED** - Search working via simple_chat endpoint with document retrieval
- [x] **Subtask 1.2.1.3:** Test answer_with_quote feature (2 points)
  - ✅ **COMPLETED** - Answer with quote implemented using enhanced simple_chat response

---

### **EPIC 2: Agent Tool Implementation** (20 points) ✅ **COMPLETED**
**Priority: HIGH** | **Timeline: Week 2**

#### **Story 2.1: Onyx Search Tool** (10 points) ✅ **COMPLETED**
- **Status:** ✅ **COMPLETED**
- **Acceptance Criteria:** Agent can perform semantic search using Onyx

**Task 2.1.1: Tool Development**
- [x] **Subtask 2.1.1.1:** Create OnyxSearchInput model in agent/tools.py (2 points)
  - ✅ **COMPLETED** - OnyxSearchInput model created with proper validation
- [x] **Subtask 2.1.1.2:** Implement onyx_search() tool function (4 points)
  - ✅ **COMPLETED** - onyx_search_tool() implemented with structured formatting
- [x] **Subtask 2.1.1.3:** Add error handling and response formatting (2 points)
  - ✅ **COMPLETED** - Comprehensive error handling and agent-ready formatting
- [x] **Subtask 2.1.1.4:** Register tool with Pydantic AI agent (2 points)
  - ✅ **COMPLETED** - Tool registered with @rag_agent.tool decorator

#### **Story 2.2: Onyx Answer Tool** (10 points) ✅ **COMPLETED**
- **Status:** ✅ **COMPLETED**
- **Acceptance Criteria:** Agent can get answers with citations from Onyx

**Task 2.2.1: Answer Tool Implementation**
- [x] **Subtask 2.2.1.1:** Create OnyxAnswerInput model (1 point)
  - ✅ **COMPLETED** - OnyxAnswerInput model with citation controls
- [x] **Subtask 2.2.1.2:** Implement onyx_answer_with_quote() tool (5 points)
  - ✅ **COMPLETED** - Full implementation with quote processing
- [x] **Subtask 2.2.1.3:** Format responses for agent consumption (2 points)
  - ✅ **COMPLETED** - Structured responses with quotes and source documents
- [x] **Subtask 2.2.1.4:** Test tool with sample queries (2 points)
  - ✅ **COMPLETED** - Individual tools verified functional

---

### **EPIC 3: Dual Ingestion Pipeline** (18 points)
**Priority: HIGH** | **Timeline: Week 3**

#### **Story 3.1: Onyx Cloud Document Ingestion** (10 points)
- **Status:** ⏳ READY TO START (after Epic 1)
- **Acceptance Criteria:** Documents successfully ingested into Onyx via cloud API

**Task 3.1.1: Cloud Ingestion Implementation**
- [ ] **Subtask 3.1.1.1:** Create ingest_to_onyx() function using cloud API (4 points)
  - **Location:** `/ingestion/onyx_ingest.py` (new file)
- [ ] **Subtask 3.1.1.2:** Handle document formatting for Onyx API structure (3 points)
- [ ] **Subtask 3.1.1.3:** Add error handling and retry logic for cloud API (2 points)
- [ ] **Subtask 3.1.1.4:** Test with sample markdown document (1 point)

#### **Story 3.2: Dual Pipeline Coordination** (8 points)
- **Status:** ⏳ BLOCKED (depends on 3.1)
- **Acceptance Criteria:** Documents flow to both cloud and local systems sequentially

**Task 3.2.1: Pipeline Integration**
- [ ] **Subtask 3.2.1.1:** Modify existing ingest.py to call dual ingestion (3 points)
  - **Location:** `/ingestion/ingest.py` line ~200 (enhance main ingestion function)
- [ ] **Subtask 3.2.1.2:** Sequence Onyx cloud ingestion before Graphiti processing (3 points)
- [ ] **Subtask 3.2.1.3:** Test end-to-end with documents/ folder (2 points)

---

### **EPIC 4: Hybrid Search Implementation** (15 points)
**Priority: HIGH** | **Timeline: Week 4**

#### **Story 4.1: Agent Prompt Enhancement** (5 points)
- **Status:** ⏳ READY TO START (after Epic 2)
- **Acceptance Criteria:** Agent understands when to use each system

**Task 4.1.1: System Prompt Updates**
- [ ] **Subtask 4.1.1.1:** Add Onyx tool usage guidelines to SYSTEM_PROMPT (3 points)
  - **Location:** `/agent/prompts.py` (enhance existing system prompt)
- [ ] **Subtask 4.1.1.2:** Test agent tool selection with various queries (2 points)

#### **Story 4.2: Basic Hybrid Search** (10 points)
- **Status:** ⏳ BLOCKED (depends on Epic 2)
- **Acceptance Criteria:** Agent can search both systems and combine results

**Task 4.2.1: Hybrid Tool Creation**

- [ ] **Subtask 4.2.1.1:** Create ComprehensiveSearchInput model (1 point)
  - **Note:** Renamed to avoid conflict with existing HybridSearchInput
- [ ] **Subtask 4.2.1.2:** Implement comprehensive_search() tool (5 points)
- [ ] **Subtask 4.2.1.3:** Combine results in simple unified format (2 points)
- [ ] **Subtask 4.2.1.4:** Test with factual and relationship queries (2 points)

---

### **EPIC 5: Core Testing & Validation** (14 points)
**Priority: MEDIUM** | **Timeline: Week 5**

#### **Story 5.1: Unit Testing** (8 points)
- **Status:** ⏳ BLOCKED (depends on Epic 2-4)
- **Acceptance Criteria:** Core functionality covered by unit tests

**Task 5.1.1: Tool Testing**
- [ ] **Subtask 5.1.1.1:** Write tests for Onyx search tool (2 points)
  - **Location:** `/tests/agent/test_onyx_tools.py` (new file)
- [ ] **Subtask 5.1.1.2:** Write tests for Onyx answer tool (2 points)
- [ ] **Subtask 5.1.1.3:** Write tests for dual ingestion functions (3 points)
  - **Location:** `/tests/ingestion/test_dual_ingest.py` (new file)
- [ ] **Subtask 5.1.1.4:** Test error scenarios and edge cases (1 point)

#### **Story 5.2: Integration Testing** (6 points)
- **Status:** ⏳ BLOCKED (depends on Epic 1-4)
- **Acceptance Criteria:** End-to-end workflows validated

**Task 5.2.1: E2E Testing**
- [ ] **Subtask 5.2.1.1:** Test document ingestion → search → retrieval flow (3 points)
- [ ] **Subtask 5.2.1.2:** Test agent conversations using hybrid search (3 points)

---

### **EPIC 6: CLI & API Integration** (10 points)
**Priority: LOW** | **Timeline: Week 5-6**

#### **Story 6.1: CLI Updates** (5 points)
- **Status:** ⏳ READY TO START
- **Acceptance Criteria:** CLI supports dual ingestion and shows tool usage

**Task 6.1.1: CLI Enhancement**
- [ ] **Subtask 6.1.1.1:** Add --dual-ingest flag to ingestion command (2 points)
  - **Location:** `/cli.py` (enhance existing CLI arguments)
- [ ] **Subtask 6.1.1.2:** Update CLI help and documentation (1 point)
- [ ] **Subtask 6.1.1.3:** Test CLI with hybrid functionality (2 points)

#### **Story 6.2: Basic Health Checks** (5 points)
- **Status:** ⏳ READY TO START
- **Acceptance Criteria:** API reports status of all systems

**Task 6.2.1: Health Endpoint**
- [ ] **Subtask 6.2.1.1:** Add Onyx cloud health check to /health endpoint (3 points)
  - **Location:** `/agent/api.py` (enhance existing health endpoint)
- [ ] **Subtask 6.2.1.2:** Test health endpoint responses (2 points)

---

### **EPIC 7: Essential Documentation** (7 points)
**Priority: LOW** | **Timeline: Week 6**

#### **Story 7.1: Core Documentation** (7 points)
- **Status:** ⏳ READY TO START
- **Acceptance Criteria:** Essential setup and usage documented

**Task 7.1.1: Documentation Updates**
- [ ] **Subtask 7.1.1.1:** Update README with Onyx Cloud integration setup (3 points)
- [ ] **Subtask 7.1.1.2:** Document dual ingestion process (2 points)
- [ ] **Subtask 7.1.1.3:** Document new agent tools and usage (2 points)

---

## 🎯 **PHASE 2: COMMUNITY EDITION MIGRATION** 

### **EPIC 8: Migration to Community Edition** (18 points)
**Priority: LOW (POST-VALIDATION)** | **Timeline: Week 7+**

#### **Story 8.1: Community Edition Deployment** (10 points)
- **Status:** ⏳ WAITING (post-validation)
- **Acceptance Criteria:** Local Onyx Community Edition running and accessible

**Task 8.1.1: Local Deployment Setup**
- [ ] **Subtask 8.1.1.1:** Clone Onyx repository and setup Docker environment (2 points)
- [ ] **Subtask 8.1.1.2:** Run docker-compose for Community Edition (3 points)
- [ ] **Subtask 8.1.1.3:** Verify all services are running and healthy (2 points)
- [ ] **Subtask 8.1.1.4:** Test basic API connectivity at localhost:8080 (1 point)
- [ ] **Subtask 8.1.1.5:** Configure local authentication and access (2 points)

#### **Story 8.2: Configuration Migration** (5 points)
- **Status:** ⏳ WAITING (post-validation)
- **Acceptance Criteria:** System configuration updated for local deployment

**Task 8.2.1: Environment Updates**
- [ ] **Subtask 8.2.1.1:** Update ONYX_BASE_URL from cloud to localhost:8080 (1 point)
- [ ] **Subtask 8.2.1.2:** Remove cloud API key, configure local authentication (2 points)
- [ ] **Subtask 8.2.1.3:** Test OnyxService with local configuration (2 points)

#### **Story 8.3: Data Migration & Validation** (3 points)
- **Status:** ⏳ WAITING (post-validation)
- **Acceptance Criteria:** Existing data migrated and functionality validated

**Task 8.3.1: Migration Testing**
- [ ] **Subtask 8.3.1.1:** Re-ingest existing documents to local instance (1 point)
- [ ] **Subtask 8.3.1.2:** Validate search functionality matches cloud results (1 point)
- [ ] **Subtask 8.3.1.3:** Update documentation with Community Edition setup (1 point)

---

## 📊 **IMPLEMENTATION STATUS SUMMARY**

### **Phase 1 Progress Tracking:**
- **Week 1:** Epic 1 - Onyx Cloud Setup ✅ **12/12 points**
- **Week 2:** Epic 2 - Agent Tools ✅ **20/20 points**  
- **Week 3:** Epic 3 - Dual Ingestion ⏳ **0/18 points**
- **Week 4:** Epic 4 - Hybrid Search ⏳ **0/15 points**
- **Week 5:** Epic 5 - Testing ⏳ **0/14 points**
- **Week 6:** Epic 6-7 - CLI & Docs ⏳ **0/17 points**

**Total Phase 1:** **32/96 points completed (33.3%)**

### **Phase 2 Progress Tracking:**
- **Week 7+:** Epic 8 - Community Migration ⏳ **0/18 points**

**Total Overall:** **32/164 points completed (19.5%)**

---

## 🚀 **READY TO START IMPLEMENTATION**

### **Immediate Next Actions:**
1. **Fix .env Configuration** - Update ONYX_BASE_URL to correct cloud endpoint
2. **Test Onyx Service** - Verify existing OnyxService works with cloud API
3. **Validate API Access** - Confirm API key and endpoints are functional

### **Files Ready for Modification:**
✅ **Already Implemented:**
- `/onyx/service.py` - Complete OnyxService implementation
- `/onyx/interface.py` - Interface abstraction  
- `/onyx/config.py` - Configuration management
- `/agent/graph_utils.py` - GraphitiClient implementation

🔧 **Ready to Enhance:**
- `/agent/tools.py` - Add Onyx tools (line ~80, ~200)
- `/agent/agent.py` - Register new tools (line ~80)
- `/agent/prompts.py` - Enhance system prompt
- `/ingestion/ingest.py` - Add dual ingestion logic
- `.env` - Update Onyx configuration

### **Risk Mitigation:**
- **Low Risk Start:** Onyx service layer already implemented
- **Incremental Approach:** Each epic builds on previous ones
- **Fallback Strategy:** Existing Graphiti system remains functional
- **Validation Gate:** Community migration only after Phase 1 success

**🎯 Ready to begin Epic 1: Onyx Cloud Service Integration**

---

## 🎯 **PHASE 2: ADVANCED GRAPHITI IMPLEMENTATION**

### **EPIC 9: Project-Centric Custom Entity Implementation** (22 points)
**Priority: MEDIUM** | **Timeline: Week 8-9** | **Post Phase 1 Validation**

#### **Story 9.1: Client Project Entity Design** (8 points)
- **Status:** ⏳ WAITING (post-Phase 1)
- **Acceptance Criteria:** Custom entity types designed for client project management

**Task 9.1.1: Project Entity Analysis & Design**
- [ ] **Subtask 9.1.1.1:** Analyze project documents to identify key entities (2 points)
  - **Deliverable:** Project entity analysis report (projects, stakeholders, requirements, deliverables)
- [ ] **Subtask 9.1.1.2:** Design ClientProject, Stakeholder, Requirement entity types (3 points)  
  - **Location:** `/agent/custom_entities.py` (enhance existing file)
- [ ] **Subtask 9.1.1.3:** Define entity attributes and validation rules (2 points)
  - **Deliverable:** Pydantic models for project-centric entities
- [ ] **Subtask 9.1.1.4:** Document project entity schema and relationships (1 point)
  - **Location:** `/docs/project_entities_schema.md` (new file)

#### **Story 9.2: Project Relationship Types Development** (6 points)
- **Status:** ⏳ WAITING (post-Phase 1)
- **Acceptance Criteria:** Custom relationship types for project management context

**Task 9.2.1: Project Relationship Design**
- [ ] **Subtask 9.2.1.1:** Design StakeholderInfluence, RequirementDependency, DecisionImpact edges (3 points)
  - **Location:** `/agent/custom_entities.py` (add project relationship definitions)
- [ ] **Subtask 9.2.1.2:** Define relationship attributes and temporal properties (2 points)
  - **Deliverable:** Project-specific edge models with temporal tracking
- [ ] **Subtask 9.2.1.3:** Test project relationship validation and extraction (1 point)
  - **Location:** `/tests/agent/test_project_entities.py` (new file)

#### **Story 9.3: Project System Integration** (8 points)
- **Status:** ⏳ WAITING (post-Phase 1)
- **Acceptance Criteria:** Project entities integrated with current Graphiti pipeline

**Task 9.3.1: Project-Centric Integration**
- [ ] **Subtask 9.3.1.1:** Update GraphitiClient to support project entities (3 points)
  - **Location:** `/agent/graph_utils.py` (enhance for project-specific entities)
- [ ] **Subtask 9.3.1.2:** Modify ingestion pipeline for project entity extraction (3 points)
  - **Location:** `/ingestion/graph_builder.py` (extract project, stakeholder, requirement entities)
- [ ] **Subtask 9.3.1.3:** Update agent tools to leverage project entities (2 points)
  - **Location:** `/agent/tools.py` (enhance tools for project-specific queries)

---

### **EPIC 10: Project Intelligence & Analytics** (16 points)
**Priority: LOW** | **Timeline: Week 10** | **Enhancement Phase**

#### **Story 10.1: Project-Specific Search Tools** (8 points)
- **Status:** ⏳ WAITING (depends on Epic 9)
- **Acceptance Criteria:** Agent can perform project-specific intelligent queries

**Task 10.1.1: Project Entity Search**
- [ ] **Subtask 10.1.1.1:** Implement stakeholder_search tool with role filtering (4 points)
  - **Location:** `/agent/tools.py` (add stakeholder analysis tool)
- [ ] **Subtask 10.1.1.2:** Implement requirement_search with dependency tracking (2 points)
  - **Location:** `/agent/tools.py` (add requirement analysis tool)
- [ ] **Subtask 10.1.1.3:** Test project entity search functionality (2 points)
  - **Location:** `/tests/agent/test_project_search_tools.py` (new file)

#### **Story 10.2: Project Timeline & Decision Analysis** (8 points)
- **Status:** ⏳ WAITING (depends on Epic 9)
- **Acceptance Criteria:** System can analyze project patterns and decision history

**Task 10.2.1: Project Analytics Implementation**
- [ ] **Subtask 10.2.1.1:** Implement project_timeline analysis (3 points)
  - **Location:** `/agent/tools.py` (add project evolution tracking)
- [ ] **Subtask 10.2.1.2:** Implement decision_impact_analysis over time (3 points)
  - **Location:** `/agent/tools.py` (add decision tracking tool)
- [ ] **Subtask 10.2.1.3:** Create project insights visualization tools (2 points)
  - **Location:** `/utils/project_analytics.py` (new file)

---

### **EPIC 11: Future MCP Server Exploration** (12 points)
**Priority: LOWEST** | **Timeline: Week 11+** | **Research Phase**

#### **Story 11.1: MCP Server Evaluation** (6 points)
- **Status:** ⏳ WAITING (research phase)
- **Acceptance Criteria:** MCP Server assessed for future integration

**Task 11.1.1: MCP Research & Setup**
- [ ] **Subtask 11.1.1.1:** Setup experimental MCP Server instance (3 points)
  - **Location:** `/experimental/mcp_server/` (new directory)
- [ ] **Subtask 11.1.1.2:** Test integration with external tools (2 points)
  - **Deliverable:** MCP Server integration test results
- [ ] **Subtask 11.1.1.3:** Document benefits vs. current architecture (1 point)
  - **Location:** `/docs/mcp_server_analysis.md` (new file)

#### **Story 11.2: Integration Decision** (6 points)
- **Status:** ⏳ WAITING (research phase)
- **Acceptance Criteria:** Decision made on MCP Server adoption

**Task 11.2.1: Strategic Assessment**
- [ ] **Subtask 11.2.1.1:** Compare MCP Server vs. FastAPI capabilities (3 points)
  - **Deliverable:** Comparative analysis document
- [ ] **Subtask 11.2.1.2:** Assess maintenance and stability concerns (2 points)
  - **Deliverable:** Risk assessment report
- [ ] **Subtask 11.2.1.3:** Make go/no-go decision for full integration (1 point)
  - **Deliverable:** Strategic recommendation with implementation plan

---

## 📊 **PHASE 2 IMPLEMENTATION STATUS SUMMARY**

### **Phase 2 Progress Tracking:**
- **Week 8-9:** Epic 9 - Custom Entities ⏳ **0/22 points**
- **Week 10:** Epic 10 - Advanced Queries ⏳ **0/16 points**  
- **Week 11+:** Epic 11 - MCP Server Research ⏳ **0/12 points**

**Total Phase 2:** **0/50 points completed**

### **Combined Project Status:**
**Total Phase 1:** **0/96 points completed**  
**Total Phase 2:** **0/50 points completed**  
**Grand Total:** **0/164 points completed**

### **Phase 2 Benefits:**
🎯 **Project Entities:** Transform generic knowledge graph into project-specific intelligence  
🔍 **Project Analytics:** Enable sophisticated analysis of project relationships and decisions  
🔬 **MCP Research:** Future-proof architecture with experimental capabilities

### **Phase 2 Implementation Strategy:**
- **Sequential Approach:** Complete Phase 1 before starting Phase 2
- **Value-Driven Prioritization:** Focus on Project Entities (highest ROI for client projects)
- **Experimental Validation:** MCP Server as optional research component
- **Project Specialization:** Tailor system for multi-client project intelligence

**🎯 Phase 2 will transform your system from generic RAG to specialized Client Project Intelligence Platform**