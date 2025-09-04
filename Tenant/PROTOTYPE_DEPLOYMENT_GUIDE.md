# Multi-Tenant RAG Prototype Deployment Guide

## 🎯 **Prototype Goal**

Deploy and validate a working 3-4 tenant multi-tenant RAG system using:
- **Neon PostgreSQL** (free tier: 20 projects, 0.5GB/project, 50 CU-hours/project/month)
- **Graphiti + Neo4j** (single instance with namespace isolation)
- **FastAPI** (prototype API layer)

## 📋 **Prerequisites**

### **Accounts Required**
- [x] Neon account (free tier)
- [x] Neo4j Desktop or AuraDB account
- [x] GitHub account (for deployment)
- [x] Railway/Vercel/Render account (for API hosting)

### **Local Development Setup**
- [x] Python 3.11+
- [x] Existing multi-tenant codebase (validated)
- [x] Neo4j Desktop or Docker

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Neon Projects  │    │  Single Neo4j   │
│  (Single Inst.) │    │                  │    │   (Graphiti)    │
│                 │    │ ┌──────────────┐ │    │                 │
│ ┌─────────────┐ │    │ │ Tenant A DB  │ │    │ Namespace A     │
│ │ API Gateway │ │────┤ │ Tenant B DB  │ │────┤ Namespace B     │
│ │ Auth Layer  │ │    │ │ Tenant C DB  │ │    │ Namespace C     │
│ │ Multi-Tenant│ │    │ │ Catalog DB   │ │    │ Namespace D     │
│ └─────────────┘ │    │ └──────────────┘ │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 **Phase 1: Local Prototype Development (Week 1)**

### **Day 1-2: Create Prototype API**

#### **Step 1: Create `prototype_api.py`**

```python
# File: prototype_api.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import os
import uuid
from datetime import datetime

from tenant_manager import TenantManager
from tenant_data_ingestion_service import TenantDataIngestionService
from tenant_graphiti_client import TenantGraphitiClient

app = FastAPI(title="Multi-Tenant RAG Prototype", version="1.0.0")
security = HTTPBearer()

# Initialize services
tenant_manager = TenantManager()
ingestion_service = TenantDataIngestionService()
graphiti_client = TenantGraphitiClient()

# Simple API key storage (for prototype only)
TENANT_API_KEYS = {}

class PrototypeAPI:
    
    @app.post("/api/v1/admin/tenants")
    async def create_tenant(tenant_name: str, admin_key: str = "prototype_admin"):
        """Admin endpoint to create new tenant"""
        if admin_key != "prototype_admin":
            raise HTTPException(status_code=401, detail="Invalid admin key")
            
        try:
            # Use existing tenant_manager
            tenant_id = await tenant_manager.create_tenant(tenant_name)
            
            # Generate API key for tenant
            api_key = str(uuid.uuid4())
            TENANT_API_KEYS[api_key] = tenant_id
            
            return {
                "tenant_id": tenant_id,
                "tenant_name": tenant_name,
                "api_key": api_key,
                "created_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_current_tenant(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Extract tenant from API key"""
        api_key = credentials.credentials
        if api_key not in TENANT_API_KEYS:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return TENANT_API_KEYS[api_key]
    
    @app.post("/api/v1/documents/upload")
    async def upload_documents(
        files: List[UploadFile] = File(...),
        tenant_id: str = Depends(get_current_tenant)
    ):
        """Upload documents for a specific tenant"""
        try:
            results = []
            for file in files:
                # Save uploaded file temporarily
                temp_path = f"/tmp/{tenant_id}_{file.filename}"
                with open(temp_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                # Process document using existing service
                result = await ingestion_service.ingest_document(
                    tenant_id=tenant_id,
                    file_path=temp_path,
                    document_name=file.filename
                )
                results.append(result)
                
                # Clean up temp file
                os.remove(temp_path)
            
            return {"processed_documents": results}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/v1/query")
    async def query_knowledge(
        query: str,
        tenant_id: str = Depends(get_current_tenant)
    ):
        """Query tenant's knowledge base"""
        try:
            # Use existing graphiti client
            response = await graphiti_client.query_tenant_knowledge(
                tenant_id=tenant_id,
                query=query
            )
            
            return {
                "query": query,
                "response": response,
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/tenants/{tenant_id}/status")
    async def get_tenant_status(
        tenant_id_path: str,
        tenant_id: str = Depends(get_current_tenant)
    ):
        """Get tenant status and usage metrics"""
        if tenant_id != tenant_id_path:
            raise HTTPException(status_code=403, detail="Access denied")
            
        try:
            status = await tenant_manager.get_tenant_status(tenant_id)
            return status
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### **Step 2: Create Environment Configuration**

```bash
# File: .env.prototype
# Neon Configuration
NEON_API_KEY=your_neon_api_key_here
NEON_CATALOG_CONNECTION_STRING=postgresql://user:pass@host/catalog_db

# Neo4j Configuration  
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Graphiti Configuration
GRAPHITI_API_KEY=your_graphiti_api_key
OPENAI_API_KEY=your_openai_api_key

# API Configuration
API_ENVIRONMENT=prototype
LOG_LEVEL=DEBUG
```

#### **Step 3: Update Requirements**

```txt
# File: requirements_prototype.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
python-dotenv==1.0.0
httpx==0.25.0
asyncpg==0.29.0
aiofiles==23.2.1

# Existing dependencies
graphiti-core
psycopg2-binary
neo4j
openai
```

### **Day 3-4: Local Testing**

#### **Step 1: Start Local Services**

```bash
# Terminal 1: Start Neo4j Desktop
# Follow Neo4j Desktop installation guide

# Terminal 2: Start API server
cd /path/to/tenant/folder
pip install -r requirements_prototype.txt
python prototype_api.py
```

#### **Step 2: Test API Endpoints**

```python
# File: test_prototype_api.py
import httpx
import asyncio
import json

async def test_prototype_api():
    base_url = "http://localhost:8000"
    
    # Test 1: Create tenants
    print("Creating tenants...")
    tenants = []
    for i in range(3):
        response = await httpx.AsyncClient().post(
            f"{base_url}/api/v1/admin/tenants",
            params={"tenant_name": f"tenant_{i+1}"}
        )
        tenant = response.json()
        tenants.append(tenant)
        print(f"Created: {tenant['tenant_name']} with API key: {tenant['api_key'][:8]}...")
    
    # Test 2: Upload documents
    print("\nUploading documents...")
    for tenant in tenants:
        files = {"files": open("sample_document.txt", "rb")}
        headers = {"Authorization": f"Bearer {tenant['api_key']}"}
        
        response = await httpx.AsyncClient().post(
            f"{base_url}/api/v1/documents/upload",
            files=files,
            headers=headers
        )
        print(f"Upload for {tenant['tenant_name']}: {response.status_code}")
    
    # Test 3: Query knowledge
    print("\nTesting queries...")
    for tenant in tenants:
        headers = {"Authorization": f"Bearer {tenant['api_key']}"}
        response = await httpx.AsyncClient().post(
            f"{base_url}/api/v1/query",
            json={"query": "What is this document about?"},
            headers=headers
        )
        result = response.json()
        print(f"Query for {tenant['tenant_name']}: {result['response'][:100]}...")

if __name__ == "__main__":
    asyncio.run(test_prototype_api())
```

### **Day 5-7: Integration Testing & Bug Fixes**

- Run comprehensive isolation tests
- Fix integration issues between API and existing components
- Optimize response times
- Add error handling and logging

## 🌐 **Phase 2: Neon Deployment (Week 2)**

### **Day 1-2: Neon Project Setup**

#### **Step 1: Create Neon Projects**

```bash
# Install Neon CLI
npm install -g neonctl

# Login to Neon
neonctl auth

# Create projects for prototype
neonctl projects create --name "multitenant-catalog"
neonctl projects create --name "multitenant-tenant-a" 
neonctl projects create --name "multitenant-tenant-b"
neonctl projects create --name "multitenant-tenant-c"

# Get connection strings
neonctl connection-string --project-id <project-id>
```

#### **Step 2: Update Environment for Cloud**

```bash
# File: .env.production
# Update with actual Neon connection strings
NEON_CATALOG_CONNECTION_STRING=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb
TENANT_A_CONNECTION_STRING=postgresql://user:pass@ep-yyy.us-east-2.aws.neon.tech/neondb
TENANT_B_CONNECTION_STRING=postgresql://user:pass@ep-zzz.us-east-2.aws.neon.tech/neondb
TENANT_C_CONNECTION_STRING=postgresql://user:pass@ep-aaa.us-east-2.aws.neon.tech/neondb

# Neo4j AuraDB or use Neo4j Desktop with ngrok for prototype
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_auradb_password
```

### **Day 3-4: Deploy API**

#### **Option A: Railway Deployment**

```yaml
# File: railway.json
{
  "deploy": {
    "startCommand": "uvicorn prototype_api:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}
```

#### **Option B: Render Deployment**

```yaml
# File: render.yaml
services:
  - type: web
    name: multitenant-rag-api
    env: python
    buildCommand: "pip install -r requirements_prototype.txt"
    startCommand: "uvicorn prototype_api:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: NEON_API_KEY
        sync: false
      - key: NEON_CATALOG_CONNECTION_STRING
        sync: false
```

### **Option C: Amazon EC2 Deployment (RECOMMENDED)**

#### **Why EC2 is Better for Your Prototype**

1. **Full Control**: Complete environment control vs serverless limitations
2. **Performance**: Better for document processing and Neo4j operations
3. **Cost Predictable**: ~$35/month vs usage-based pricing surprises
4. **Debugging**: SSH access for troubleshooting
5. **Neo4j Compatible**: Can run Neo4j Docker locally on same instance

#### **EC2 Setup Guide**

##### **Step 1: Launch EC2 Instance**

```bash
# Via AWS Console or CLI
# Instance: t3.medium (2 vCPU, 4GB RAM)
# OS: Ubuntu 22.04 LTS
# Storage: 20GB gp3 SSD
# Security Group: SSH(22), HTTP(80), HTTPS(443), Custom(8000)
```

##### **Step 2: Server Setup**

```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# System updates
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.11 python3.11-venv python3-pip git curl nginx -y

# Install Docker for Neo4j
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
newgrp docker

# Install Node.js for Neon CLI
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g neonctl pm2
```

##### **Step 3: Application Deployment**

```bash
# Clone your repository
cd /home/ubuntu
git clone <your-repo-url> multitenant-rag
cd multitenant-rag/Tenant

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements_prototype.txt

# Setup Neo4j with Docker
docker run -d \
  --name neo4j-prototype \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/prototype123 \
  -v neo4j_data:/data \
  neo4j:5.15

# Wait for Neo4j to start
sleep 30
docker logs neo4j-prototype
```

##### **Step 4: Environment Configuration**

```bash
# Create production environment file
cat > .env.production << 'EOF'
# Neon Configuration (Update with your actual connection strings)
NEON_API_KEY=your_neon_api_key_here
CATALOG_DATABASE_URL=postgresql://user:pass@ep-catalog.us-east-2.aws.neon.tech/neondb
TENANT_A_CONNECTION_STRING=postgresql://user:pass@ep-tenant-a.us-east-2.aws.neon.tech/neondb
TENANT_B_CONNECTION_STRING=postgresql://user:pass@ep-tenant-b.us-east-2.aws.neon.tech/neondb
TENANT_C_CONNECTION_STRING=postgresql://user:pass@ep-tenant-c.us-east-2.aws.neon.tech/neondb

# Neo4j Configuration (Local Docker)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=prototype123

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production

# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here
GRAPHITI_API_KEY=your_graphiti_api_key_here
EOF

# Load environment variables
source .env.production
```

##### **Step 5: Create Neon Projects**

```bash
# Authenticate with Neon
neonctl auth

# Create all required projects
echo "Creating Neon projects..."
CATALOG_PROJECT=$(neonctl projects create --name "prototype-catalog" --output json | jq -r '.project.id')
TENANT_A_PROJECT=$(neonctl projects create --name "prototype-tenant-a" --output json | jq -r '.project.id')
TENANT_B_PROJECT=$(neonctl projects create --name "prototype-tenant-b" --output json | jq -r '.project.id')
TENANT_C_PROJECT=$(neonctl projects create --name "prototype-tenant-c" --output json | jq -r '.project.id')

# Get connection strings
echo "Getting connection strings..."
CATALOG_CONN=$(neonctl connection-string --project-id $CATALOG_PROJECT)
TENANT_A_CONN=$(neonctl connection-string --project-id $TENANT_A_PROJECT)
TENANT_B_CONN=$(neonctl connection-string --project-id $TENANT_B_PROJECT)
TENANT_C_CONN=$(neonctl connection-string --project-id $TENANT_C_PROJECT)

# Update .env file with actual connection strings
sed -i "s|CATALOG_DATABASE_URL=.*|CATALOG_DATABASE_URL=$CATALOG_CONN|" .env.production
sed -i "s|TENANT_A_CONNECTION_STRING=.*|TENANT_A_CONNECTION_STRING=$TENANT_A_CONN|" .env.production
sed -i "s|TENANT_B_CONNECTION_STRING=.*|TENANT_B_CONNECTION_STRING=$TENANT_B_CONN|" .env.production
sed -i "s|TENANT_C_CONNECTION_STRING=.*|TENANT_C_CONNECTION_STRING=$TENANT_C_CONN|" .env.production

echo "Neon projects created successfully!"
```

##### **Step 6: Production Deployment with PM2**

```bash
# Create PM2 ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'multitenant-rag-api',
    script: 'prototype_api.py',
    interpreter: '/home/ubuntu/multitenant-rag/Tenant/venv/bin/python',
    cwd: '/home/ubuntu/multitenant-rag/Tenant',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env_file: '.env.production',
    error_file: '/home/ubuntu/logs/api-error.log',
    out_file: '/home/ubuntu/logs/api-out.log',
    log_file: '/home/ubuntu/logs/api-combined.log',
    time: true
  }]
};
EOF

# Create logs directory
mkdir -p /home/ubuntu/logs

# Start application with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# Check application status
pm2 status
pm2 logs multitenant-rag-api --lines 50
```

##### **Step 7: Nginx Reverse Proxy**

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/multitenant-rag << 'EOF'
server {
    listen 80;
    server_name _;  # Will work with IP or any domain
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle large file uploads
        client_max_body_size 100M;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    
    # API documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    
    # Default route
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/multitenant-rag /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

##### **Step 8: Firewall Configuration**

```bash
# Configure UFW firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (for future SSL)
sudo ufw --force enable

# Check firewall status
sudo ufw status
```

#### **EC2 Testing & Validation**

```bash
# Test local API directly
curl http://localhost:8000/health

# Test through Nginx
curl http://your-ec2-public-ip/health

# Check all services
pm2 status
docker ps
sudo systemctl status nginx

# Monitor logs
pm2 logs multitenant-rag-api
tail -f /home/ubuntu/logs/api-combined.log
```

#### **EC2 Management Commands**

```bash
# Application management
pm2 restart multitenant-rag-api
pm2 stop multitenant-rag-api
pm2 delete multitenant-rag-api

# Database management
docker restart neo4j-prototype
docker logs neo4j-prototype

# System monitoring
htop                    # CPU/Memory usage
df -h                   # Disk usage
free -h                 # Memory usage
sudo systemctl status nginx

# Update application code
cd /home/ubuntu/multitenant-rag
git pull origin main
cd Tenant
source venv/bin/activate
pip install -r requirements_prototype.txt
pm2 restart multitenant-rag-api
```
## 📊 **Phase 3: Validation & Metrics (Week 3)**

### **Performance Testing**

```python
# File: performance_test.py
import asyncio
import httpx
import time
from statistics import mean, median

async def performance_test():
    base_url = "https://your-api-url.railway.app"
    
    # Test concurrent queries
    async def query_test(tenant_api_key, query_num):
        start_time = time.time()
        headers = {"Authorization": f"Bearer {tenant_api_key}"}
        
        response = await httpx.AsyncClient().post(
            f"{base_url}/api/v1/query",
            json={"query": f"Test query number {query_num}"},
            headers=headers
        )
        
        end_time = time.time()
        return {
            "query_num": query_num,
            "status_code": response.status_code,
            "response_time": end_time - start_time
        }
    
    # Run 10 concurrent queries per tenant
    tasks = []
    for tenant_key in ["tenant_1_api_key", "tenant_2_api_key", "tenant_3_api_key"]:
        for i in range(10):
            tasks.append(query_test(tenant_key, i))
    
    results = await asyncio.gather(*tasks)
    
    # Analyze results
    response_times = [r["response_time"] for r in results if r["status_code"] == 200]
    
    print(f"Total queries: {len(results)}")
    print(f"Successful queries: {len(response_times)}")
    print(f"Average response time: {mean(response_times):.3f}s")
    print(f"Median response time: {median(response_times):.3f}s")
    print(f"Max response time: {max(response_times):.3f}s")

if __name__ == "__main__":
    asyncio.run(performance_test())
```

### **Resource Monitoring**

```python
# File: monitor_resources.py
import asyncio
import psycopg2
from datetime import datetime

async def monitor_neon_usage():
    """Monitor Neon project resource usage"""
    
    connection_strings = [
        "TENANT_A_CONNECTION_STRING",
        "TENANT_B_CONNECTION_STRING", 
        "TENANT_C_CONNECTION_STRING",
        "CATALOG_CONNECTION_STRING"
    ]
    
    for conn_str in connection_strings:
        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()
            
            # Check database size
            cursor.execute("SELECT pg_database_size(current_database())")
            size_bytes = cursor.fetchone()[0]
            size_mb = size_bytes / (1024 * 1024)
            
            # Check connection count
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            connections = cursor.fetchone()[0]
            
            print(f"Project: {conn_str[:20]}...")
            print(f"  Size: {size_mb:.2f} MB")
            print(f"  Connections: {connections}")
            print("---")
            
            conn.close()
            
        except Exception as e:
            print(f"Error monitoring {conn_str}: {e}")

if __name__ == "__main__":
    asyncio.run(monitor_neon_usage())
```

## 🎯 **Success Criteria Validation**

### **Technical Checklist**

- [ ] **API Deployment**: FastAPI app deployed and accessible
- [ ] **Tenant Creation**: 3-4 tenants created successfully  
- [ ] **Document Upload**: Files uploaded and processed per tenant
- [ ] **Query Isolation**: Each tenant only sees their own data
- [ ] **Concurrent Operations**: Multiple tenants can operate simultaneously
- [ ] **Response Times**: Queries complete in < 2 seconds
- [ ] **Resource Usage**: Staying within Neon free tier limits

### **Business Validation**

- [ ] **End-to-End Workflow**: Complete tenant onboarding → upload → query cycle works
- [ ] **Data Isolation**: Zero cross-tenant data leakage
- [ ] **Scalability Assessment**: System can handle planned load
- [ ] **Production Readiness**: Clear path to production identified

## 📝 **Documentation & Next Steps**

### **Create Demo Video**

1. **Tenant Creation**: Show API creating new tenant
2. **Document Upload**: Upload different documents to different tenants
3. **Query Testing**: Demonstrate isolated query responses
4. **Concurrent Usage**: Show multiple tenants operating simultaneously

### **Production Planning**

Based on prototype results, document:

1. **Scaling Requirements**: What needs to change for 10+ tenants
2. **Authentication Needs**: Move from API keys to full auth system  
3. **Monitoring Requirements**: Production-grade observability needs
4. **Cost Projections**: Resource usage patterns and cost estimates

### **Phase 4 Roadmap**

- **Authentication & Authorization**: JWT, OAuth, role-based access
- **Self-Service Registration**: Automated tenant onboarding
- **Usage-Based Billing**: Tracking and billing integration
- **Advanced Monitoring**: Prometheus, Grafana, alerting
- **High Availability**: Multi-region, disaster recovery

## 🎉 **Prototype Success = Foundation for Production**

A successful prototype deployment will prove:

1. **Architecture Validity**: Multi-tenant design works at scale
2. **Technology Choices**: Neon + Graphiti combination is viable
3. **Resource Efficiency**: Can operate within reasonable cost bounds
4. **Scalability Path**: Clear understanding of scaling requirements

This prototype becomes the foundation for building a production-ready multi-tenant RAG system.
