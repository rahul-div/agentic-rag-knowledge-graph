# Multi-Tenant RAG Prototype Implementation Roadmap

## Prototype Goals (Validated)

1. **Tenant Creation Model**
   - No authentication initially - focus on data isolation
   - Simple tenant identification via tenant_slug parameter

2. **User Management Scope**
   - Single admin per tenant (simplified for prototype)
   - No complex user roles or permissions

3. **Resource Limits**
   - No resource limitations for prototype testing

4. **Deployment Target**
   - Quick deployment on Amazon EC2 for testing

## Week 1: Core Prototype Development

### Day 1-2: Database Infrastructure

**Tasks:**
1. Set up simple PostgreSQL tenant registry
2. Create basic tenant schema (no auth tables)
3. Integrate with existing tenant infrastructure
4. Test Neon project creation per tenant

**Files to Create:**
- `database/migrations/001_simple_tenant_schema.sql`
- `database/connection.py` 
- `models/tenant.py` (simplified)

**Integration Points:**
- Update existing `TenantManager` for simplified schema
- Remove authentication complexity
- Focus on tenant isolation mechanics

### Day 3-4: Core Services

**Tasks:**
1. Create simplified tenant service
2. Build document ingestion service (tenant-isolated)
3. Build search service (tenant-isolated)
4. Test with existing Graphiti integration

**Files to Create:**
- `services/tenant_service.py` (simplified)
- `services/ingestion_service.py`
- `services/search_service.py`

**Integration Points:**
- Use existing `multi_tenant_agent.py` structure
- Ensure proper Neo4j group_id isolation
- Test Neon database isolation

### Day 5-7: API Endpoints

**Tasks:**
1. Create tenant management endpoints
2. Create document ingestion endpoints
3. Create search/query endpoints
4. Add basic error handling

**Files to Create:**
- `api/tenants.py`
- `api/documents.py`
- `api/search.py`

**Core Endpoints:**
```bash
POST   /tenants                           # Create tenant
GET    /tenants                           # List tenants
POST   /tenants/{slug}/documents          # Upload document
GET    /tenants/{slug}/documents          # List documents
POST   /tenants/{slug}/query              # Hybrid RAG query
POST   /tenants/{slug}/search/vector      # Vector search
POST   /tenants/{slug}/search/graph       # Graph search
```

## Week 2: CLI & EC2 Deployment

### Day 8-10: CLI Development

**Tasks:**
1. Create simplified CLI (no auth commands)
2. Add tenant creation commands
3. Add document upload commands
4. Add query/search commands

**Files to Update:**
- `interactive_multi_tenant_cli.py` (major simplification)

**CLI Commands:**
```bash
mt-rag tenant create --name "Acme" --slug "acme"
mt-rag docs upload --tenant acme --file document.pdf
mt-rag query --tenant acme "search query"
mt-rag search --tenant acme --type vector "search query"
```

### Day 11-12: Docker & Deployment Prep

**Tasks:**
1. Create Docker containers
2. Set up docker-compose.yml
3. Test local deployment
4. Prepare EC2 deployment scripts

**Files to Create:**
- `Dockerfile`
- `docker-compose.yml`
- `deploy/ec2-setup.sh`

### Day 13-14: EC2 Deployment & Testing

**Tasks:**
1. Deploy to EC2 instance
2. Create 2 test tenants ("acme", "demo")
3. Upload different documents to each tenant
4. Test isolation via CLI and API calls
5. Validate complete tenant separation

**Testing Checklist:**
- [ ] Tenant "acme" data not visible to "demo" queries
- [ ] Tenant "demo" data not visible to "acme" queries
- [ ] Both tenants can upload/search independently
- [ ] Neo4j group_id isolation working
- [ ] Neon database isolation working
- [ ] CLI works with both tenants
- [ ] API endpoints work for both tenants

## Implementation Priority Order

### Priority 1: Tenant Isolation Foundation
1. Simple tenant registry database
2. Neon project-per-tenant setup
3. Neo4j group_id isolation
4. Basic tenant service

### Priority 2: Core Functionality
1. Document ingestion with tenant isolation
2. Vector search with tenant isolation
3. Graph search with tenant isolation
4. Hybrid RAG queries with tenant isolation

### Priority 3: API Layer
1. Tenant management endpoints
2. Document ingestion endpoints
3. Search/query endpoints
4. Basic error handling

### Priority 4: CLI & Deployment
1. Simplified CLI tool
2. Docker containerization
3. EC2 deployment
4. Multi-tenant testing

## Success Criteria for Prototype

### Functional Requirements
- [ ] Create tenants via API/CLI
- [ ] Upload documents per tenant
- [ ] Search/query per tenant with full isolation
- [ ] No cross-tenant data leaks
- [ ] Deploy and test on EC2

### Technical Requirements
- [ ] Neon project-per-tenant working
- [ ] Neo4j group_id isolation working
- [ ] API endpoints functional
- [ ] CLI commands working
- [ ] Docker deployment successful

### Test Validation
- [ ] 2 tenants created and tested
- [ ] Different documents uploaded to each
- [ ] Search results completely isolated
- [ ] Performance acceptable (<3 seconds per query)

## Next Steps After Prototype

Once prototype is validated:
1. Add proper authentication (API keys, JWT)
2. Add user management per tenant
3. Add resource limits and monitoring
4. Add production security measures
5. Scale testing with more tenants

This prototype focuses on proving the core tenant isolation and RAG functionality works correctly before adding complexity.
