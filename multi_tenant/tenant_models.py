"""
Pydantic models for multi-tenant Local Path: Dual Storage system.

All models inherit from TenantAware base class to ensure tenant isolation
is enforced at the data validation layer.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class TenantStatus(str, Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SearchType(str, Enum):
    """Search type enumeration for Local Path: Dual Storage."""
    VECTOR = "vector"
    GRAPH = "graph"
    HYBRID = "hybrid"
    LOCAL_DUAL = "local_dual"  # Default for tenant queries


class TenantAware(BaseModel):
    """
    Base class for all tenant-aware models.
    
    Ensures every data structure includes tenant_id for complete isolation.
    """
    tenant_id: str = Field(
        ..., 
        description="Tenant identifier for data isolation",
        min_length=3,
        max_length=50
    )
    
    @validator('tenant_id')
    def validate_tenant_id(cls, v):
        """Validate tenant ID format."""
        if not v or not isinstance(v, str):
            raise ValueError("tenant_id must be a non-empty string")
        
        # Basic tenant ID format validation (alphanumeric + underscores)
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("tenant_id must contain only alphanumeric characters, underscores, and hyphens")
        
        return v.lower()  # Normalize to lowercase


# Tenant Management Models

class TenantConfig(BaseModel):
    """Tenant configuration and metadata."""
    id: str = Field(..., description="Unique tenant identifier")
    name: str = Field(..., description="Human-readable tenant name", max_length=255)
    status: TenantStatus = Field(default=TenantStatus.ACTIVE, description="Tenant status")
    max_documents: int = Field(default=1000, description="Maximum documents allowed", ge=1)
    max_storage_mb: int = Field(default=500, description="Maximum storage in MB", ge=1)
    max_chunks_per_document: int = Field(default=100, description="Maximum chunks per document", ge=1)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional tenant metadata")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('id')
    def validate_id(cls, v):
        """Validate tenant ID format."""
        if not v or not isinstance(v, str):
            raise ValueError("id must be a non-empty string")
        return v.lower()


class TenantUsage(TenantAware):
    """Tenant resource usage statistics."""
    documents_count: int = Field(default=0, description="Number of documents")
    chunks_count: int = Field(default=0, description="Number of chunks")
    storage_mb: float = Field(default=0.0, description="Storage used in MB")
    entities_count: int = Field(default=0, description="Number of graph entities")
    relationships_count: int = Field(default=0, description="Number of graph relationships")
    active_sessions: int = Field(default=0, description="Number of active sessions")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")


# Document and Content Models

class Document(TenantAware):
    """Document model with tenant isolation."""
    id: Optional[str] = Field(default=None, description="Document unique identifier")
    title: str = Field(..., description="Document title", max_length=500)
    source: str = Field(..., description="Document source path or URL", max_length=1000)
    content: str = Field(..., description="Document content", min_length=1)
    content_type: str = Field(default="text/markdown", description="MIME type of content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('id', pre=True, always=True)
    def set_id(cls, v):
        """Set document ID if not provided."""
        return v or f"doc_{uuid.uuid4().hex[:16]}"
    
    @validator('content')
    def validate_content_length(cls, v):
        """Validate content is not too long."""
        max_length = 1_000_000  # 1MB text limit
        if len(v) > max_length:
            raise ValueError(f"Content too long. Maximum {max_length} characters allowed.")
        return v


class Chunk(TenantAware):
    """Chunk model with tenant isolation and vector embedding."""
    id: Optional[str] = Field(default=None, description="Chunk unique identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk content", min_length=1)
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")
    chunk_index: int = Field(..., description="Chunk index within document", ge=0)
    token_count: Optional[int] = Field(default=None, description="Token count estimate")
    char_start: Optional[int] = Field(default=None, description="Start character position in document")
    char_end: Optional[int] = Field(default=None, description="End character position in document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('id', pre=True, always=True)
    def set_id(cls, v):
        """Set chunk ID if not provided."""
        return v or f"chunk_{uuid.uuid4().hex[:16]}"
    
    @validator('embedding')
    def validate_embedding(cls, v):
        """Validate embedding dimensions."""
        if v is not None:
            expected_dim = 768  # OpenAI/Gemini embedding dimension
            if len(v) != expected_dim:
                raise ValueError(f"Embedding must have {expected_dim} dimensions, got {len(v)}")
        return v


# Session and Authentication Models

class TenantSession(TenantAware):
    """Session model with tenant context."""
    id: Optional[str] = Field(default=None, description="Session unique identifier")
    user_id: str = Field(..., description="User identifier", max_length=100)
    expires_at: datetime = Field(..., description="Session expiration time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('id', pre=True, always=True)
    def set_id(cls, v):
        """Set session ID if not provided."""
        return v or f"session_{uuid.uuid4().hex[:16]}"
    
    @validator('expires_at')
    def validate_expires_at(cls, v):
        """Ensure session expiration is in the future."""
        if v <= datetime.now(timezone.utc):
            raise ValueError("Session expiration must be in the future")
        return v


class AuthToken(TenantAware):
    """JWT token model with tenant claims."""
    user_id: str = Field(..., description="User identifier")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    session_id: Optional[str] = Field(default=None, description="Associated session ID")
    expires_at: datetime = Field(..., description="Token expiration")
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Search and Query Models

class BaseSearchInput(TenantAware):
    """Base search input with tenant context."""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    limit: int = Field(default=10, description="Maximum results to return", ge=1, le=50)
    
    @validator('query')
    def validate_query(cls, v):
        """Basic query validation."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class VectorSearchInput(BaseSearchInput):
    """Vector search input with tenant isolation."""
    threshold: float = Field(default=0.7, description="Similarity threshold", ge=0.0, le=1.0)
    include_metadata: bool = Field(default=True, description="Include chunk metadata in results")


class GraphSearchInput(BaseSearchInput):
    """Graph search input with tenant isolation."""
    search_type: str = Field(default="similarity", description="Type of graph search")
    entity_types: Optional[List[str]] = Field(default=None, description="Filter by entity types")
    include_relationships: bool = Field(default=True, description="Include relationship information")
    max_depth: int = Field(default=3, description="Maximum relationship depth", ge=1, le=5)


class LocalDualSearchInput(BaseSearchInput):
    """Local Path: Dual Storage search input."""
    use_vector: bool = Field(default=True, description="Enable vector search")
    use_graph: bool = Field(default=True, description="Enable graph search")
    vector_weight: float = Field(default=0.6, description="Vector vs graph result weight", ge=0.0, le=1.0)
    vector_threshold: float = Field(default=0.7, description="Vector similarity threshold", ge=0.0, le=1.0)
    
    @validator('use_vector', 'use_graph')
    def validate_search_enabled(cls, v, values):
        """Ensure at least one search type is enabled."""
        if 'use_vector' in values and not values['use_vector'] and not v:
            raise ValueError("At least one search type (vector or graph) must be enabled")
        return v


# API Request and Response Models

class ChatRequest(BaseModel):
    """Chat request with tenant context."""
    message: str = Field(..., description="User message", min_length=1, max_length=5000)
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: str = Field(default="api_user", description="User identifier")
    search_type: SearchType = Field(default=SearchType.LOCAL_DUAL, description="Search type to use")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Request metadata")


class SearchResult(BaseModel):
    """Individual search result."""
    id: str = Field(..., description="Result identifier")
    content: str = Field(..., description="Result content")
    source: str = Field(..., description="Source identifier")
    score: float = Field(..., description="Relevance score", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Result metadata")
    result_type: str = Field(..., description="Type of result (chunk, entity, fact)")


class ChatResponse(BaseModel):
    """Chat response with tenant context."""
    response: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    tools_used: List[str] = Field(default_factory=list, description="Tools used in response")
    sources: List[SearchResult] = Field(default_factory=list, description="Information sources")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    confidence: float = Field(default=0.5, description="Response confidence score", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")


# Health and System Models

class SystemHealth(BaseModel):
    """System health status."""
    status: str = Field(..., description="Overall system status")
    systems: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Individual system status")
    agent_ready: bool = Field(..., description="AI agent readiness")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TenantHealth(TenantAware):
    """Tenant-specific health status."""
    status: str = Field(..., description="Tenant health status")
    database_status: str = Field(..., description="Database connectivity")
    graph_status: str = Field(..., description="Graph database connectivity") 
    document_count: int = Field(default=0, description="Number of documents")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")
    errors: List[str] = Field(default_factory=list, description="Recent errors")


# Graph-specific Models

class GraphEntity(TenantAware):
    """Graph entity with tenant isolation."""
    uuid: Optional[str] = Field(default=None, description="Entity UUID")
    name: str = Field(..., description="Entity name", max_length=200)
    entity_type: str = Field(..., description="Entity type", max_length=50)
    properties: Dict[str, Any] = Field(default_factory=dict, description="Entity properties")
    summary: Optional[str] = Field(default=None, description="Entity summary")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('uuid', pre=True, always=True)
    def set_uuid(cls, v):
        """Set entity UUID if not provided."""
        return v or f"entity_{uuid.uuid4().hex[:16]}"


class GraphRelationship(TenantAware):
    """Graph relationship with tenant isolation."""
    uuid: Optional[str] = Field(default=None, description="Relationship UUID")
    source_entity_uuid: str = Field(..., description="Source entity UUID")
    target_entity_uuid: str = Field(..., description="Target entity UUID")
    relationship_type: str = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")
    summary: Optional[str] = Field(default=None, description="Relationship summary")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('uuid', pre=True, always=True)
    def set_uuid(cls, v):
        """Set relationship UUID if not provided."""
        return v or f"rel_{uuid.uuid4().hex[:16]}"


class GraphFact(TenantAware):
    """Graph fact with tenant context."""
    uuid: Optional[str] = Field(default=None, description="Fact UUID")
    fact: str = Field(..., description="Fact statement", max_length=1000)
    entity_uuids: List[str] = Field(default_factory=list, description="Related entity UUIDs")
    valid_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    invalid_at: Optional[datetime] = Field(default=None, description="Fact invalidation time")
    confidence: float = Field(default=1.0, description="Fact confidence score", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Fact metadata")
    
    @validator('uuid', pre=True, always=True)
    def set_uuid(cls, v):
        """Set fact UUID if not provided."""
        return v or f"fact_{uuid.uuid4().hex[:16]}"


class Episode(TenantAware):
    """Episode (document) processed by Graphiti."""
    uuid: Optional[str] = Field(default=None, description="Episode UUID")
    name: str = Field(..., description="Episode name", max_length=200)
    content: str = Field(..., description="Episode content")
    source_description: str = Field(..., description="Source description")
    reference_time: datetime = Field(..., description="Reference timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Episode metadata")
    entities_extracted: int = Field(default=0, description="Number of entities extracted")
    relationships_extracted: int = Field(default=0, description="Number of relationships extracted")
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time")
    
    @validator('uuid', pre=True, always=True)
    def set_uuid(cls, v):
        """Set episode UUID if not provided."""
        return v or f"episode_{uuid.uuid4().hex[:16]}"


# Ingestion and Processing Models

class IngestionRequest(TenantAware):
    """Document ingestion request."""
    source: str = Field(..., description="Document source", max_length=1000)
    content: str = Field(..., description="Document content", min_length=1)
    title: Optional[str] = Field(default=None, description="Document title")
    content_type: str = Field(default="text/markdown", description="Content MIME type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    extract_entities: bool = Field(default=True, description="Extract entities to knowledge graph")
    chunk_size: int = Field(default=512, description="Chunk size for splitting", ge=100, le=2048)
    chunk_overlap: int = Field(default=50, description="Chunk overlap size", ge=0, le=200)


class IngestionResult(TenantAware):
    """Document ingestion result."""
    document_id: str = Field(..., description="Created document ID")
    chunks_created: int = Field(default=0, description="Number of chunks created")
    entities_extracted: int = Field(default=0, description="Number of entities extracted")
    relationships_extracted: int = Field(default=0, description="Number of relationships extracted")
    processing_time_ms: float = Field(..., description="Total processing time")
    success: bool = Field(..., description="Ingestion success status")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Result metadata")


# Validation and Utility Functions

def validate_tenant_context(data: Dict[str, Any], expected_tenant_id: str) -> bool:
    """
    Validate that data belongs to expected tenant.
    
    Args:
        data: Dictionary containing tenant_id
        expected_tenant_id: Expected tenant identifier
        
    Returns:
        True if tenant context is valid
        
    Raises:
        ValueError: If tenant context is invalid
    """
    data_tenant_id = data.get('tenant_id')
    if not data_tenant_id:
        raise ValueError("Missing tenant_id in data")
    
    if data_tenant_id != expected_tenant_id:
        raise ValueError(f"Tenant mismatch: expected {expected_tenant_id}, got {data_tenant_id}")
    
    return True


def extract_tenant_id(model: TenantAware) -> str:
    """Extract tenant ID from tenant-aware model."""
    return model.tenant_id


# Model Registry for Dynamic Loading
TENANT_MODELS = {
    'tenant_config': TenantConfig,
    'tenant_usage': TenantUsage,
    'document': Document,
    'chunk': Chunk,
    'session': TenantSession,
    'auth_token': AuthToken,
    'vector_search_input': VectorSearchInput,
    'graph_search_input': GraphSearchInput,
    'local_dual_search_input': LocalDualSearchInput,
    'chat_request': ChatRequest,
    'chat_response': ChatResponse,
    'search_result': SearchResult,
    'system_health': SystemHealth,
    'tenant_health': TenantHealth,
    'graph_entity': GraphEntity,
    'graph_relationship': GraphRelationship,
    'graph_fact': GraphFact,
    'episode': Episode,
    'ingestion_request': IngestionRequest,
    'ingestion_result': IngestionResult
}


def get_model_by_name(model_name: str) -> BaseModel:
    """Get model class by name."""
    if model_name not in TENANT_MODELS:
        raise ValueError(f"Unknown model: {model_name}")
    return TENANT_MODELS[model_name]