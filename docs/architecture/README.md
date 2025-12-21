# CyborgDB Architecture Documentation

## System Architecture Overview

The CyborgDB platform follows a microservices architecture with clear separation of concerns and cryptographic isolation between tenants.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            React Frontend (Port 3000)                 │   │
│  │  - Authentication UI                                  │   │
│  │  - Document Upload/Management                         │   │
│  │  - Search Interface                                   │   │
│  │  - Analytics Dashboard                                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         FastAPI Backend (Port 8000)                   │   │
│  │  - JWT Authentication & Authorization                 │   │
│  │  - Multi-Tenant Isolation Middleware                  │   │
│  │  - Request Routing & Validation                       │   │
│  │  - Rate Limiting & CORS                               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Processing Layer       │  │    Data Layer            │
│  ┌────────────────────┐  │  │  ┌────────────────────┐  │
│  │ Embedding Service  │  │  │  │   PostgreSQL       │  │
│  │  (Port 8001)       │  │  │  │   (Port 5432)      │  │
│  │ - Model Loading    │  │  │  │ - Tenant Metadata  │  │
│  │ - Vector Gen       │  │  │  │ - User Data        │  │
│  │ - Batch Process    │  │  │  │ - Document Chunks  │  │
│  └────────────────────┘  │  │  │ - Search Logs      │  │
│                          │  │  └────────────────────┘  │
│  ┌────────────────────┐  │  │                          │
│  │ Document Processor │  │  │  ┌────────────────────┐  │
│  │ - PDF Extraction   │  │  │  │   Redis (Cache)    │  │
│  │ - Text Chunking    │  │  │  │   (Port 6379)      │  │
│  │ - Preprocessing    │  │  │  │ - Key Cache        │  │
│  └────────────────────┘  │  │  │ - Session Store    │  │
│                          │  │  └────────────────────┘  │
└──────────────────────────┘  └──────────────────────────┘
                │
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                   Encryption Layer                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Tenant-Specific Encryption                    │   │
│  │  - AES-256 Key Generation                             │   │
│  │  - Vector Encryption/Decryption                       │   │
│  │  - Key Management & Rotation                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                │
                │ Encrypted Vectors
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Vector Storage Layer                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              CyborgDB (External)                      │   │
│  │  - Encrypted Vector Storage                           │   │
│  │  - Encrypted Similarity Search                        │   │
│  │  - Per-Tenant Indexes                                 │   │
│  │  - Cryptographic Isolation                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React)
- **Technology**: React 18, TailwindCSS
- **Responsibilities**:
  - User authentication flows
  - Document upload and management
  - Search interface with results display
  - Analytics and metrics visualization
- **Communication**: REST API calls to backend

### 2. Backend (FastAPI)
- **Technology**: FastAPI, Python 3.9+
- **Responsibilities**:
  - JWT authentication and authorization
  - Multi-tenant request scoping
  - API endpoint orchestration
  - Business logic coordination
- **Key Features**:
  - Automatic OpenAPI documentation
  - Async request handling
  - Middleware pipeline for tenant isolation

### 3. Embedding Service
- **Technology**: FastAPI, Hugging Face Transformers
- **Responsibilities**:
  - Load and cache embedding models
  - Generate vector embeddings from text
  - Batch processing for efficiency
- **Model**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)

### 4. Database (PostgreSQL)
- **Schema**:
  - Tenants, Users, Documents
  - Document Chunks, Search Logs
  - Encryption Keys, Sessions
- **Features**:
  - Foreign key constraints for data integrity
  - Indexes for query optimization
  - Triggers for automatic timestamp updates

### 5. CyborgDB
- **Purpose**: Encrypted vector storage and search
- **Key Features**:
  - Encryption-in-use during similarity search
  - Per-tenant index isolation
  - No plaintext vector exposure

## Data Flow Diagrams

### Document Ingestion Flow

```
User Upload → Backend Validation → Storage → Text Extraction
                                                    ↓
                                              Text Chunking
                                                    ↓
                                           Embedding Generation
                                                    ↓
                                          Vector Encryption
                                                    ↓
                                         CyborgDB Insertion
                                                    ↓
                                            Status: Completed
```

### Search Query Flow

```
User Query → Backend Auth → Query Embedding → Encryption
                                                    ↓
                                         CyborgDB Search
                                                    ↓
                                        Encrypted Results
                                                    ↓
                                          Decryption
                                                    ↓
                                      Chunk Text Retrieval
                                                    ↓
                                         Result Ranking
                                                    ↓
                                      Response to User
```

## Security Architecture

### Multi-Tenant Isolation

1. **Database Level**: All queries filtered by `tenant_id`
2. **API Level**: JWT tokens include tenant scope
3. **Vector Level**: Separate CyborgDB indexes per tenant
4. **Encryption Level**: Unique encryption keys per tenant

### Encryption Strategy

- **Key Generation**: 256-bit AES keys per tenant
- **Key Storage**: Encrypted with master key in database
- **Vector Encryption**: Fernet symmetric encryption
- **Key Caching**: Short-lived cache (1-5 minutes)

## Deployment Architecture

### Docker Compose (Development)
- All services in single compose file
- Shared network for inter-service communication
- Volume mounts for persistence
- Health checks for service readiness

### Production (Future)
- Kubernetes orchestration
- Horizontal pod autoscaling
- Load balancing
- Multi-region deployment

## Performance Considerations

### Caching Strategy
- Redis for session storage
- In-memory key cache (short TTL)
- Model weights cached on disk

### Optimization Points
- Batch embedding generation
- Connection pooling (database, HTTP)
- Async processing for document ingestion
- CDN for frontend assets

## Monitoring & Observability

### Metrics Collected
- Request latency (p50, p95, p99)
- Error rates per endpoint
- Search query patterns
- Resource utilization (CPU, memory)

### Logging
- Structured JSON logs
- Correlation IDs for request tracing
- Tenant-scoped audit logs
- Error tracking with context

## Scalability

### Horizontal Scaling
- Backend: Multiple FastAPI instances behind load balancer
- Embedding Service: Multiple instances with shared model cache
- Database: Read replicas for query distribution

### Vertical Scaling
- GPU acceleration for embedding generation
- Increased database connection pool
- Larger Redis cache

## Next Steps

See detailed documentation:
- [API Specification](../api/README.md)
- [Deployment Guide](../deployment/README.md)
- [Security Guide](../security/README.md)
