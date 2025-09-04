
# CORRECTED Multi-Tenant RAG Implementation Tasks - Following Neon Best Practices

## 🚨 **CRITICAL COURSE CORRECTION REQUIRED**

Our current shared-schema approach **CONTRADICTS** official Neon recommendations. This document provides the corrected implementation following Neon's **PRIMARY RECOMMENDATION**: Project-per-Tenant architecture.

---

## 📋 **CORRECTED TASK BREAKDOWN**

### **Phase 1: Catalog Database & Control Plane (Week 1)**
**Priority:** Critical  
**Risk:** Low  
**Approach:** Follow official Neon patterns  

#### **Task 1.1: Setup Catalog Database (Control Plane)**
**Estimated Time:** 2 days  
**Assignee:** Backend Developer  
**Dependencies:** None  

**Subtasks:**
- [ ] **1.1.1** Create main Neon project for catalog database
  ```python
  # Create via Neon API
  catalog_project = neon_client.create_project(
      name="rag-system-catalog",
      pg_version=16,
      region_id="aws-us-east-1"
  )
  ```

- [ ] **1.1.2** Implement catalog database schema
  ```sql
  -- Tenant-to-project mapping table
  CREATE TABLE tenant_projects (
      tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_name VARCHAR(255) NOT NULL,
      tenant_email VARCHAR(255) UNIQUE NOT NULL,
      neon_project_id VARCHAR(100) NOT NULL UNIQUE,
      neon_database_url TEXT NOT NULL,
      region VARCHAR(50) NOT NULL DEFAULT 'aws-us-east-1',
      status VARCHAR(20) DEFAULT 'active',
      plan VARCHAR(50) DEFAULT 'basic',
      max_documents INTEGER DEFAULT 1000,
      max_storage_mb INTEGER DEFAULT 500,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- Tenant configuration store
  CREATE TABLE tenant_configs (
      tenant_id UUID REFERENCES tenant_projects(tenant_id) ON DELETE CASCADE,
      config_key VARCHAR(100) NOT NULL,
      config_value JSONB NOT NULL,
      updated_at TIMESTAMPTZ DEFAULT NOW(),
      PRIMARY KEY (tenant_id, config_key)
  );

  -- Usage tracking and billing
  CREATE TABLE tenant_usage (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID REFERENCES tenant_projects(tenant_id),
      metric_name VARCHAR(50) NOT NULL,
      metric_value BIGINT NOT NULL,
      period_date DATE NOT NULL,
      recorded_at TIMESTAMPTZ DEFAULT NOW(),
      UNIQUE(tenant_id, metric_name, period_date)
  );
  ```

- [ ] **1.1.3** Create performance indexes
  ```sql
  CREATE INDEX idx_tenant_projects_status ON tenant_projects(status);
  CREATE INDEX idx_tenant_projects_created ON tenant_projects(created_at);
  CREATE INDEX idx_tenant_usage_period ON tenant_usage(tenant_id, period_date);
  CREATE INDEX idx_tenant_configs_key ON tenant_configs(config_key);
  ```

**Acceptance Criteria:**
- Catalog database created in dedicated Neon project
- All tables created with proper relationships and constraints
- Performance indexes in place
- Connection pooling configured for catalog access

#### **Task 1.2: Neon API Integration**
**Estimated Time:** 3 days  
**Assignee:** Backend Developer  
**Dependencies:** Task 1.1  

**Subtasks:**
- [ ] **1.2.1** Install and configure Neon API client
  ```python
  # Add to requirements.txt
  neondatabase-api-client==1.0.0
  
  # Environment configuration
  NEON_API_KEY=neon_api_xxxxxxxxxx
  CATALOG_DATABASE_URL=postgresql://...
  ```

- [ ] **1.2.2** Implement Neon project management service
  ```python
  from neondatabase import NeonAPIClient
  
  class NeonProjectManager:
      """Manages Neon projects for tenant isolation"""
      
      def __init__(self, api_key: str):
          self.client = NeonAPIClient(api_key=api_key)
      
      async def create_tenant_project(self, tenant_name: str, region: str = "aws-us-east-1"):
          """Create dedicated Neon project for tenant"""
          project = await self.client.create_project({
              "name": f"tenant-{tenant_name.lower().replace(' ', '-')}",
              "pg_version": 16,
              "region_id": region
          })
          
          # Get connection details
          connection = await self.client.get_connection_details(
              project_id=project.project.id,
              branch_id=project.project.default_branch_id
          )
          
          return {
              "project_id": project.project.id,
              "database_url": connection.connection_string,
              "region": region
          }
      
      async def delete_tenant_project(self, project_id: str):
          """Safely delete tenant's Neon project"""
          await self.client.delete_project(project_id=project_id)
  ```

- [ ] **1.2.3** Create tenant database schema initializer
  ```python
  class TenantSchemaInitializer:
      """Initialize identical schema in each tenant's database"""
      
      TENANT_SCHEMA_SQL = """
      -- Enable extensions
      CREATE EXTENSION IF NOT EXISTS "pgvector";
      CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
      
      -- Documents table (NO tenant_id - entire DB is for one tenant)
      CREATE TABLE documents (
          id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
          title TEXT NOT NULL,
          source TEXT NOT NULL,
          content TEXT NOT NULL,
          metadata JSONB DEFAULT '{}',
          created_at TIMESTAMPTZ DEFAULT NOW(),
          updated_at TIMESTAMPTZ DEFAULT NOW()
      );
      
      -- Chunks with vector embeddings
      CREATE TABLE chunks (
          id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
          document_id VARCHAR(50) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
          content TEXT NOT NULL,
          embedding VECTOR(768),
          chunk_index INTEGER NOT NULL,
          token_count INTEGER,
          metadata JSONB DEFAULT '{}',
          created_at TIMESTAMPTZ DEFAULT NOW()
      );
      
      -- Sessions for conversation tracking
      CREATE TABLE sessions (
          id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
          user_id VARCHAR(50),
          metadata JSONB DEFAULT '{}',
          created_at TIMESTAMPTZ DEFAULT NOW(),
          last_activity TIMESTAMPTZ DEFAULT NOW()
      );
      
      -- Messages for conversation history
      CREATE TABLE messages (
          id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
          session_id VARCHAR(50) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
          role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
          content TEXT NOT NULL,
          metadata JSONB DEFAULT '{}',
          created_at TIMESTAMPTZ DEFAULT NOW()
      );
      
      -- Performance indexes
      CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops);
      CREATE INDEX idx_chunks_document ON chunks(document_id);
      CREATE INDEX idx_messages_session ON messages(session_id, created_at);
      CREATE INDEX idx_documents_created ON documents(created_at);
      
      -- Vector search function
      CREATE OR REPLACE FUNCTION match_chunks(
          query_embedding VECTOR(768),
          match_threshold FLOAT DEFAULT 0.7,
          match_count INTEGER DEFAULT 10
      )
      RETURNS TABLE (
          chunk_id VARCHAR(50),
          document_id VARCHAR(50),
          content TEXT,
          similarity FLOAT
      )
      LANGUAGE SQL STABLE
      AS $$
          SELECT 
              chunks.id,
              chunks.document_id,
              chunks.content,
              1 - (chunks.embedding <=> query_embedding) AS similarity
          FROM chunks
          WHERE 1 - (chunks.embedding <=> query_embedding) > match_threshold
          ORDER BY chunks.embedding <=> query_embedding
          LIMIT match_count;
      $$;
      """
      
      async def initialize_tenant_database(self, database_url: str):
          """Initialize schema in new tenant database"""
          # Implementation to execute schema SQL
  ```

**Acceptance Criteria:**
- Neon API client properly configured and authenticated
- Can successfully create/delete Neon projects via API
- Schema initialization works for new tenant databases
- Connection details properly retrieved and stored

### **Phase 2: Tenant Manager Service (Week 2)**
**Priority:** Critical  
**Risk:** Low  

#### **Task 2.1: Core Tenant Manager Implementation**
**Estimated Time:** 4 days  
**Assignee:** Backend Developer  
**Dependencies:** Task 1.2  

**Subtasks:**
- [ ] **2.1.1** Implement comprehensive tenant manager
  ```python
  class TenantManager:
      """Complete tenant lifecycle management following Neon patterns"""
      
      def __init__(self, neon_api_key: str, catalog_db_url: str):
          self.neon_manager = NeonProjectManager(neon_api_key)
          self.catalog_db = CatalogDatabase(catalog_db_url)
          self.schema_initializer = TenantSchemaInitializer()
      
      async def create_tenant(self, name: str, email: str, region: str = "aws-us-east-1") -> UUID:
          """Create new tenant with dedicated Neon project"""
          
          # 1. Create Neon project
          project_info = await self.neon_manager.create_tenant_project(name, region)
          
          # 2. Initialize tenant database schema
          await self.schema_initializer.initialize_tenant_database(
              project_info["database_url"]
          )
          
          # 3. Store mapping in catalog
          tenant_id = await self.catalog_db.store_tenant_project(
              name=name,
              email=email,
              neon_project_id=project_info["project_id"],
              database_url=project_info["database_url"],
              region=region
          )
          
          return tenant_id
      
      async def get_tenant_database_url(self, tenant_id: UUID) -> str:
          """Get database connection for specific tenant"""
          tenant_info = await self.catalog_db.get_tenant_project(tenant_id)
          if not tenant_info or tenant_info.status != 'active':
              raise TenantNotFoundError(f"Tenant {tenant_id} not found or inactive")
          return tenant_info.database_url
      
      async def delete_tenant(self, tenant_id: UUID):
          """Safely delete tenant and all associated resources"""
          tenant_info = await self.catalog_db.get_tenant_project(tenant_id)
          
          # Delete Neon project (destroys all tenant data)
          await self.neon_manager.delete_tenant_project(tenant_info.neon_project_id)
          
          # Remove from catalog
          await self.catalog_db.delete_tenant_project(tenant_id)
      
      async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[TenantInfo]:
          """List all tenants with pagination"""
          return await self.catalog_db.list_tenant_projects(limit, offset)
      
      async def update_tenant_config(self, tenant_id: UUID, config: Dict[str, Any]):
          """Update tenant configuration"""
          await self.catalog_db.update_tenant_config(tenant_id, config)
  ```

- [ ] **2.1.2** Implement catalog database operations
  ```python
  class CatalogDatabase:
      """Database operations for tenant catalog"""
      
      def __init__(self, database_url: str):
          self.pool = create_async_pool(database_url)
      
      async def store_tenant_project(self, name: str, email: str, 
                                   neon_project_id: str, database_url: str, 
                                   region: str) -> UUID:
          """Store new tenant-project mapping"""
          async with self.pool.acquire() as conn:
              result = await conn.fetchrow("""
                  INSERT INTO tenant_projects 
                  (tenant_name, tenant_email, neon_project_id, neon_database_url, region)
                  VALUES ($1, $2, $3, $4, $5)
                  RETURNING tenant_id
              """, name, email, neon_project_id, database_url, region)
              return result['tenant_id']
      
      async def get_tenant_project(self, tenant_id: UUID) -> Optional[TenantProjectInfo]:
          """Get tenant project information"""
          async with self.pool.acquire() as conn:
              row = await conn.fetchrow("""
                  SELECT * FROM tenant_projects WHERE tenant_id = $1
              """, tenant_id)
              return TenantProjectInfo(**row) if row else None
  ```

- [ ] **2.1.3** Create tenant authentication and routing
  ```python
  class TenantAuthenticator:
      """Handle tenant authentication and request routing"""
      
      def __init__(self, tenant_manager: TenantManager):
          self.tenant_manager = tenant_manager
      
      async def authenticate_tenant(self, api_key: str) -> UUID:
          """Authenticate tenant by API key"""
          # Implementation for API key authentication
          pass
      
      async def get_tenant_database_connection(self, tenant_id: UUID) -> AsyncDatabase:
          """Get database connection for authenticated tenant"""
          db_url = await self.tenant_manager.get_tenant_database_url(tenant_id)
          return AsyncDatabase(db_url)
  ```

**Acceptance Criteria:**
- Complete tenant lifecycle management (CRUD operations)
- Proper error handling for tenant operations
- Database connection routing per tenant
- Comprehensive logging and monitoring
- Unit tests with >90% coverage

#### **Task 2.2: Migration Strategy for Existing Data**
**Estimated Time:** 2 days  
**Assignee:** Backend Developer  
**Dependencies:** Task 2.1  

**Subtasks:**
- [ ] **2.2.1** Create default tenant for existing data
  ```python
  async def migrate_existing_data_to_default_tenant():
      """Migrate current single-tenant data to default tenant project"""
      
      # 1. Create "Default Tenant" project
      default_tenant_id = await tenant_manager.create_tenant(
          name="Default Tenant",
          email="admin@company.com",
          region="aws-us-east-1"
      )
      
      # 2. Migrate existing data to default tenant database
      await migrate_data_to_tenant_database(
          source_db_url=CURRENT_DATABASE_URL,
          target_tenant_id=default_tenant_id
      )
      
      return default_tenant_id
  ```

- [ ] **2.2.2** Data migration utilities
  ```python
  class DataMigrationService:
      """Utilities for migrating data between databases"""
      
      async def export_tenant_data(self, source_db_url: str) -> Dict[str, List]:
          """Export all data from source database"""
          # Implementation for data export
          pass
      
      async def import_tenant_data(self, target_db_url: str, data: Dict[str, List]):
          """Import data into tenant database"""
          # Implementation for data import with proper validation
          pass
  ```

**Acceptance Criteria:**
- Existing data successfully migrated to default tenant
- Zero data loss during migration
- Migration process is repeatable and testable
- Rollback procedure documented and tested

#### **Task 2.3: Multi-Tenant Graphiti Implementation**
**Estimated Time:** 3 days  
**Assignee:** Backend Developer + AI Engineer  
**Dependencies:** Task 2.1  

**Subtasks:**
- [ ] **2.3.1** Implement shared Graphiti client with namespace isolation
  ```python
  class TenantGraphitiClient:
      """Shared Graphiti instance with tenant namespace isolation using group_id"""
      
      def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
          """Single Graphiti instance for all tenants"""
          self.graphiti = Graphiti(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
      
      def _get_tenant_namespace(self, tenant_id: str) -> str:
          """Generate namespace for tenant isolation"""
          return f"tenant_{tenant_id}"
      
      async def add_episode_for_tenant(self, tenant_id: str, episode_name: str, 
                                     episode_content: str, source_description: str = "Document"):
          """Add episode to tenant's namespace using group_id"""
          namespace = self._get_tenant_namespace(tenant_id)
          
          await self.graphiti.add_episode(
              name=episode_name,
              episode_body=episode_content,
              source_description=source_description,
              group_id=namespace  # ✅ Official Graphiti namespace isolation
          )
      
      async def search_for_tenant(self, tenant_id: str, query: str, limit: int = 10) -> List[Dict]:
          """Search within tenant's namespace only"""
          namespace = self._get_tenant_namespace(tenant_id)
          
          results = await self.graphiti.search(
              query=query,
              group_id=namespace,  # ✅ Search only within tenant namespace
              limit=limit
          )
          
          return results
      
      async def get_entities_for_tenant(self, tenant_id: str) -> List[Dict]:
          """Get all entities for specific tenant"""
          namespace = self._get_tenant_namespace(tenant_id)
          
          # Get entities filtered by namespace
          entities = await self.graphiti.get_entities(group_id=namespace)
          return entities
      
      async def create_relationship_for_tenant(self, tenant_id: str, 
                                            source_entity: str, target_entity: str,
                                            relationship_type: str, description: str):
          """Create relationship within tenant namespace"""
          namespace = self._get_tenant_namespace(tenant_id)
          
          await self.graphiti.create_relationship(
              source_entity=source_entity,
              target_entity=target_entity,
              relationship_type=relationship_type,
              description=description,
              group_id=namespace  # ✅ Namespace isolation
          )
      
      async def delete_tenant_data(self, tenant_id: str):
          """Delete all data for specific tenant"""
          namespace = self._get_tenant_namespace(tenant_id)
          
          # Delete all entities and relationships in tenant namespace
          await self.graphiti.delete_group_data(group_id=namespace)
  ```

- [ ] **2.3.2** Create Graphiti data models for tenant isolation
  ```python
  @dataclass
  class TenantGraphEpisode:
      """Episode model with tenant context"""
      tenant_id: str
      name: str
      content: str
      source_description: str = "Document content"
      reference_time: Optional[datetime] = None
      metadata: Dict[str, Any] = None
      
      def __post_init__(self):
          if self.reference_time is None:
              self.reference_time = datetime.now()
          if self.metadata is None:
              self.metadata = {}
  
  @dataclass
  class TenantGraphEntity:
      """Entity model with tenant context"""
      tenant_id: str
      name: str
      entity_type: str
      properties: Dict[str, Any] = None
      
      def __post_init__(self):
          if self.properties is None:
              self.properties = {}
  
  @dataclass
  class TenantGraphRelationship:
      """Relationship model with tenant context"""
      tenant_id: str
      source_entity: str
      target_entity: str
      relationship_type: str
      description: str
      properties: Dict[str, Any] = None
      
      def __post_init__(self):
          if self.properties is None:
              self.properties = {}
  ```

- [ ] **2.3.3** Implement tenant isolation validation for Graphiti
  ```python
  class GraphitiTenantValidator:
      """Validate Graphiti tenant isolation"""
      
      def __init__(self, graphiti_client: TenantGraphitiClient):
          self.client = graphiti_client
      
      async def validate_tenant_isolation(self, tenant_a_id: str, tenant_b_id: str) -> bool:
          """Verify that tenants cannot access each other's graph data"""
          
          # Add test data to tenant A
          await self.client.add_episode_for_tenant(
              tenant_id=tenant_a_id,
              episode_name="Secret Episode A",
              episode_content="This is secret content for tenant A only"
          )
          
          # Try to search for tenant A's data from tenant B
          tenant_b_results = await self.client.search_for_tenant(
              tenant_id=tenant_b_id,
              query="Secret Episode A"
          )
          
          # Should return no results (complete isolation)
          return len(tenant_b_results) == 0
      
      async def validate_namespace_consistency(self, tenant_id: str) -> bool:
          """Verify all tenant data is properly namespaced"""
          namespace = self.client._get_tenant_namespace(tenant_id)
          
          # Get all entities for tenant
          entities = await self.client.get_entities_for_tenant(tenant_id)
          
          # Verify all entities have correct namespace
          for entity in entities:
              if entity.get('group_id') != namespace:
                  return False
          
          return True
  ```

- [ ] **2.3.4** Integrate Graphiti with tenant lifecycle management
  ```python
  class TenantManager:
      """Enhanced tenant manager with Graphiti integration"""
      
      def __init__(self, neon_api_key: str, catalog_db_url: str, 
                   neo4j_uri: str, neo4j_user: str, neo4j_password: str):
          self.neon_manager = NeonProjectManager(neon_api_key)
          self.catalog_db = CatalogDatabase(catalog_db_url)
          self.schema_initializer = TenantSchemaInitializer()
          
          # ✅ ADDED: Shared Graphiti client for all tenants
          self.graphiti_client = TenantGraphitiClient(neo4j_uri, neo4j_user, neo4j_password)
      
      async def create_tenant(self, name: str, email: str, region: str = "aws-us-east-1") -> UUID:
          """Create new tenant with dedicated Neon project and Graphiti namespace"""
          
          # 1. Create Neon project
          project_info = await self.neon_manager.create_tenant_project(name, region)
          
          # 2. Initialize tenant database schema
          await self.schema_initializer.initialize_tenant_database(
              project_info["database_url"]
          )
          
          # 3. Store mapping in catalog
          tenant_id = await self.catalog_db.store_tenant_project(
              name=name,
              email=email,
              neon_project_id=project_info["project_id"],
              database_url=project_info["database_url"],
              region=region
          )
          
          # 4. ✅ ADDED: Initialize Graphiti namespace for tenant
          await self._initialize_tenant_graphiti_namespace(tenant_id)
          
          return tenant_id
      
      async def delete_tenant(self, tenant_id: UUID):
          """Safely delete tenant and all associated resources including Graphiti data"""
          tenant_info = await self.catalog_db.get_tenant_project(tenant_id)
          
          # 1. Delete Graphiti data for tenant
          await self.graphiti_client.delete_tenant_data(str(tenant_id))
          
          # 2. Delete Neon project (destroys all tenant data)
          await self.neon_manager.delete_tenant_project(tenant_info.neon_project_id)
          
          # 3. Remove from catalog
          await self.catalog_db.delete_tenant_project(tenant_id)
      
      async def _initialize_tenant_graphiti_namespace(self, tenant_id: UUID):
          """Initialize Graphiti namespace for new tenant"""
          # Add initial episode to establish namespace
          await self.graphiti_client.add_episode_for_tenant(
              tenant_id=str(tenant_id),
              episode_name="Tenant Initialization",
              episode_content=f"Tenant {tenant_id} initialized with dedicated namespace",
              source_description="System initialization"
          )
  ```

**Acceptance Criteria:**
- Shared Graphiti instance properly configured with Neo4j
- Tenant namespace isolation using group_id working correctly
- Complete data isolation verified between tenants
- No cross-tenant data leakage in graph operations
- All Graphiti operations scoped to tenant namespace
- Integration with tenant lifecycle (create/delete)
- Comprehensive isolation testing passed

#### **Task 2.4: Multi-Tenant Data Ingestion Service**
**Estimated Time:** 3 days  
**Assignee:** Backend Developer + AI Engineer  
**Dependencies:** Task 2.3  

**Subtasks:**
- [ ] **2.4.1** Implement coordinated document ingestion service
  ```python
  class TenantDataIngestionService:
      """Coordinate document ingestion into both Neon database and Neo4j graph"""
      
      def __init__(self, tenant_manager: TenantManager, embedder_service: EmbedderService):
          self.tenant_manager = tenant_manager
          self.embedder = embedder_service
      
      async def ingest_document_for_tenant(self, tenant_id: UUID, document: DocumentInput) -> str:
          """Complete document ingestion workflow for specific tenant"""
          
          # 1. Get tenant-specific dependencies
          deps = await TenantAgentDependencies.create_for_tenant(
              tenant_id=tenant_id,
              tenant_manager=self.tenant_manager,
              shared_graphiti_client=self.tenant_manager.graphiti_client
          )
          
          try:
              # 2. Store document in tenant's dedicated database
              document_id = await self._store_document_in_tenant_db(deps, document)
              
              # 3. Create and store chunks with embeddings
              await self._process_and_store_chunks(deps, document_id, document)
              
              # 4. Add document content to tenant's graph namespace
              await self._add_document_to_tenant_graph(deps, document_id, document)
              
              # 5. Update tenant usage metrics
              await self._update_tenant_metrics(tenant_id, document)
              
              return document_id
              
          except Exception as e:
              # Rollback on failure
              await self._rollback_ingestion(deps, document_id)
              raise IngestionError(f"Failed to ingest document for tenant {tenant_id}: {str(e)}")
      
      async def _store_document_in_tenant_db(self, deps: TenantAgentDependencies, 
                                           document: DocumentInput) -> str:
          """Store document in tenant's dedicated Neon database"""
          document_id = str(uuid.uuid4())
          
          await deps.tenant_database.execute("""
              INSERT INTO documents (id, title, source, content, metadata, created_at)
              VALUES ($1, $2, $3, $4, $5, NOW())
          """, document_id, document.title, document.source, document.content, document.metadata)
          
          return document_id
      
      async def _process_and_store_chunks(self, deps: TenantAgentDependencies, 
                                        document_id: str, document: DocumentInput):
          """Create chunks, generate embeddings, store in tenant database"""
          chunks = await self.embedder.create_chunks(document.content)
          
          for i, chunk in enumerate(chunks):
              embedding = await self.embedder.generate_embedding(chunk.content)
              
              await deps.tenant_database.execute("""
                  INSERT INTO chunks (id, document_id, content, embedding, chunk_index, token_count, metadata)
                  VALUES ($1, $2, $3, $4, $5, $6, $7)
              """, str(uuid.uuid4()), document_id, chunk.content, embedding, i, 
                  chunk.token_count, chunk.metadata)
      
      async def _add_document_to_tenant_graph(self, deps: TenantAgentDependencies, 
                                            document_id: str, document: DocumentInput):
          """Add document to tenant's graph namespace via Graphiti"""
          await deps.shared_graphiti.add_episode_for_tenant(
              tenant_id=str(deps.tenant_id),
              episode_name=f"Document: {document.title}",
              episode_content=document.content,
              source_description=f"Document from {document.source}"
          )
      
      async def _update_tenant_metrics(self, tenant_id: UUID, document: DocumentInput):
          """Update tenant usage metrics in catalog database"""
          await self.tenant_manager.catalog_db.update_tenant_usage(
              tenant_id=tenant_id,
              metric_name="documents_ingested",
              metric_value=1
          )
          
          await self.tenant_manager.catalog_db.update_tenant_usage(
              tenant_id=tenant_id,
              metric_name="storage_used_mb",
              metric_value=len(document.content) // (1024 * 1024)  # Rough estimate
          )
      
      async def _rollback_ingestion(self, deps: TenantAgentDependencies, document_id: str):
          """Rollback failed ingestion by cleaning up partial data"""
          try:
              # Remove document and cascading chunks from database
              await deps.tenant_database.execute(
                  "DELETE FROM documents WHERE id = $1", document_id
              )
              # Graph cleanup handled by transaction rollback in Graphiti
          except Exception as rollback_error:
              # Log rollback failure but don't raise to avoid masking original error
              logger.error(f"Rollback failed for document {document_id}: {rollback_error}")
  ```

- [ ] **2.4.2** Implement batch document ingestion
  ```python
  async def batch_ingest_documents_for_tenant(self, tenant_id: UUID, 
                                            documents: List[DocumentInput]) -> List[str]:
      """Batch ingest multiple documents for tenant with progress tracking"""
      
      results = []
      failed_documents = []
      
      for i, document in enumerate(documents):
          try:
              document_id = await self.ingest_document_for_tenant(tenant_id, document)
              results.append(document_id)
              
              # Progress callback
              await self._update_batch_progress(tenant_id, i + 1, len(documents))
              
          except IngestionError as e:
              failed_documents.append({"document": document, "error": str(e)})
              continue
      
      # Report batch results
      await self._report_batch_results(tenant_id, len(results), len(failed_documents))
      
      if failed_documents:
          raise BatchIngestionError(f"Failed to ingest {len(failed_documents)} documents", 
                                  failed_documents)
      
      return results
  ```

- [ ] **2.4.3** Implement document update and deletion workflows
  ```python
  async def update_document_for_tenant(self, tenant_id: UUID, document_id: str, 
                                     updated_document: DocumentInput) -> bool:
      """Update existing document in both database and graph"""
      deps = await TenantAgentDependencies.create_for_tenant(tenant_id, self.tenant_manager)
      
      # 1. Update document in database
      await deps.tenant_database.execute("""
          UPDATE documents 
          SET title = $2, content = $3, metadata = $4, updated_at = NOW()
          WHERE id = $1
      """, document_id, updated_document.title, updated_document.content, updated_document.metadata)
      
      # 2. Regenerate chunks and embeddings
      await deps.tenant_database.execute("DELETE FROM chunks WHERE document_id = $1", document_id)
      await self._process_and_store_chunks(deps, document_id, updated_document)
      
      # 3. Update graph (Graphiti handles episode updates)
      await deps.shared_graphiti.add_episode_for_tenant(
          tenant_id=str(tenant_id),
          episode_name=f"Updated Document: {updated_document.title}",
          episode_content=updated_document.content,
          source_description=f"Updated document from {updated_document.source}"
      )
      
      return True
  
  async def delete_document_for_tenant(self, tenant_id: UUID, document_id: str) -> bool:
      """Delete document from both database and graph"""
      deps = await TenantAgentDependencies.create_for_tenant(tenant_id, self.tenant_manager)
      
      # 1. Delete from database (cascades to chunks)
      result = await deps.tenant_database.execute(
          "DELETE FROM documents WHERE id = $1", document_id
      )
      
      # 2. Graph cleanup (Graphiti handles entity cleanup automatically)
      # No explicit deletion needed as episodes are content-based
      
      return result > 0
  ```

**Acceptance Criteria:**
- Documents successfully ingested into both tenant database and graph
- Complete rollback on ingestion failures
- Batch ingestion with progress tracking
- Document update/delete workflows working
- Tenant usage metrics properly tracked
- No cross-tenant data contamination during ingestion

### **Phase 3: Application Layer Updates (Week 3-4)**
**Priority:** High  
**Risk:** Medium  

#### **Task 3.1: Multi-Tenant RAG Agent**
**Estimated Time:** 5 days  
**Assignee:** AI Engineer + Backend Developer  
**Dependencies:** Task 2.4  

**Subtasks:**
- [ ] **3.1.1** Update agent dependencies for tenant isolation
  ```python
  @dataclass
  class TenantAgentDependencies:
      """Dependencies injected per tenant"""
      tenant_id: UUID
      tenant_database: AsyncDatabase
      shared_graphiti: TenantGraphitiClient  # ✅ FIXED: Shared Graphiti with tenant methods
      
      @classmethod
      async def create_for_tenant(cls, tenant_id: UUID, 
                                tenant_manager: TenantManager,
                                shared_graphiti_client: TenantGraphitiClient) -> 'TenantAgentDependencies':
          # Get tenant-specific database connection
          db_url = await tenant_manager.get_tenant_database_url(tenant_id)
          tenant_db = AsyncDatabase(db_url)
          
          # ✅ FIXED: Use shared Graphiti client (not per-tenant instance)
          # The TenantGraphitiClient handles namespacing internally
          
          return cls(
              tenant_id=tenant_id,
              tenant_database=tenant_db,
              shared_graphiti=shared_graphiti_client  # Shared instance
          )
  ```

- [ ] **3.1.2** Update all search tools for tenant isolation
  ```python
  # Vector search - now uses tenant-specific database
  async def vector_search_tool(input_data: VectorSearchInput, 
                             deps: TenantAgentDependencies) -> List[ChunkResult]:
      """Vector search within tenant's dedicated database"""
      
      # No tenant_id filtering needed - entire database is for this tenant
      query = """
          SELECT chunk_id, document_id, content, similarity
          FROM match_chunks($1, $2, $3)
      """
      
      results = await deps.tenant_database.fetch_all(
          query, input_data.embedding, input_data.threshold, input_data.limit
      )
      
      return [ChunkResult.from_row(row) for row in results]
  
  # Graph search - uses shared Graphiti with tenant namespacing
  async def graph_search_tool(input_data: GraphSearchInput,
                            deps: TenantAgentDependencies) -> List[GraphSearchResult]:
      """Graph search within tenant's namespace"""
      
      # ✅ FIXED: Use shared Graphiti with tenant-aware method
      results = await deps.shared_graphiti.search_for_tenant(
          tenant_id=deps.tenant_id,
          query=input_data.query
      )
      
      return [GraphSearchResult.from_dict(r) for r in results]
  ```

- [ ] **3.1.3** Update comprehensive search with tenant context
  ```python
  async def comprehensive_search_tool(input_data: ComprehensiveSearchInput,
                                    deps: TenantAgentDependencies) -> Dict[str, Any]:
      """Multi-system search within tenant boundaries"""
      
      # All searches automatically isolated to tenant's resources
      vector_results = await vector_search_tool(
          VectorSearchInput(embedding=input_data.embedding, limit=5),
          deps
      )
      
      graph_results = await graph_search_tool(
          GraphSearchInput(query=input_data.query, limit=5),
          deps
      )
      
      # Same synthesis logic as before
      return {
          "vector_results": vector_results,
          "graph_results": graph_results,
          "synthesized_response": await synthesize_results(vector_results, graph_results)
      }
  ```

**Acceptance Criteria:**
- All tools work with tenant-specific dependencies
- Complete tenant isolation verified through testing
- Same functionality as single-tenant version
- Performance parity with original implementation

#### **Task 3.2: Multi-Tenant API Endpoints**
**Estimated Time:** 3 days  
**Assignee:** Backend Developer  
**Dependencies:** Task 3.1  

**Subtasks:**
- [ ] **3.2.1** Implement tenant authentication middleware
  ```python
  class TenantAuthMiddleware:
      """Extract and validate tenant context from requests"""
      
      def __init__(self, tenant_authenticator: TenantAuthenticator):
          self.authenticator = tenant_authenticator
      
      async def __call__(self, request: Request, call_next):
          # Extract API key from Authorization header
          auth_header = request.headers.get("Authorization")
          if not auth_header or not auth_header.startswith("Bearer "):
              raise HTTPException(401, "Missing or invalid API key")
          
          api_key = auth_header.split(" ")[1]
          
          # Authenticate and get tenant ID
          tenant_id = await self.authenticator.authenticate_tenant(api_key)
          
          # Add tenant context to request state
          request.state.tenant_id = tenant_id
          
          return await call_next(request)
  ```

- [ ] **3.2.2** Update chat endpoints with tenant context
  ```python
  @app.post("/chat", response_model=ChatResponse)
  async def chat_endpoint(request: ChatRequest, 
                         tenant_id: UUID = Depends(get_tenant_id)) -> ChatResponse:
      """Chat endpoint with tenant isolation"""
      
      # Create tenant-specific agent dependencies
      deps = await TenantAgentDependencies.create_for_tenant(tenant_id, tenant_manager)
      
      # Same chat logic as before, but isolated per tenant
      agent = PydanticAIAgent(deps)
      response = await agent.chat(request.message)
      
      return ChatResponse(
          message=response,
          tenant_id=tenant_id,
          session_id=request.session_id
      )
  
  # Tenant management endpoints
  @app.post("/tenants", response_model=TenantResponse)
  async def create_tenant_endpoint(request: CreateTenantRequest) -> TenantResponse:
      """Create new tenant with dedicated Neon project"""
      tenant_id = await tenant_manager.create_tenant(
          name=request.name,
          email=request.email,
          region=request.region or "aws-us-east-1"
      )
      
      return TenantResponse(tenant_id=tenant_id, status="created")
  ```

**Acceptance Criteria:**
- Tenant authentication working properly
- All endpoints respect tenant boundaries
- Proper error handling for invalid tenants
- API documentation updated for multi-tenancy

#### **Task 3.3: Multi-Tenant Ingestion API Endpoints**
**Estimated Time:** 2 days  
**Assignee:** Backend Developer  
**Dependencies:** Task 2.4, Task 3.2  

**Subtasks:**
- [ ] **3.3.1** Implement document ingestion endpoints
  ```python
  @app.post("/tenants/{tenant_id}/documents", response_model=IngestionResponse)
  async def ingest_document_endpoint(
      tenant_id: UUID,
      document: DocumentInput,
      current_tenant: UUID = Depends(get_authenticated_tenant)
  ) -> IngestionResponse:
      """Ingest single document into tenant's database and graph"""
      
      # Verify tenant access
      if tenant_id != current_tenant:
          raise HTTPException(403, "Access denied to this tenant")
      
      try:
          document_id = await tenant_ingestion_service.ingest_document_for_tenant(
              tenant_id=tenant_id,
              document=document
          )
          
          return IngestionResponse(
              document_id=document_id,
              status="success",
              message="Document ingested successfully"
          )
          
      except IngestionError as e:
          raise HTTPException(400, f"Ingestion failed: {str(e)}")
  
  @app.post("/tenants/{tenant_id}/documents/batch", response_model=BatchIngestionResponse)
  async def batch_ingest_documents_endpoint(
      tenant_id: UUID,
      documents: List[DocumentInput],
      current_tenant: UUID = Depends(get_authenticated_tenant)
  ) -> BatchIngestionResponse:
      """Batch ingest multiple documents for tenant"""
      
      if tenant_id != current_tenant:
          raise HTTPException(403, "Access denied to this tenant")
      
      try:
          document_ids = await tenant_ingestion_service.batch_ingest_documents_for_tenant(
              tenant_id=tenant_id,
              documents=documents
          )
          
          return BatchIngestionResponse(
              document_ids=document_ids,
              total_ingested=len(document_ids),
              total_failed=0,
              status="success"
          )
          
      except BatchIngestionError as e:
          return BatchIngestionResponse(
              document_ids=e.successful_ids if hasattr(e, 'successful_ids') else [],
              total_ingested=len(e.successful_ids) if hasattr(e, 'successful_ids') else 0,
              total_failed=len(e.failed_documents),
              status="partial_success",
              errors=e.failed_documents
          )
  ```

- [ ] **3.3.2** Implement document management endpoints
  ```python
  @app.get("/tenants/{tenant_id}/documents", response_model=List[DocumentSummary])
  async def list_tenant_documents(
      tenant_id: UUID,
      limit: int = 100,
      offset: int = 0,
      current_tenant: UUID = Depends(get_authenticated_tenant)
  ) -> List[DocumentSummary]:
      """List all documents for tenant with pagination"""
      
      if tenant_id != current_tenant:
          raise HTTPException(403, "Access denied to this tenant")
      
      deps = await TenantAgentDependencies.create_for_tenant(tenant_id, tenant_manager)
      
      documents = await deps.tenant_database.fetch_all("""
          SELECT id, title, source, created_at, updated_at
          FROM documents
          ORDER BY created_at DESC
          LIMIT $1 OFFSET $2
      """, limit, offset)
      
      return [DocumentSummary.from_row(doc) for doc in documents]
  
  @app.get("/tenants/{tenant_id}/documents/{document_id}", response_model=DocumentDetail)
  async def get_tenant_document(
      tenant_id: UUID,
      document_id: str,
      current_tenant: UUID = Depends(get_authenticated_tenant)
  ) -> DocumentDetail:
      """Get specific document details for tenant"""
      
      if tenant_id != current_tenant:
          raise HTTPException(403, "Access denied to this tenant")
      
      deps = await TenantAgentDependencies.create_for_tenant(tenant_id, tenant_manager)
      
      document = await deps.tenant_database.fetch_one("""
          SELECT * FROM documents WHERE id = $1
      """, document_id)
      
      if not document:
          raise HTTPException(404, "Document not found")
      
      return DocumentDetail.from_row(document)
  
  @app.put("/tenants/{tenant_id}/documents/{document_id}", response_model=UpdateResponse)
  async def update_tenant_document(
      tenant_id: UUID,
      document_id: str,
      updated_document: DocumentInput,
      current_tenant: UUID = Depends(get_authenticated_tenant)
  ) -> UpdateResponse:
      """Update existing document for tenant"""
      
      if tenant_id != current_tenant:
          raise HTTPException(403, "Access denied to this tenant")
      
      try:
          success = await tenant_ingestion_service.update_document_for_tenant(
              tenant_id=tenant_id,
              document_id=document_id,
              updated_document=updated_document
          )
          
          if not success:
              raise HTTPException(404, "Document not found")
          
          return UpdateResponse(status="success", message="Document updated successfully")
          
      except Exception as e:
          raise HTTPException(400, f"Update failed: {str(e)}")
  
  @app.delete("/tenants/{tenant_id}/documents/{document_id}", response_model=DeleteResponse)
  async def delete_tenant_document(
      tenant_id: UUID,
      document_id: str,
      current_tenant: UUID = Depends(get_authenticated_tenant)
  ) -> DeleteResponse:
      """Delete document from tenant's database and graph"""
      
      if tenant_id != current_tenant:
          raise HTTPException(403, "Access denied to this tenant")
      
      success = await tenant_ingestion_service.delete_document_for_tenant(
          tenant_id=tenant_id,
          document_id=document_id
      )
      
      if not success:
          raise HTTPException(404, "Document not found")
      
      return DeleteResponse(status="success", message="Document deleted successfully")
  ```

- [ ] **3.3.3** Implement tenant usage and metrics endpoints
  ```python
  @app.get("/tenants/{tenant_id}/usage", response_model=TenantUsageResponse)
  async def get_tenant_usage(
      tenant_id: UUID,
      current_tenant: UUID = Depends(get_authenticated_tenant)
  ) -> TenantUsageResponse:
      """Get tenant usage statistics and limits"""
      
      if tenant_id != current_tenant:
          raise HTTPException(403, "Access denied to this tenant")
      
      # Get tenant info and usage from catalog
      tenant_info = await tenant_manager.catalog_db.get_tenant_project(tenant_id)
      usage_stats = await tenant_manager.catalog_db.get_tenant_usage_stats(tenant_id)
      
      deps = await TenantAgentDependencies.create_for_tenant(tenant_id, tenant_manager)
      
      # Get current document and chunk counts
      doc_count = await deps.tenant_database.fetch_val("SELECT COUNT(*) FROM documents")
      chunk_count = await deps.tenant_database.fetch_val("SELECT COUNT(*) FROM chunks")
      
      return TenantUsageResponse(
          tenant_id=tenant_id,
          plan=tenant_info.plan,
          documents_count=doc_count,
          chunks_count=chunk_count,
          max_documents=tenant_info.max_documents,
          max_storage_mb=tenant_info.max_storage_mb,
          usage_stats=usage_stats
      )
  
  @app.get("/tenants/{tenant_id}/search/test", response_model=SearchTestResponse)
  async def test_tenant_search(
      tenant_id: UUID,
      query: str,
      current_tenant: UUID = Depends(get_authenticated_tenant)
  ) -> SearchTestResponse:
      """Test search functionality for tenant (vector + graph)"""
      
      if tenant_id != current_tenant:
          raise HTTPException(403, "Access denied to this tenant")
      
      deps = await TenantAgentDependencies.create_for_tenant(tenant_id, tenant_manager)
      
      # Test vector search
      embedding = await embedder_service.generate_embedding(query)
      vector_results = await deps.tenant_database.fetch_all("""
          SELECT content, similarity FROM match_chunks($1, 0.7, 5)
      """, embedding)
      
      # Test graph search
      graph_results = await deps.shared_graphiti.search_for_tenant(
          tenant_id=str(tenant_id),
          query=query,
          limit=5
      )
      
      return SearchTestResponse(
          query=query,
          vector_results_count=len(vector_results),
          graph_results_count=len(graph_results),
          vector_results=[{"content": r["content"], "similarity": r["similarity"]} for r in vector_results],
          graph_results=graph_results
      )
  ```

**Acceptance Criteria:**
- Complete document ingestion API (single + batch)
- Document management endpoints (CRUD operations)
- Proper tenant authentication and authorization
- Usage monitoring and metrics endpoints
- Search testing endpoints for validation
- Comprehensive error handling and responses
- API documentation with tenant-specific examples

### **Phase 4: Testing & Validation (Week 5)**
**Priority:** Critical  
**Risk:** Medium  

#### **Task 4.1: Tenant Isolation Testing**
**Estimated Time:** 3 days  
**Assignee:** QA Engineer + Backend Developer  
**Dependencies:** Task 3.3  

**Subtasks:**
- [ ] **4.1.1** Create comprehensive tenant isolation test suite
  ```python
  class TestTenantIsolation:
      """Verify complete tenant isolation"""
      
      async def test_data_isolation(self):
          """Verify tenants cannot access each other's data"""
          # Create two tenants
          tenant_a = await tenant_manager.create_tenant("Tenant A", "a@test.com")
          tenant_b = await tenant_manager.create_tenant("Tenant B", "b@test.com")
          
          # Add data to tenant A
          await add_test_data(tenant_a, "Secret A Data")
          
          # Verify tenant B cannot see tenant A's data
          results = await search_tenant_data(tenant_b, "Secret A Data")
          assert len(results) == 0, "Data leaked between tenants!"
      
      async def test_database_isolation(self):
          """Verify tenants use completely separate databases"""
          tenant_a_url = await tenant_manager.get_tenant_database_url(tenant_a)
          tenant_b_url = await tenant_manager.get_tenant_database_url(tenant_b)
          
          assert tenant_a_url != tenant_b_url, "Tenants sharing database URL!"
          
          # Verify different Neon project IDs
          tenant_a_info = await catalog_db.get_tenant_project(tenant_a)
          tenant_b_info = await catalog_db.get_tenant_project(tenant_b)
          
          assert tenant_a_info.neon_project_id != tenant_b_info.neon_project_id
  ```

- [ ] **4.1.2** Performance testing under multi-tenant load
- [ ] **4.1.3** Security penetration testing

**Acceptance Criteria:**
- Zero cross-tenant data leakage in all tests
- Performance degradation < 5% compared to single-tenant
- All security tests pass
- Comprehensive test coverage > 95%

### **Phase 5: Production Deployment (Week 6)**
**Priority:** High  
**Risk:** Low  

#### **Task 5.1: Production Rollout**
**Estimated Time:** 3 days  
**Assignee:** DevOps + Backend Developer  
**Dependencies:** Task 4.1  

**Subtasks:**
- [ ] **5.1.1** Deploy catalog database to production Neon project
- [ ] **5.1.2** Configure production Neon API credentials
- [ ] **5.1.3** Deploy tenant manager service
- [ ] **5.1.4** Migrate existing data to default tenant
- [ ] **5.1.5** Update monitoring and alerting for multi-tenant metrics

**Acceptance Criteria:**
- Production deployment successful
- Existing functionality preserved
- Monitoring covers all tenant operations
- Rollback procedure tested and documented

---

## 🎯 **KEY BENEFITS OF CORRECTED APPROACH**

1. **Follows Official Neon Best Practices** ✅
2. **True Tenant Isolation** (no RLS complexity) ✅
3. **Linear Scaling** (unlimited tenants) ✅
4. **Cost Optimization** (scale-to-zero) ✅
5. **Operational Simplicity** (no shared table management) ✅
6. **Production-Proven Pattern** ✅

---

## 📊 **IMPLEMENTATION TIMELINE**

- **Week 1**: Catalog database + Neon API integration
- **Week 2**: Tenant manager service + migration strategy  
- **Week 3-4**: Application layer updates + API changes
- **Week 5**: Comprehensive testing + validation
- **Week 6**: Production deployment + monitoring

**Total Duration**: 6 weeks (same as original estimate)
**Risk Level**: LOW (following official patterns)
**Effort**: Same development effort, but correct architecture
