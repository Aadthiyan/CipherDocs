# Database Operations Quick Reference

## Alembic Migration Commands

### Create New Migration
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration (for data migrations)
alembic revision -m "Description"
```

### Apply Migrations
```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Upgrade to specific version
alembic upgrade <revision_id>
```

### Rollback Migrations
```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Downgrade to base (empty database)
alembic downgrade base
```

### View Migration History
```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Database Setup

### First Time Setup
```bash
# 1. Ensure PostgreSQL is running
docker-compose up postgres

# 2. Create initial migration
cd backend
alembic revision --autogenerate -m "Initial schema"

# 3. Apply migration
alembic upgrade head

# 4. Verify tables created
docker-compose exec postgres psql -U cyborgdb_user -d cyborgdb -c "\dt"
```

### Reset Database
```bash
# WARNING: This deletes all data!

# 1. Downgrade to base
alembic downgrade base

# 2. Upgrade to latest
alembic upgrade head
```

## Common SQL Queries

### View All Tables
```sql
\dt
```

### Describe Table Structure
```sql
\d tenants
\d users
\d documents
```

### Check Table Sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### View Indexes
```sql
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

### Check Foreign Keys
```sql
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

## Seed Data

### Create Demo Tenant
```sql
INSERT INTO tenants (id, name, plan, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'Demo Tenant',
    'pro',
    true,
    NOW(),
    NOW()
);
```

### Create Demo User
```sql
-- First, get tenant_id
SELECT id FROM tenants WHERE name = 'Demo Tenant';

-- Then create user (replace <tenant_id>)
INSERT INTO users (id, email, tenant_id, password_hash, role, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'demo@example.com',
    '<tenant_id>',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7BQKQ4Q4zO',  -- password: demo123
    'admin',
    true,
    NOW(),
    NOW()
);
```

## Troubleshooting

### Migration Conflicts
```bash
# If you have migration conflicts:

# 1. Check current version
alembic current

# 2. View history
alembic history

# 3. Manually resolve conflicts in migration files

# 4. Mark as resolved
alembic stamp head
```

### Database Connection Issues
```bash
# Test connection
docker-compose exec postgres psql -U cyborgdb_user -d cyborgdb -c "SELECT 1;"

# Check if database exists
docker-compose exec postgres psql -U cyborgdb_user -l

# Restart PostgreSQL
docker-compose restart postgres
```

### Schema Out of Sync
```bash
# If models and database are out of sync:

# 1. Create new migration
alembic revision --autogenerate -m "Sync schema"

# 2. Review generated migration file

# 3. Apply migration
alembic upgrade head
```

## Performance Tuning

### Analyze Query Performance
```sql
EXPLAIN ANALYZE
SELECT * FROM documents WHERE tenant_id = '<tenant_id>' AND status = 'completed';
```

### Rebuild Indexes
```sql
REINDEX TABLE documents;
REINDEX DATABASE cyborgdb;
```

### Vacuum and Analyze
```sql
VACUUM ANALYZE tenants;
VACUUM ANALYZE documents;
VACUUM FULL;  -- WARNING: Locks table
```

## Backup and Restore

### Backup Database
```bash
# Full backup
docker-compose exec postgres pg_dump -U cyborgdb_user cyborgdb > backup.sql

# Schema only
docker-compose exec postgres pg_dump -U cyborgdb_user --schema-only cyborgdb > schema.sql

# Data only
docker-compose exec postgres pg_dump -U cyborgdb_user --data-only cyborgdb > data.sql
```

### Restore Database
```bash
# Restore from backup
docker-compose exec -T postgres psql -U cyborgdb_user cyborgdb < backup.sql
```

## Monitoring

### Active Connections
```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'cyborgdb';
```

### Long Running Queries
```sql
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
```

### Table Statistics
```sql
SELECT 
    schemaname,
    tablename,
    n_live_tup AS live_tuples,
    n_dead_tup AS dead_tuples,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

---

**Note:** Always test migrations on a development database before applying to production!
