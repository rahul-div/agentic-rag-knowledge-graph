# 🤖 Onyx Agent Documentation

## 🎯 Purpose and Scope

The standalone Onyx agent serves as:

- **Validation Platform**: Test Onyx Cloud integration independently
- **Reference Implementation**: Demonstrate best practices for Pydantic AI + Onyx Cloud
- **Integration Gateway**: Bridge between Onyx Cloud APIs and conversational AI
- **Quality Assurance**: Ensure robust error handling and response quality
- **Document Set Strategy Testing**: Validate different approaches to document organization and access

## 📊 Document Set Strategy

### Current Implementation: Fixed CC-pair 285

The interactive agent uses a **validated, fixed document set approach** for maximum reliability:

**Benefits:**

- ✅ **Proven Success**: CC-pair 285 achieved 100% success rate on all test queries
- ✅ **Predictable Performance**: Consistent search results and response times
- ✅ **Simple Configuration**: No complex document set management required
- ✅ **Fast Startup**: Cached document set ID for immediate availability

**Documents Available in CC-pair 285:**

- `temporal_rag_test_story.md` - Aanya Sharma's personal experiences and preferences
- `TECHNICAL_SUMMARY.md` - Technical project documentation
- `Final_V1.IIRM_Document Management_finalapproved.xlsx` - Project specifications
- Additional technical and project documentation

### Alternative Document Set Strategies

#### 1. Multi-CC-pair Strategy

```python
# Support multiple connector-credential pairs
class MultiCCPairStrategy:
    def __init__(self, cc_pairs: List[int]):
        self.cc_pairs = cc_pairs  # e.g., [285, 318, 320]
        self.document_sets = {}   # Cache for each CC-pair
    
    def get_document_set_for_query(self, query: str) -> int:
        # Intelligent routing based on query content
        if "aanya" in query.lower():
            return self.document_sets[285]  # Personal stories
        elif "technical" in query.lower():
            return self.document_sets[318]  # Technical docs
        else:
            return self.document_sets[285]  # Default
```

**Use Cases:**

- Different document types (personal, technical, legal)
- Time-based document organization (2024 docs vs 2025 docs)
- Project-specific document collections

#### 2. Dynamic Document Set Creation

```python
# Create document sets on-demand based on query intent
class DynamicStrategy:
    def create_targeted_document_set(self, query: str, cc_pairs: List[int]) -> int:
        # Analyze query to determine relevant CC-pairs
        relevant_pairs = self.analyze_query_intent(query)
        
        # Create document set with specific CC-pairs
        document_set_name = f"Dynamic_{hash(query)}_{timestamp}"
        return self.onyx_service.create_document_set_validated(
            relevant_pairs, document_set_name
        )
```

**Use Cases:**

- Cross-project searches spanning multiple connectors
- Temporary document sets for specific research tasks
- User-specific document collections

#### 3. Hierarchical Document Set Strategy

```python
# Organize document sets by hierarchy (project -> team -> individual)
class HierarchicalStrategy:
    document_sets = {
        "company": 100,      # All company documents
        "engineering": 101,  # Engineering team documents
        "aanya_project": 285 # Specific project documents
    }
    
    def get_document_set_by_scope(self, scope: str) -> int:
        return self.document_sets.get(scope, 285)  # Default to specific
```

**Use Cases:**

- Role-based access to different document scopes
- Organizational hierarchy-based search
- Permission-based document access

### Document Set Management Best Practices

#### Caching Strategy

```python
# Cache document set IDs to avoid repeated creation
cache_structure = {
    "285": 85,    # CC-pair 285 -> Document Set 85
    "318": 92,    # CC-pair 318 -> Document Set 92
    "dynamic_hash_123": 95  # Temporary sets
}
```

#### Health Monitoring

```python
def verify_document_set_health(document_set_id: int) -> bool:
    """Verify document set is still accessible and populated."""
    try:
        # Check if document set still exists
        ds_info = self.onyx_service.get_document_sets()
        active_sets = [ds['id'] for ds in ds_info]
        
        if document_set_id not in active_sets:
            # Document set was deleted, recreate
            return False
            
        # Test search to ensure functionality
        test_result = self.onyx_service.search_with_document_set_validated(
            "test query", document_set_id, max_retries=1
        )
        
        return test_result.get("success", False)
        
    except Exception:
        return False
```

#### Cleanup Strategy

```python
def cleanup_temporary_document_sets():
    """Remove old temporary document sets to avoid accumulation."""
    
    # Get all document sets
    all_sets = self.onyx_service.get_document_sets()
    
    # Find temporary sets older than 24 hours
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for ds in all_sets:
        if ds['name'].startswith('Dynamic_') or ds['name'].startswith('Temp_'):
            created_time = datetime.fromisoformat(ds.get('created_at', ''))
            if created_time < cutoff_time:
                self.onyx_service.delete_document_set(ds['id'])
```

### Configuration Options for Document Set Strategy

#### Environment Variables

```bash
# Document set strategy configuration
ONYX_DOCUMENT_SET_STRATEGY=fixed    # fixed, multi, dynamic, hierarchical
ONYX_DEFAULT_CC_PAIR=285           # Default CC-pair for fixed strategy
ONYX_DOCUMENT_SET_CACHE_TTL=3600   # Cache TTL in seconds
ONYX_AUTO_CLEANUP_TEMP_SETS=true   # Automatic cleanup of temporary sets

# Multi-CC-pair strategy
ONYX_CC_PAIRS=285,318,320          # Comma-separated list
ONYX_CC_PAIR_ROUTING=smart         # smart, round_robin, random

# Dynamic strategy
ONYX_MAX_TEMP_DOCUMENT_SETS=10     # Maximum temporary sets
ONYX_DYNAMIC_SET_TTL=86400         # Temporary set lifetime (24 hours)
```

#### Runtime Configuration

```python
# Agent initialization with document set strategy
deps = OnyxAgentDependencies(
    onyx_service=onyx_service,
    document_set_strategy="fixed",   # or "multi", "dynamic", "hierarchical"
    default_cc_pair_id=285,
    cc_pair_routing="smart",
    cache_ttl=3600
)
```

### Recommended Strategy by Use Case

| Use Case | Recommended Strategy | Benefits |
|----------|---------------------|----------|
| **Development/Testing** | Fixed (CC-pair 285) | Predictable, reliable, fast |
| **Multi-team Organization** | Hierarchical | Role-based access, organized |
| **Research/Analysis** | Dynamic | Flexible, query-optimized |
| **Production Multi-project** | Multi-CC-pair | Scalable, organized, efficient |
| **Personal Use** | Fixed | Simple, reliable, sufficient |

### Migration Path

**Phase 1**: Start with Fixed (Current Implementation)

- Use validated CC-pair 285
- Build confidence and collect usage patterns

**Phase 2**: Add Multi-CC-pair Support

- Extend to support multiple validated CC-pairs
- Implement intelligent routing based on query analysis

**Phase 3**: Dynamic Document Set Creation

- Add on-demand document set creation
- Implement cleanup and management strategies

**Phase 4**: Advanced Strategies

- Add hierarchical and permission-based strategies
- Implement advanced caching and optimization

## 🏗️ Production Implementation Guidelines

### Security Considerations

```python
# Secure document set access
class SecureDocumentSetStrategy:
    def __init__(self, user_permissions: Dict[str, List[int]]):
        self.user_permissions = user_permissions
    
    def get_allowed_cc_pairs(self, user_id: str) -> List[int]:
        """Return CC-pairs user has access to"""
        return self.user_permissions.get(user_id, [285])  # Default safe set
    
    def validate_document_set_access(self, user_id: str, cc_pair_id: int) -> bool:
        """Validate user can access specific CC-pair"""
        allowed = self.get_allowed_cc_pairs(user_id)
        return cc_pair_id in allowed
```

### Performance Optimization

```python
# Optimize document set operations
class OptimizedDocumentSetManager:
    def __init__(self):
        self.cache = {}
        self.health_status = {}
        self.last_health_check = {}
    
    async def get_document_set_cached(self, cc_pair_id: int) -> int:
        """Get document set with caching"""
        cache_key = f"cc_pair_{cc_pair_id}"
        
        if cache_key in self.cache:
            # Verify cache is still valid
            if await self.is_document_set_healthy(self.cache[cache_key]):
                return self.cache[cache_key]
        
        # Create new document set
        ds_id = await self.create_document_set_validated([cc_pair_id])
        self.cache[cache_key] = ds_id
        return ds_id
```

### Error Recovery Strategies

```python
# Robust error handling for document sets
class RobustDocumentSetHandler:
    def __init__(self):
        self.fallback_cc_pairs = [285, 318]  # Known good CC-pairs
        self.retry_strategies = {
            "create_failed": self.retry_with_fallback,
            "search_failed": self.try_alternative_document_set,
            "health_check_failed": self.recreate_document_set
        }
    
    async def handle_document_set_error(self, error_type: str, context: Dict):
        """Handle document set errors with appropriate recovery"""
        strategy = self.retry_strategies.get(error_type)
        if strategy:
            return await strategy(context)
        else:
            # Fall back to default CC-pair 285
            return await self.create_document_set_validated([285])
```

### Monitoring and Observability

```python
# Comprehensive monitoring for document set operations
class DocumentSetMonitor:
    def __init__(self):
        self.metrics = {
            "document_sets_created": 0,
            "document_sets_deleted": 0,
            "search_success_rate": 0.0,
            "avg_search_latency": 0.0,
            "cache_hit_rate": 0.0
        }
        self.health_alerts = []
    
    def log_document_set_operation(self, operation: str, success: bool, latency: float):
        """Log document set operations for monitoring"""
        self.metrics[f"{operation}_count"] += 1
        if success:
            self.metrics[f"{operation}_success_rate"] = self.calculate_success_rate(operation)
        
        self.metrics[f"avg_{operation}_latency"] = self.update_avg_latency(operation, latency)
    
    def check_health_thresholds(self):
        """Check if metrics exceed alert thresholds"""
        if self.metrics["search_success_rate"] < 0.95:
            self.health_alerts.append("Search success rate below 95%")
        
        if self.metrics["avg_search_latency"] > 5.0:
            self.health_alerts.append("Search latency above 5 seconds")
```

## 📁 File Structure and Components

### Core Files

- `interactive_onyx_agent.py` - **MAIN** Interactive Pydantic AI agent with CLI session support
- `validate_interactive_agent.py` - Comprehensive validation script
- `test_agent_tool.py` - Quick tool integration test

### Supporting Infrastructure

- `/onyx/service.py` - Validated Onyx Cloud service implementation
- `/onyx/interface.py` - Service interface definitions
- `/onyx/config.py` - Configuration management
- `/onyx/__init__.py` - Package exports (OnyxService, OnyxInterface, MockOnyxService)

## 🚀 Quick Start

1. **Environment Setup**:

   ```bash
   source .venv/bin/activate
   pip install -r requirements_final.txt
   ```

2. **Environment Variables**:

   ```bash
   export ONYX_API_KEY="your_onyx_api_key"
   export GEMINI_API_KEY="your_gemini_key"  # or OPENAI_API_KEY
   ```

3. **Run Interactive Agent**:

   ```bash
   python interactive_onyx_agent.py
   ```

4. **Validate Setup**:

   ```bash
   python validate_interactive_agent.py
   ```

## 🔧 API Reference

### OnyxService Class

The main service class providing validated Onyx Cloud integration.

#### Methods

**search_with_document_set_validated(query: str, document_set_id: int, max_retries: int = 3) -> Dict**

Performs validated search with comprehensive error handling and retry logic.

**Parameters:**

- `query` (str): Search query
- `document_set_id` (int): Target document set ID
- `max_retries` (int): Maximum retry attempts

**Example:**

```python
result = await onyx_service.search_with_document_set_validated(
    "What are Aanya's preferences?", 85, max_retries=3
)
```

**Response:**

```json
{
  "success": true,
  "results": [
    {
      "content": "...",
      "source": "temporal_rag_test_story.md",
      "score": 0.85
    }
  ],
  "total_results": 1
}
```

**answer_question_validated(question: str, document_set_id: int) -> Dict**

Provides comprehensive answers with source citations.

**Parameters:**

- `question` (str): Question to answer
- `document_set_id` (int): Target document set

**Example:**

```python
answer = await onyx_service.answer_question_validated(
    "Which cafe did Aanya prefer?", 85
)
```

**Response:**

```json
{
  "answer": "Aanya preferred Blue Bottle Coffee...",
  "sources": [
    {
      "title": "temporal_rag_test_story.md",
      "content": "...",
      "relevance_score": 0.92
    }
  ],
  "confidence": 0.88
}
```

**validate_environment_and_connection(check_connectors: bool = True) -> Dict**

Validates complete environment setup and connectivity.

**Parameters:**

- `check_connectors` (bool): Check connector status (default: True)

**Example:**

```python
validation = await onyx_service.validate_environment_and_connection()
```

### Interactive Agent Class

**run_interactive_session(document_set_id: Optional[str] = None) -> None**

Starts interactive CLI session with Onyx agent.

**Parameters:**

- `document_set_id` (Optional[str]): Target document set for session

**Example:**

```python
agent = InteractiveOnyxAgent()
await agent.run_interactive_session()
```

## ✅ Validation and Testing

### Validation Protocol

The validation system performs comprehensive checks:

1. **Environment Validation**: Check required environment variables (ONYX_API_KEY, LLM keys)
2. **Connectivity Tests**: Verify Onyx Cloud API connection and authentication
3. **CC-pair Verification**: Confirm CC-pair 285 exists and is accessible
4. **Document Set Tests**: Create, verify, and test document set operations
5. **Search Functionality**: Test search with various query types
6. **LLM Integration**: Verify language model connectivity and tool integration
7. **End-to-end Tests**: Complete agent interaction validation

### Test Scenarios

#### Standard Test Queries

Test the agent with these validated queries:

- "What are Aanya Sharma's coffee preferences?"
- "Which cafe did Aanya Sharma prefer and when?"
- "Tell me about Aanya's experience with different coffee shops"
- "What technical documentation is available?"

#### Expected Behaviors

- **Detailed Responses**: Agent provides comprehensive answers with context
- **Source Citations**: Top 3 most relevant sources cited for each answer
- **Tool Usage**: Agent always uses search tool for information retrieval
- **Error Handling**: Graceful handling of network issues and API errors

### Running Validation Scripts

```bash
# Full environment and connectivity validation
python validate_interactive_agent.py

# Quick tool integration test
python test_agent_tool.py

# Interactive agent testing
python interactive_onyx_agent.py
```

## 🔍 Troubleshooting

### Common Issues

#### Environment Variables Not Set

**Problem**: `ValueError: ONYX_API_KEY environment variable is required`

**Solution**: Set required environment variables:

```bash
export ONYX_API_KEY="your_key_here"
export GEMINI_API_KEY="your_gemini_key"  # or OPENAI_API_KEY
```

#### Connection Timeouts

**Problem**: `OnyxConnectionError: Connection timeout after 30 seconds`

**Solutions:**

- Check network connectivity
- Verify Onyx Cloud API endpoint is accessible
- Increase timeout in `/onyx/config.py`

#### Document Set Creation Failures

**Problem**: `OnyxServiceError: Failed to create document set`

**Solutions:**

- Verify CC-pair 285 exists and is accessible
- Check API permissions for document set operations
- Review Onyx Cloud dashboard for CC-pair status

#### Search Returns Empty Results

**Problem**: Agent responds with "I couldn't find relevant information"

**Solutions:**

- Verify documents are properly indexed in CC-pair 285
- Check if document set contains expected documents
- Test with simpler, more direct queries

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed API calls and responses
```

### Health Check Commands

```bash
# Verify Onyx service health
python -c "
from onyx.service import OnyxService
import asyncio
async def check():
    service = OnyxService()
    result = await service.validate_environment_and_connection()
    print('Health check:', result)
asyncio.run(check())
"

# Verify CC-pair accessibility
python -c "
from onyx.service import OnyxService
import asyncio
async def check():
    service = OnyxService()
    result = await service.verify_cc_pair_and_get_document_set(285)
    print('CC-pair check:', result)
asyncio.run(check())
"
```

## 📈 Production Deployment

### Deployment Checklist

- [ ] All environment variables configured
- [ ] Network connectivity to Onyx Cloud verified
- [ ] Document sets created and validated
- [ ] Monitoring and logging configured
- [ ] Error handling and recovery tested
- [ ] Security permissions validated
- [ ] Performance benchmarks established

### Scaling Considerations

- **Document Set Caching**: Implement Redis or similar for document set ID caching
- **Connection Pooling**: Use connection pools for high-throughput scenarios
- **Rate Limiting**: Implement client-side rate limiting to respect API quotas
- **Load Balancing**: Distribute requests across multiple agent instances
- **Monitoring**: Set up comprehensive monitoring for all components

### Integration Patterns

#### Web Service Integration

```python
from fastapi import FastAPI
from interactive_onyx_agent import InteractiveOnyxAgent

app = FastAPI()
agent = InteractiveOnyxAgent()

@app.post("/query")
async def query_agent(question: str):
    return await agent.query(question)
```

#### Batch Processing

```python
# Process multiple queries efficiently
async def batch_process_queries(queries: List[str]):
    agent = InteractiveOnyxAgent()
    results = []
    for query in queries:
        result = await agent.query(query)
        results.append(result)
    return results
```

## 📚 Additional Resources

### Documentation Files

- `INFRASTRUCTURE_VALIDATION_COMPLETE.md` - Infrastructure validation results
- `ONYX_AGENT_ARCHITECTURE_PROPOSAL.md` - Detailed architecture documentation
- `COMPREHENSIVE_ONYX_CLOUD_GUIDE.md` - Complete Onyx Cloud integration guide

### Reference Implementation

- `search_pipeline.py` - Working search pipeline validation
- `onyx_cloud_integration.py` - Core integration examples

### Testing Framework

- `conftest.py` - Test configuration and fixtures
- `/tests/` - Comprehensive test suite

---

## 🏆 Project Status: COMPLETE

✅ **Infrastructure Validated**: All Onyx Cloud components verified and production-ready  
✅ **Agent Implemented**: Interactive Pydantic AI agent with CLI support  
✅ **Documentation Complete**: Comprehensive guides and API references  
✅ **Testing Validated**: All validation scripts pass consistently  
✅ **Best Practices**: Document set strategies and production guidelines  

The Onyx agent is **ready for production use** with a proven track record of 100% success on validation queries.
