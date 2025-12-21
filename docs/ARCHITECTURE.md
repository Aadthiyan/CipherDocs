# Architecture - CipherDocs

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Tier                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   React SPA  │    │  Mobile App  │    │  REST Client │      │
│  │ (Web UI)     │    │  (iOS/And)   │    │  (cURL, etc) │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘              │
│                              │ HTTPS                            │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway / LB                             │
│              (nginx / AWS ALB / Cloudflare)                    │
│  - SSL/TLS Termination                                          │
│  - Rate Limiting                                                │
│  - Request Routing                                              │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Backend Services (Tier 1)                 │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │  FastAPI Server  │  │  FastAPI Server  │  │ FastAPI Srv  │   │
│  │   (Instance 1)   │  │   (Instance 2)   │  │ (Instance N) │   │
│  │                  │  │                  │  │              │   │
│  │ - Auth Service   │  │ - Auth Service   │  │ - Auth Svc   │   │
│  │ - Doc Service    │  │ - Doc Service    │  │ - Doc Svc    │   │
│  │ - Search Service │  │ - Search Service │  │ - Search Svc │   │
│  │ - Analytics      │  │ - Analytics      │  │ - Analytics  │   │
│  │                  │  │                  │  │              │   │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────┘   │
│           │                     │                     │         │
│           └─────────────────────┼─────────────────────┘         │
│                                 │                               │
└─────────────────────────────────┼───────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Support Services                            │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────┐ │
│  │  Embedding Service │  │   CyborgDB         │  │   Cache    │ │
│  │  (Python + PyTorch)│  │ (Encrypted Vector  │  │  (Redis)   │ │
│  │                    │  │  Database)         │  │            │ │
│  │ - HuggingFace BERT │  │                    │  │ - Search   │ │
│  │ - Vector Gen       │  │ - Encrypted        │  │ - Sessions │ │
│  │ - Model Caching    │  │   Similarity       │  │ - Data     │ │
│  │ - GPU Support      │  │ - Access Control   │  │            │ │
│  │ - Batch Process    │  │ - Multi-tenant     │  │            │ │
│  │                    │  │                    │  │            │ │
│  └────────┬───────────┘  └────────┬───────────┘  └────────┬───┘ │
│           │                       │                       │      │
└───────────┼───────────────────────┼───────────────────────┼──────┘
            │                       │                       │
            │       ┌───────────────┼───────────────┐       │
            │       │               │               │       │
            ▼       ▼               ▼               ▼       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Data Tier                                     │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │   PostgreSQL   │  │ Encrypted      │  │ File Storage   │    │
│  │   Database     │  │ Vault/Secrets  │  │ (S3/Local)     │    │
│  │                │  │                │  │                │    │
│  │ - Users        │  │ - Encryption   │  │ - PDFs         │    │
│  │ - Documents    │  │   Keys         │  │ - Documents    │    │
│  │ - Chunks       │  │ - API Keys     │  │ - Indexes      │    │
│  │ - Metadata     │  │ - Credentials  │  │ - Backups      │    │
│  │ - Audit Logs   │  │                │  │                │    │
│  │                │  │                │  │                │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Interactions

### Authentication Flow

```
Client                   Backend                    Database
  │                         │                           │
  │──POST /auth/login────▶  │                           │
  │                         │──Query User──────────────▶│
  │                         │◀──User Record─────────────│
  │                         │                           │
  │                    [Hash Password]                  │
  │                    [Generate JWT]                   │
  │                         │                           │
  │◀──Token Response────────│                           │
  │                         │                           │
  │──GET /documents─────▶   │                           │
  │  (With Token)          │[Verify JWT]               │
  │                         │──Query Documents─────────▶│
  │                         │◀──Document List───────────│
  │◀──Documents────────────│                            │
```

### Document Upload & Processing

```
Client                   Backend                 Embedding Service
  │                         │                           │
  │──POST /upload────────▶  │                           │
  │  (File)                 │[Create Document Record]   │
  │                         │──Queue Job─────────────▶  │
  │◀──202 Accepted─────────│  (Background)             │
  │                         │                           │
  │  (Client polls)         │                           │
  │──GET /documents/{id}──▶ │                           │
  │                         │──Read Status──────────────│
  │                     [Processing starts]             │
  │                         │                           │
  │                         │──1. Extract Text─────────▶│
  │                         │◀──Text Chunks────────────│
  │                         │                           │
  │                         │──2. Generate Embeddings──▶│
  │                         │◀──Vectors────────────────│
  │                         │                           │
  │                    [3. Encrypt Embeddings]          │
  │                    [4. Store in CyborgDB]           │
  │                         │                           │
  │◀──200 Ready────────────│  (Status: completed)      │
```

### Search Flow

```
Client                   Backend                   CyborgDB
  │                         │                         │
  │──POST /search────────▶  │                         │
  │  (Query: "AI ML")       │[Embed Query String]     │
  │                         │─────────────────────────│
  │                         │─────────────────────────▶│
  │                         │◀──Vector────────────────│
  │                         │                         │
  │                         │[Encrypt Query Vector]   │
  │                         │                         │
  │                         │──Search with            │
  │                         │  Encrypted Vector───────▶│
  │                         │                         │
  │                         │◀──Encrypted Results────│
  │                         │                         │
  │                    [Decrypt Results]              │
  │                    [Format Response]              │
  │                         │                         │
  │◀──JSON Results─────────│                         │
  │  (Top 10 matches)       │                         │
```

---

## Data Flow

### Request Processing

```
Incoming Request
      │
      ▼
┌──────────────────────────┐
│ SSL/TLS Termination      │  - HTTPS enforcement
│ Request Validation       │  - Schema validation
│ Rate Limiting Check      │  - Rate limit verification
└──────────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Authentication           │  - Extract JWT token
│ Token Verification       │  - Verify signature
│ User Lookup              │  - Get user context
└──────────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Tenant Isolation         │  - Verify tenant_id
│ Permission Check         │  - Check RBAC
│ Request Context Setup    │  - Set user/tenant
└──────────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Request Routing          │  - Route to handler
│ Dependency Injection     │  - Inject dependencies
│ Handler Execution        │  - Execute business logic
└──────────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Response Serialization   │  - Pydantic validation
│ Audit Logging            │  - Log request/response
│ Error Handling           │  - Format errors
└──────────────────────────┘
      │
      ▼
Response to Client
```

---

## Security Architecture

### Encryption Strategy

```
Document Upload
      │
      ▼
┌─────────────────────┐
│ File Processing     │  - Extract text
│ Chunking            │  - Split into chunks
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Embedding Generation│  - Generate 768-dim vectors
│ (No encryption yet) │  - From text content
└─────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│ Encryption (Server-side)    │  - Uses tenant's key
│ AES-256-GCM                 │  - 256-bit encryption
│ Per-tenant encryption key   │  - Unique per tenant
└─────────────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Storage in CyborgDB │  - Encrypted vectors
│ Metadata in PgSQL   │  - Unencrypted metadata
└─────────────────────┘
```

### Multi-Tenant Isolation

```
┌─────────────────────────────────────────┐
│         All Data Structures             │
├─────────────────────────────────────────┤
│                                         │
│  Users                                  │
│  ├── tenant_id (indexed)               │
│  ├── email (unique per tenant)         │
│  └── documents ───────────┐            │
│                            │            │
│  Documents                 │            │
│  ├── tenant_id (indexed)   │            │
│  ├── file_content ◀────────┘            │
│  └── chunks ────────────────┐           │
│                              │           │
│  DocumentChunks             │           │
│  ├── tenant_id (indexed)    │           │
│  ├── text ◀─────────────────┘           │
│  ├── encrypted_embedding    │           │
│  └── created_by (user_id)   │           │
│                              │           │
│  Search Queries             │           │
│  ├── tenant_id (indexed)    │           │
│  ├── query_text             │           │
│  └── results                │           │
│                              │           │
│  All queries ALWAYS include: │           │
│  WHERE tenant_id = current_tenant_id    │
│                                         │
│  ✅ Zero Cross-Tenant Data Leakage     │
│  ✅ Encryption Key Per Tenant          │
│  ✅ Database-level Isolation           │
│  ✅ Application-level Verification     │
│                                         │
└─────────────────────────────────────────┘
```

### Key Management

```
Master Encryption Key (MEK)
│
├── Environment Variable: ENCRYPTION_MASTER_KEY
│
├── Never logged, printed, or transmitted
│
└── Used to encrypt Tenant Encryption Keys (TEK)
    │
    ├── TEK generated per tenant
    │
    ├── TEK encrypted with MEK
    │
    ├── Encrypted TEK stored in secrets vault
    │
    └── Decrypted on-demand for tenant operations
        │
        └── Used to encrypt/decrypt embeddings
```

---

## Scalability

### Horizontal Scaling

```
                    Load Balancer
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
      Backend-1      Backend-2      Backend-N
          │               │               │
          └───────────────┼───────────────┘
                          │
                   Shared Database
                    (Connection Pool)
```

**Strategy:**
- Multiple FastAPI instances behind load balancer
- Stateless services (no session state)
- Shared PostgreSQL database
- Connection pooling via pgBouncer or PgSQL max_connections
- Redis cache for session/data caching

### Vertical Scaling

```
Single Powerful Instance
│
├── ✅ More CPU cores (8-16)
├── ✅ More RAM (16-32GB)
├── ✅ SSD storage (50GB+)
├── ✅ Worker processes increased
│    (uvicorn --workers 16)
│
└── Embedded Scaling
    ├── Process in batches (100 chunks at a time)
    ├── GPU acceleration for embeddings
    └── Caching frequently used embeddings
```

---

## Failure Modes & Recovery

```
Component Failure        Recovery Time      Strategy
─────────────────────────────────────────────────────────
Backend Instance         < 1 min            Auto-restart
Database                 < 5 min            Replica failover
Redis Cache              < 30 sec           Restart
Embedding Service        2-5 min            Model reload
Network Partition        Varies             Retry with backoff
Disk Space Exhausted     Manual             Archive old data

Success Criteria:
- RTO (Recovery Time Objective): < 5 minutes
- RPO (Recovery Point Objective): < 1 minute
```

---

## Performance Characteristics

```
Operation               Latency      Throughput    Notes
─────────────────────────────────────────────────────────
Login                   50-100ms     100+/sec      Cached
Search Query            125-200ms    100+/sec      p99 < 1s
Document Upload         1-3 sec      100+ docs/hr  10MB file
Embedding (1000)        2-5 sec      200+/sec      GPU: <1s
Encryption (1000)       500ms        2000+/sec     Server-side
Database Query          5-20ms       1000+/sec     Indexed
Cache Hit               < 5ms        10000+/sec    Redis
Cache Miss              + latency    -             Fallback to DB
```

---

## Monitoring & Observability

### Metrics

```
Application Metrics:
- Request latency (p50, p95, p99)
- Request throughput (req/sec)
- Error rate (%)
- Cache hit ratio (%)
- Search result count
- Upload success rate

System Metrics:
- CPU usage (%)
- Memory usage (%)
- Disk usage (%)
- Network bandwidth (Mbps)
- Connections (active/idle)

Database Metrics:
- Query latency
- Slow query count
- Connection pool status
- Index usage
- Table bloat
```

### Logging Strategy

```
Log Levels (configured in .env):
- DEBUG: Development (verbose)
- INFO: Production (normal operations)
- WARNING: Anomalies to investigate
- ERROR: Failures requiring attention
- CRITICAL: System-wide failures

Log Aggregation:
- ELK Stack (Elasticsearch/Kibana)
- CloudWatch (AWS)
- DataDog
- Splunk

Audit Logging:
- All authentication events
- Document access
- Search queries
- Data modifications
- Administrative actions
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 | Web UI |
| **API** | FastAPI | REST API framework |
| **Server** | Uvicorn | ASGI server |
| **Database** | PostgreSQL 13+ | Relational data |
| **Vector DB** | CyborgDB | Encrypted vectors |
| **Cache** | Redis | Session/data cache |
| **Embeddings** | HuggingFace BERT | Text vectorization |
| **Auth** | PyJWT | Token generation |
| **Encryption** | Cryptography | AES-256-GCM |
| **Validation** | Pydantic | Schema validation |
| **Testing** | Pytest | Unit/integration tests |
| **Container** | Docker | Deployment |
| **Orchestration** | Docker Compose | Local; Kubernetes for production |

---

## References

- [FastAPI Architecture Patterns](https://fastapi.tiangolo.com/)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [12-Factor App Methodology](https://12factor.net/)

---

**Last Updated**: December 16, 2025  
**Version**: 1.0  
**Status**: ✅ Complete
