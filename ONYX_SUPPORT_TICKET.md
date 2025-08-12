# 🎫 Onyx Cloud Support Ticket - Document Indexing Pipeline Issue

## 🚨 **Issue Summary**
Documents upload successfully via the file upload API but never complete the indexing process, remaining permanently in "INDEXING" status and never becoming searchable.

---

## 🔧 **Technical Details**

### **Environment**
- **Platform**: Onyx Cloud (https://cloud.onyx.app)
- **Authentication**: Bearer Token (API Key)
- **API Endpoint Used**: `/api/user/file/upload`
- **Implementation**: Programmatic upload via Python requests

### **API Configuration**
```python
Base URL: https://cloud.onyx.app
Endpoint: /api/user/file/upload
Authentication: Bearer {ONYX_API_KEY}
Content-Type: multipart/form-data
```

---

## 📊 **Evidence of the Issue**

### **Successful Upload Response**
```json
{
  "id": 19,
  "name": "temporal_rag_test_story.md: 📚 Temporal Knowledge Story for RAG Testing.md",
  "document_id": "USER_FILE_CONNECTOR__2a644e91-05d2-495b-884e-8426fbffe4ff",
  "folder_id": -1,
  "user_id": "ed289a04-6977-4d9d-99e1-812714c958e2",
  "file_id": "2a644e91-05d2-495b-884e-8426fbffe4ff",
  "created_at": "2025-08-11T12:18:12.569278",
  "assistant_ids": [],
  "token_count": null,
  "indexed": false,          ← STAYS FALSE PERMANENTLY
  "link_url": null,
  "status": "INDEXING",       ← NEVER CHANGES FROM THIS STATUS
  "chat_file_type": "plain_text"
}
```

### **Affected Document IDs**
- `USER_FILE_CONNECTOR__2a644e91-05d2-495b-884e-8426fbffe4ff` (Temporal story, 2370 chars)
- `USER_FILE_CONNECTOR__97ace4ae-4860-4177-a02a-0fb8baab8654` (Simple test, 253 chars)
- `USER_FILE_CONNECTOR__99afe786-5a11-4680-9052-a034ffcc02d1` (Previous test)

### **File Types Tested**
- ✅ **Markdown files (.md)** - Same issue
- ✅ **Plain text files (.txt)** - Same issue  
- ✅ **Various file sizes** - Same issue across all sizes

---

## 🔍 **Troubleshooting Performed**

### **1. Authentication Verification**
- ✅ Bearer token authentication working correctly
- ✅ API returns 200 status for uploads
- ✅ Valid tenant API key confirmed

### **2. File Format Testing**
```python
# Tested multiple formats
- Markdown with metadata headers
- Plain text without formatting
- Different file sizes (253 chars to 2370 chars)
- Various content types (technical docs, simple text, structured data)
```

### **3. Search Verification**
```python
# Search queries attempted
search_queries = ['Aanya Sharma', 'temporal story', 'OnePlus', 'Simple Test Document']
# Result: ZERO documents found that match our uploaded document IDs
# Existing documents in system are searchable, but not our uploads
```

### **4. API Endpoint Testing**
- ✅ `/api/user/file/upload` - Works, returns success
- ❌ `/api/user/file` (GET) - Returns 404  
- ❌ `/onyx-api/ingestion` (GET) - Returns HTML login page
- ✅ Search functionality - Works for existing docs, not uploaded ones

---

## 📋 **Issue Pattern Analysis**

### **Consistent Behavior Across All Tests:**
1. **Upload Success**: HTTP 200, document ID generated
2. **Indexing Failure**: `"indexed": false` never changes
3. **Status Stuck**: `"status": "INDEXING"` permanently  
4. **Search Failure**: Documents never appear in search results
5. **Token Count**: Always `null`, suggesting processing never completes

### **Timeline Pattern:**
- **Immediate**: Upload succeeds, document appears with INDEXING status
- **10 seconds later**: Status unchanged, still INDEXING
- **Minutes later**: Status unchanged, still INDEXING
- **Hours later**: Status unchanged, still INDEXING

---

## 🔗 **Reference Implementation**

Our implementation follows the file upload pattern and is based on successful API responses. Here's our working upload code:

```python
def upload_document(api_key, content, filename):
    url = "https://cloud.onyx.app/api/user/file/upload"
    headers = {'Authorization': f'Bearer {api_key}'}
    files = {'files': (filename, content, 'text/markdown')}
    
    response = requests.post(url, headers=headers, files=files, timeout=30)
    return response.json()[0] if response.status_code == 200 else None
```

---

## 🎯 **Specific Questions for Support**

1. **Is there a known issue** with the document indexing pipeline for programmatically uploaded files?

2. **What is the expected timeline** for documents to move from "INDEXING" to "indexed: true"?

3. **Are there specific requirements** for programmatically uploaded files that differ from UI uploads?

4. **Is the `/api/user/file/upload` endpoint** the correct approach for programmatic document ingestion?

5. **Are there any tenant-specific settings** that need to be configured for API-uploaded documents to be indexed?

6. **Is there a way to check indexing queue status** or force re-indexing of stuck documents?

---

## 📞 **Account Information**

- **Tenant ID**: [Your tenant ID from API key]  
- **API Key Prefix**: `on_tenant_f77e9e8b...`
- **User ID**: `ed289a04-6977-4d9d-99e1-812714c958e2`
- **Upload Method**: Programmatic via API
- **Issue Duration**: Consistent across multiple days of testing

---

## 🔄 **Requested Action**

Please investigate the document indexing pipeline for our tenant. The upload mechanism is working correctly, but the indexing process appears to be stuck or non-functional for API-uploaded documents.

**Priority**: High - This is blocking our production implementation of Onyx Cloud integration.

**Expected Outcome**: Documents uploaded via API should complete indexing and become searchable within a reasonable timeframe.

---

## 📎 **Additional Context**

We're implementing a hybrid RAG system that combines Onyx Cloud with local knowledge graphs. The Onyx Cloud integration is a critical component, and this indexing issue is preventing us from completing our implementation.

Our local storage components (PostgreSQL + Neo4j) are working correctly with the same documents, confirming that our document processing and formatting is sound.

Thank you for your assistance in resolving this indexing pipeline issue.