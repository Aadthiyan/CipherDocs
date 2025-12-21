# CyborgDB Database Schema Documentation

## Overview

The CyborgDB database schema is designed for a multi-tenant SaaS platform with encrypted document search capabilities. The schema enforces strict tenant isolation, supports role-based access control, and tracks all document processing and search activities.

## Database: PostgreSQL 14+

**Why PostgreSQL?**
- Native UUID support
- JSONB for flexible metadata
- Excellent performance for complex queries
- Strong ACID compliance
- Robust foreign key constraints

---

## Entity Relationship Diagram (ERD)

```
┌─────────────────────────────────────────────────────────────────┐
│                          TENANTS                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ id (UUID, PK)                                             │   │
│  │ name (VARCHAR 255)                                        │   │
│  │ plan (VARCHAR 50) [starter, pro, enterprise]             │   │
│  │ key_fingerprint (VARCHAR 255, UNIQUE)                    │   │
│  │ cyborgdb_namespace (VARCHAR 255, UNIQUE)                 │   │
│  │ is_active (BOOLEAN)                                       │   │
│  │ created_at (TIMESTAMP)                                    │   │
│  │ updated_at (TIMESTAMP)                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├──────────────────────────────────────────┐
             │                                          │
             ▼                                          ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│        USERS            │              │   ENCRYPTION_KEYS       │
├─────────────────────────┤              ├─────────────────────────┤
│ id (UUID, PK)           │              │ id (UUID, PK)           │
│ email (VARCHAR, UNIQUE) │              │ tenant_id (UUID, FK)    │
│ tenant_id (UUID, FK) ───┼──────┐       │ key_fingerprint (UNIQUE)│
│ password_hash (VARCHAR) │      │       │ encrypted_key (TEXT)    │
│ role (VARCHAR 50)       │      │       │ is_active (BOOLEAN)     │
│ is_active (BOOLEAN)     │      │       │ created_at (TIMESTAMP)  │
│ last_login (TIMESTAMP)  │      │       │ rotated_at (TIMESTAMP)  │
│ created_at (TIMESTAMP)  │      │       └─────────────────────────┘
│ updated_at (TIMESTAMP)  │      │
└────────┬────────────────┘      │
         │                       │
         │                       ▼
         │          ┌─────────────────────────┐
         │          │      DOCUMENTS          │
         │          ├─────────────────────────┤
         │          │ id (UUID, PK)           │
         │          │ tenant_id (UUID, FK)    │
         │          │ filename (VARCHAR 255)  │
         │          │ storage_path (VARCHAR)  │
         │          │ doc_type (VARCHAR 50)   │
         │          │ file_size_bytes (BIGINT)│
         │          │ file_hash (VARCHAR 64)  │
         │          │ chunk_count (INTEGER)   │
         │          │ status (VARCHAR 50)     │
         │          │ error_message (TEXT)    │
         │          │ retry_count (INTEGER)   │
         │          │ uploaded_at (TIMESTAMP) │
         │          │ updated_at (TIMESTAMP)  │
         │          └────────┬────────────────┘
         │                   │
         │                   ▼
         │          ┌─────────────────────────┐
         │          │   DOCUMENT_CHUNKS       │
         │          ├─────────────────────────┤
         │          │ id (UUID, PK)           │
         │          │ doc_id (UUID, FK)       │
         │          │ tenant_id (UUID, FK)    │
         │          │ chunk_sequence (INTEGER)│
         │          │ text (TEXT)             │
         │          │ embedding_dimension (INT)│
         │          │ page_number (INTEGER)   │
         │          │ section_heading (VARCHAR)│
         │          │ indexed_at (TIMESTAMP)  │
         │          └─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│     SEARCH_LOGS         │
├─────────────────────────┤
│ id (UUID, PK)           │
│ tenant_id (UUID, FK)    │
│ user_id (UUID, FK)      │
│ query_text (VARCHAR)    │
│ query_latency_ms (INT)  │
│ result_count (INTEGER)  │
│ top_k (INTEGER)         │
│ created_at (TIMESTAMP)  │
└─────────────────────────┘

┌─────────────────────────┐
│       SESSIONS          │
├─────────────────────────┤
│ id (UUID, PK)           │
│ user_id (UUID, FK)      │
│ refresh_token (VARCHAR) │
│ expires_at (TIMESTAMP)  │
│ is_revoked (BOOLEAN)    │
│ created_at (TIMESTAMP)  │
└─────────────────────────┘
```

---

## Table Specifications

### 1. TENANTS

**Purpose:** Store tenant (organization) information for multi-tenancy

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique tenant identifier |
| name | VARCHAR(255) | NOT NULL | Tenant organization name |
| plan | VARCHAR(50) | NOT NULL, DEFAULT 'starter' | Subscription plan (starter, pro, enterprise) |
| key_fingerprint | VARCHAR(255) | UNIQUE | Fingerprint of tenant's encryption key |
| cyborgdb_namespace | VARCHAR(255) | UNIQUE | CyborgDB index/namespace for this tenant |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether tenant is active |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Tenant creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes:**
- `ix_tenants_name` - For tenant lookup by name
- `ix_tenants_is_active` - For filtering active tenants

**Relationships:**
- One-to-many with Users
- One-to-many with Documents
- One-to-many with DocumentChunks
- One-to-many with SearchLogs
- One-to-many with EncryptionKeys

---

### 2. USERS

**Purpose:** Store user authentication and authorization information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| tenant_id | UUID | FK → tenants.id, NOT NULL | Tenant this user belongs to |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| role | VARCHAR(50) | NOT NULL, DEFAULT 'user' | User role (admin, user, viewer) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether user account is active |
| last_login | TIMESTAMP | NULL | Last successful login timestamp |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | User creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes:**
- `ix_users_email` - For login lookups
- `ix_users_tenant_id` - For tenant-scoped queries
- `ix_users_tenant_email` (UNIQUE) - Ensure email unique per tenant

**Relationships:**
- Many-to-one with Tenant
- One-to-many with SearchLogs
- One-to-many with Sessions

**Cascade Rules:**
- ON DELETE CASCADE - When tenant is deleted, all users are deleted

---

### 3. DOCUMENTS

**Purpose:** Store metadata about uploaded documents

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique document identifier |
| tenant_id | UUID | FK → tenants.id, NOT NULL | Tenant that owns this document |
| filename | VARCHAR(255) | NOT NULL | Original filename |
| storage_path | VARCHAR(500) | NOT NULL | Path to stored file (S3/local) |
| doc_type | VARCHAR(50) | NOT NULL | File type (pdf, docx, txt) |
| file_size_bytes | BIGINT | NULL | File size in bytes |
| file_hash | VARCHAR(64) | NULL | SHA-256 hash for deduplication |
| chunk_count | INTEGER | DEFAULT 0 | Number of chunks extracted |
| status | VARCHAR(50) | NOT NULL, DEFAULT 'uploaded' | Processing status |
| error_message | TEXT | NULL | Error message if processing failed |
| retry_count | INTEGER | DEFAULT 0 | Number of processing retries |
| uploaded_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Upload timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Status Values:**
- `uploaded` - File uploaded, not yet processed
- `extracting` - Extracting text from file
- `chunking` - Splitting text into chunks
- `embedding` - Generating embeddings
- `indexing` - Storing in CyborgDB
- `completed` - Fully processed and indexed
- `failed` - Processing failed

**Indexes:**
- `ix_documents_tenant_id` - For tenant-scoped queries
- `ix_documents_status` - For status filtering
- `ix_documents_file_hash` - For duplicate detection
- `ix_documents_tenant_status` - Composite index for common queries

**Relationships:**
- Many-to-one with Tenant
- One-to-many with DocumentChunks

**Cascade Rules:**
- ON DELETE CASCADE - When tenant is deleted, all documents are deleted

---

### 4. DOCUMENT_CHUNKS

**Purpose:** Store text chunks extracted from documents for embedding and search

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique chunk identifier |
| doc_id | UUID | FK → documents.id, NOT NULL | Parent document |
| tenant_id | UUID | FK → tenants.id, NOT NULL | Tenant (for isolation) |
| chunk_sequence | INTEGER | NOT NULL | Sequence number within document |
| text | TEXT | NOT NULL | Chunk text content |
| embedding_dimension | INTEGER | DEFAULT 384 | Embedding vector dimension |
| page_number | INTEGER | NULL | Page number in source document |
| section_heading | VARCHAR(500) | NULL | Section heading if available |
| indexed_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When chunk was indexed |

**Indexes:**
- `ix_document_chunks_doc_id` - For document-scoped queries
- `ix_document_chunks_tenant_id` - For tenant isolation
- `ix_document_chunks_doc_sequence` (UNIQUE) - Ensure unique sequence per document

**Relationships:**
- Many-to-one with Document
- Many-to-one with Tenant

**Cascade Rules:**
- ON DELETE CASCADE - When document is deleted, all chunks are deleted

---

### 5. SEARCH_LOGS

**Purpose:** Track search queries for analytics and monitoring

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique log identifier |
| tenant_id | UUID | FK → tenants.id, NOT NULL | Tenant that performed search |
| user_id | UUID | FK → users.id, NULL | User that performed search |
| query_text | VARCHAR(1000) | NOT NULL | Search query text |
| query_latency_ms | INTEGER | NULL | Query latency in milliseconds |
| result_count | INTEGER | NULL | Number of results returned |
| top_k | INTEGER | DEFAULT 10 | Number of results requested |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Search timestamp |

**Indexes:**
- `ix_search_logs_tenant_id` - For tenant-scoped analytics
- `ix_search_logs_created_at` - For time-based queries
- `ix_search_logs_tenant_created` - Composite for common analytics queries

**Relationships:**
- Many-to-one with Tenant
- Many-to-one with User (optional)

**Cascade Rules:**
- ON DELETE CASCADE - When tenant is deleted, all logs are deleted
- ON DELETE SET NULL - When user is deleted, logs remain but user_id is nulled

---

### 6. ENCRYPTION_KEYS

**Purpose:** Store encrypted tenant-specific encryption keys

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique key identifier |
| tenant_id | UUID | FK → tenants.id, NOT NULL | Tenant that owns this key |
| key_fingerprint | VARCHAR(255) | UNIQUE, NOT NULL | Key fingerprint for identification |
| encrypted_key | TEXT | NOT NULL | Encrypted AES key (encrypted with master key) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether this key is currently active |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Key creation timestamp |
| rotated_at | TIMESTAMP | NULL | When key was last rotated |

**Indexes:**
- `ix_encryption_keys_tenant_id` - For tenant-scoped queries
- `ix_encryption_keys_tenant_active` - Ensure only one active key per tenant

**Relationships:**
- Many-to-one with Tenant

**Cascade Rules:**
- ON DELETE CASCADE - When tenant is deleted, all keys are deleted

**Security Notes:**
- Keys are encrypted at rest using MASTER_ENCRYPTION_KEY
- Only one active key per tenant at a time
- Old keys retained for decryption of historical data

---

### 7. SESSIONS

**Purpose:** Track user sessions and refresh tokens

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique session identifier |
| user_id | UUID | FK → users.id, NOT NULL | User this session belongs to |
| refresh_token | VARCHAR(500) | UNIQUE, NOT NULL | JWT refresh token |
| expires_at | TIMESTAMP | NOT NULL | Token expiration timestamp |
| is_revoked | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether token has been revoked |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Session creation timestamp |

**Indexes:**
- `ix_sessions_user_id` - For user-scoped queries
- `ix_sessions_refresh_token` - For token lookup
- `ix_sessions_expires_at` - For cleanup of expired sessions

**Relationships:**
- Many-to-one with User

**Cascade Rules:**
- ON DELETE CASCADE - When user is deleted, all sessions are deleted

---

## Data Integrity & Constraints

### Foreign Key Constraints

1. **Tenant Isolation**
   - All user data is linked to a tenant
   - Cascading deletes ensure no orphaned records
   - Composite indexes enforce tenant-scoped queries

2. **Document Hierarchy**
   - Documents belong to tenants
   - Chunks belong to both documents and tenants (redundant for performance)
   - Cascading deletes maintain referential integrity

3. **User Sessions**
   - Sessions belong to users
   - Revoked sessions remain for audit trail
   - Expired sessions cleaned up periodically

### Unique Constraints

1. **Email uniqueness** - Per tenant (not globally)
2. **Key fingerprints** - Globally unique
3. **CyborgDB namespaces** - Globally unique
4. **Chunk sequences** - Unique per document
5. **Refresh tokens** - Globally unique

### Check Constraints

1. **Plan values** - Must be 'starter', 'pro', or 'enterprise'
2. **Role values** - Must be 'admin', 'user', or 'viewer'
3. **Status values** - Must be valid document status
4. **Positive values** - chunk_count, file_size_bytes, etc.

---

## Performance Optimization

### Indexes Strategy

1. **Single-column indexes** - For primary lookups (email, tenant_id)
2. **Composite indexes** - For common query patterns (tenant_id + created_at)
3. **Unique indexes** - Enforce constraints and speed up lookups

### Query Optimization

1. **Tenant-scoped queries** - Always filter by tenant_id first
2. **Time-based queries** - Use created_at indexes
3. **Status filtering** - Indexed for document processing queries

### Expected Performance

- **Empty tables:** < 1ms for all queries
- **1M documents:** < 100ms for tenant-scoped queries
- **10M chunks:** < 200ms with proper indexing
- **Search logs:** Partitioning recommended after 100M records

---

## Security Considerations

### Multi-Tenant Isolation

1. **Row-level security** - All queries filtered by tenant_id
2. **Encrypted keys** - Tenant keys encrypted with master key
3. **Cascade deletes** - Prevent orphaned data

### Data Protection

1. **Password hashing** - Bcrypt with salt
2. **Key encryption** - AES-256 encryption
3. **Audit trail** - Search logs track all queries

### Compliance

- **GDPR** - User deletion cascades all personal data
- **HIPAA** - Encryption at rest and in transit
- **SOC2** - Audit logs for all data access

---

## Migration Strategy

### Initial Migration

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### Rollback

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

### Future Migrations

1. **Add columns** - Use `ALTER TABLE ADD COLUMN`
2. **Modify columns** - Create new column, migrate data, drop old
3. **Add indexes** - Use `CREATE INDEX CONCURRENTLY` (PostgreSQL)
4. **Data migrations** - Separate migration for data changes

---

## Maintenance

### Regular Tasks

1. **Vacuum** - Weekly VACUUM ANALYZE
2. **Reindex** - Monthly REINDEX for heavily updated tables
3. **Cleanup** - Delete expired sessions daily
4. **Backup** - Daily full backup, hourly incremental

### Monitoring

1. **Table sizes** - Monitor growth trends
2. **Index usage** - Identify unused indexes
3. **Query performance** - Slow query log analysis
4. **Connection pool** - Monitor pool utilization

---

## Estimated Storage

### Per Tenant (1000 documents, 100 pages each)

- **Documents:** ~100 KB
- **Chunks:** ~50 MB (100,000 chunks × 500 bytes)
- **Search Logs:** ~10 MB (10,000 searches × 1 KB)
- **Total:** ~60 MB per tenant

### Database Size Projections

- **100 tenants:** ~6 GB
- **1,000 tenants:** ~60 GB
- **10,000 tenants:** ~600 GB

**Note:** Actual size depends on document size and search volume.

---

## Schema Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2025-12-03 | Initial schema with all core tables |

---

**Last Updated:** December 3, 2025  
**Database:** PostgreSQL 14+  
**ORM:** SQLAlchemy 2.0  
**Migration Tool:** Alembic
