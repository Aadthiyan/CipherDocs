# API Documentation - CipherDocs

## Overview

CipherDocs provides a comprehensive REST API built with FastAPI. All endpoints return JSON responses and require authentication via JWT tokens (except public endpoints).

**Base URL**: `http://localhost:8000/api`  
**API Version**: 1.0  
**Authentication**: Bearer Token (JWT)

---

## Authentication

### Getting a Token

All protected endpoints require a JWT bearer token. Obtain a token by logging in.

**Endpoint**: `POST /api/auth/login`

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using the Token

Include the token in the `Authorization` header:

```bash
curl -X GET http://localhost:8000/api/documents \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Endpoints

### Authentication

#### Sign Up
**POST** `/auth/signup`

Create a new user account.

**Request**:
```json
{
  "email": "newuser@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newuser@example.com",
  "full_name": "John Doe",
  "created_at": "2025-12-16T10:30:00Z"
}
```

**Error Codes**:
- `400`: Invalid email format or weak password
- `409`: Email already registered

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "Jane Smith"
  }'
```

---

#### Login
**POST** `/auth/login`

Authenticate user and get JWT tokens.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Codes**:
- `401`: Invalid credentials
- `400`: Missing email or password

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password"
  }' | jq '.access_token' -r
```

---

#### Refresh Token
**POST** `/auth/refresh`

Get a new access token using refresh token.

**Request Headers**:
```
Authorization: Bearer YOUR_REFRESH_TOKEN
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Codes**:
- `401`: Invalid or expired refresh token

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

---

#### Logout
**POST** `/auth/logout`

Invalidate current session.

**Request Headers**:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### Documents

#### List Documents
**GET** `/documents`

Retrieve all documents accessible to the current user.

**Query Parameters**:
- `skip` (int, optional): Number of documents to skip (default: 0)
- `limit` (int, optional): Maximum documents to return (default: 10, max: 100)
- `status` (string, optional): Filter by status (pending, processing, completed, failed)

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "report.pdf",
      "file_size_bytes": 1024000,
      "status": "completed",
      "created_at": "2025-12-16T10:30:00Z",
      "updated_at": "2025-12-16T10:35:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/documents?limit=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

#### Upload Document
**POST** `/documents/upload`

Upload and process a new document.

**Request**:
- Content-Type: `multipart/form-data`
- File parameter: `file` (PDF, TXT, DOCX)

**Response** (202 Accepted):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "report.pdf",
  "file_size_bytes": 1024000,
  "status": "processing",
  "created_at": "2025-12-16T10:30:00Z"
}
```

**Error Codes**:
- `400`: Invalid file type or size
- `413`: File too large
- `422`: Processing error

**Example**:
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@report.pdf"
```

---

#### Get Document
**GET** `/documents/{document_id}`

Retrieve document details.

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "report.pdf",
  "file_size_bytes": 1024000,
  "status": "completed",
  "doc_type": "application/pdf",
  "chunk_count": 25,
  "created_at": "2025-12-16T10:30:00Z",
  "updated_at": "2025-12-16T10:35:00Z"
}
```

**Error Codes**:
- `404`: Document not found
- `403`: Access denied

**Example**:
```bash
curl -X GET http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

#### Delete Document
**DELETE** `/documents/{document_id}`

Delete a document (GDPR compliant deletion).

**Response** (204 No Content)

**Error Codes**:
- `404`: Document not found
- `403`: Access denied

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### Search

#### Search Documents
**POST** `/search`

Search documents using semantic search.

**Request**:
```json
{
  "query": "machine learning algorithms",
  "top_k": 10,
  "threshold": 0.5
}
```

**Response** (200 OK):
```json
{
  "query": "machine learning algorithms",
  "results": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "report.pdf",
      "chunk_id": "chunk_001",
      "text": "Machine learning is a subset of artificial intelligence...",
      "similarity_score": 0.92,
      "chunk_sequence": 5
    },
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440001",
      "filename": "guide.pdf",
      "chunk_id": "chunk_002",
      "text": "Algorithm optimization improves learning speed...",
      "similarity_score": 0.87,
      "chunk_sequence": 12
    }
  ],
  "execution_time_ms": 145
}
```

**Parameters**:
- `query` (string, required): Search query
- `top_k` (int, optional): Number of results (default: 10, max: 100)
- `threshold` (float, optional): Minimum similarity score (0-1, default: 0.5)

**Error Codes**:
- `400`: Invalid query or parameters
- `422`: Query processing error

**Example**:
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "encryption algorithms",
    "top_k": 5,
    "threshold": 0.7
  }'
```

---

### Analytics

#### Get Analytics
**GET** `/analytics`

Retrieve platform analytics and statistics.

**Response** (200 OK):
```json
{
  "total_documents": 150,
  "total_chunks": 3500,
  "total_searches": 12500,
  "avg_search_latency_ms": 145,
  "total_storage_gb": 2.5,
  "period": "last_30_days",
  "summary": {
    "documents_uploaded": 12,
    "searches_performed": 850,
    "avg_similarity_score": 0.78
  }
}
```

**Query Parameters**:
- `period` (string, optional): Time period (last_day, last_7_days, last_30_days, all)

**Example**:
```bash
curl -X GET "http://localhost:8000/api/analytics?period=last_7_days" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-12-16T10:30:00Z"
}
```

### Common Error Codes

| Code | Status | Meaning |
|------|--------|---------|
| `INVALID_CREDENTIALS` | 401 | Email or password incorrect |
| `TOKEN_EXPIRED` | 401 | JWT token has expired |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permissions |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `INVALID_REQUEST` | 400 | Request validation failed |
| `TENANT_ISOLATION_VIOLATION` | 403 | Cross-tenant access attempt |
| `PROCESSING_ERROR` | 422 | Document processing failed |
| `STORAGE_QUOTA_EXCEEDED` | 409 | Storage limit reached |

---

## OpenAPI/Swagger UI

Access interactive API documentation at:

```
http://localhost:8000/docs
```

This provides:
- ✅ Interactive endpoint testing
- ✅ Automatic schema validation
- ✅ Request/response examples
- ✅ Real-time API exploration

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Authentication**: 5 requests per minute
- **Search**: 100 requests per minute
- **Upload**: 10 requests per minute
- **General**: 1000 requests per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702728600
```

---

## Pagination

List endpoints support cursor-based pagination:

```bash
curl -X GET "http://localhost:8000/api/documents?skip=20&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Request Headers

All requests should include:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
User-Agent: MyApp/1.0
```

---

## Response Headers

All responses include:

```
Content-Type: application/json
X-Request-ID: unique-request-id
X-Response-Time: 145ms
```

---

## API Versioning

The API uses URL-based versioning:
- Current version: `/api/v1` (implicit, default)
- Legacy support: `/api/v1` (backwards compatible)

---

## Security Considerations

✅ **All endpoints require authentication** (except signup/login)  
✅ **Responses are always encrypted** via HTTPS  
✅ **API keys are never logged** in audit trails  
✅ **Rate limiting** prevents brute force attacks  
✅ **CORS** configured for specified origins only  

---

## Example Workflows

### Complete Search Workflow

```bash
# 1. Sign up (if new user)
SIGNUP_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "Jane Smith"
  }')

# 2. Login
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

# 3. Upload document
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf")

DOC_ID=$(echo $UPLOAD_RESPONSE | jq -r '.id')

# 4. Wait for processing (poll status)
sleep 5

# 5. Search documents
curl -s -X POST http://localhost:8000/api/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your search query",
    "top_k": 5
  }' | jq '.'

# 6. Logout
curl -s -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

---

## Support

For API issues:
1. Check the [Deployment Guide](DEPLOYMENT_GUIDE.md)
2. Review [Troubleshooting](DEPLOYMENT_GUIDE.md#troubleshooting)
3. Check application logs: `docker logs cyborgdb_backend`
4. Open an issue on GitHub

---

**Last Updated**: December 16, 2025  
**API Version**: 1.0  
**Status**: ✅ Complete
