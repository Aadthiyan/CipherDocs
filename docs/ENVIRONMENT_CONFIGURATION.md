# Environment Configuration & Secrets Management

This document describes all environment variables used by the CyborgDB backend and security best practices.

## Quick Start

1. **Copy the template:**
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **Generate secure secrets:**
   ```bash
   # Generate JWT secret
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Generate Master Encryption Key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Fill in `.env` file:**
   ```bash
   # Update DATABASE_URL with your Neon connection string
   # Update JWT_SECRET with generated value
   # Update MASTER_ENCRYPTION_KEY with generated value
   ```

4. **Verify configuration:**
   ```bash
   python -c "from app.core.config import settings; print('✅ Configuration loaded successfully')"
   ```

---

## Environment Variables Reference

### 🔴 Required Variables (Application Will Not Start)

| Variable | Description | Example | Security |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` | SENSITIVE - Use Neon |
| `JWT_SECRET` | Secret key for JWT signing | Min 32 characters | SENSITIVE - Must be strong |
| `MASTER_ENCRYPTION_KEY` | Key for tenant encryption | Min 32 characters | SENSITIVE - Keep safe |

**Validation Rules:**
- `DATABASE_URL` must start with `postgresql://`
- `JWT_SECRET` must be at least 32 characters
- `MASTER_ENCRYPTION_KEY` must be at least 32 characters
- Application exits immediately if these are missing or invalid

### 🟡 Important Variables (Have Defaults But Should Customize)

| Variable | Default | Description | Values |
|----------|---------|-------------|--------|
| `ENVIRONMENT` | `development` | Runtime environment | `development`, `staging`, `production` |
| `DEBUG` | `true` | Enable debug mode | `true`, `false` |
| `CYBORGDB_API_KEY` | `None` | CyborgDB integration | Your API key from dashboard |
| `CYBORGDB_ENDPOINT` | `https://api.cyborg.co` | CyborgDB API URL | URL string |
| `CYBORGDB_TIMEOUT` | `30` | Request timeout | Seconds (integer) |

**Development Notes:**
- Set `DEBUG=false` and `ENVIRONMENT=production` before deploying
- NEVER commit `.env` files with real secrets to Git
- Rotate `JWT_SECRET` and `MASTER_ENCRYPTION_KEY` regularly

### 🟢 Optional Variables (Have Safe Defaults)

#### Server Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |

#### Database Connection Pool
| Variable | Default | Description |
|----------|---------|-------------|
| `DB_POOL_SIZE` | `10` | Base pool size |
| `DB_MAX_OVERFLOW` | `20` | Max overflow connections |
| `DB_POOL_TIMEOUT` | `30` | Timeout in seconds |
| `DB_ECHO` | `false` | Log SQL queries (dev only) |

#### Redis Caching
| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `REDIS_ENABLED` | `false` | Enable caching |

**Note:** Leave `REDIS_URL` empty to disable Redis

#### JWT Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_ALGORITHM` | `HS256` | Signing algorithm |
| `JWT_EXPIRATION_HOURS` | `24` | Token expiry |
| `REFRESH_TOKEN_EXPIRATION_DAYS` | `30` | Refresh token expiry |

#### Embedding Service
| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_SERVICE_URL` | `http://localhost:8001` | Service URL |
| `EMBEDDING_DIMENSION` | `384` | Vector dimension |
| `HUGGINGFACE_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Model name |

#### CORS Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed origins (comma-separated) |

#### Logging
| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log verbosity |

**Valid Values:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

#### Rate Limiting
| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `MAX_LOGIN_ATTEMPTS` | `5` | Max login retries |
| `RATE_LIMIT_WINDOW_SECONDS` | `300` | Time window (5 min) |

#### Document Processing
| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_FILE_SIZE_MB` | `50` | Max upload size |
| `ALLOWED_FILE_TYPES` | `pdf,docx,txt` | Allowed types |
| `CHUNK_SIZE` | `512` | Text chunk size |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |

#### Search Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_TOP_K` | `10` | Default results |
| `MAX_TOP_K` | `100` | Max results limit |
| `SEARCH_TIMEOUT_SECONDS` | `30` | Search timeout |

#### Storage Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_BACKEND` | `local` | Storage type |
| `LOCAL_STORAGE_PATH` | `./storage/documents` | Local path |

**Valid Backends:**
- `local`: Store on server filesystem
- `s3`: AWS S3 storage
- `minio`: Self-hosted S3-compatible

---

## Configuration by Environment

### Development Environment
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/cyborgdb_dev
JWT_SECRET=dev_jwt_secret_at_least_32_chars_for_testing
MASTER_ENCRYPTION_KEY=dev_master_key_at_least_32_chars_for_testing
```

### Staging Environment
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://staging_user:secure_pass@neon.tech/cyborgdb_staging
JWT_SECRET=strong_random_32_char_secret_from_key_manager
MASTER_ENCRYPTION_KEY=strong_random_32_char_key_from_key_manager
```

### Production Environment
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod_user:secure_pass@neon.tech/cyborgdb_prod
JWT_SECRET=very_strong_unique_secret_from_secrets_manager
MASTER_ENCRYPTION_KEY=very_strong_unique_key_from_secrets_manager
```

---

## Security Best Practices

### 🔐 Secret Generation

Generate strong secrets using Python:
```python
import secrets

# Generate JWT secret
jwt_secret = secrets.token_urlsafe(32)
print(f"JWT_SECRET={jwt_secret}")

# Generate Master Encryption Key
master_key = secrets.token_urlsafe(32)
print(f"MASTER_ENCRYPTION_KEY={master_key}")
```

### 🔐 Secret Management

1. **Development:**
   - Store in `.env` file (gitignored)
   - Use test/demo secrets only
   - Never use production secrets

2. **Staging/Production:**
   - Use environment variables from CI/CD system
   - Consider AWS Secrets Manager / HashiCorp Vault
   - Rotate secrets regularly (monthly/quarterly)
   - Audit access to secrets

### 🔐 .gitignore

Ensure `.env` is in `.gitignore`:
```
# Environment variables
.env
.env.local
.env.*.local
.env.*.example  # Optional - only if no example needed in repo
```

### 🔐 No Secrets in Logs

Configuration validation logs secrets carefully:
- Database URL shows only hostname (not credentials)
- Secrets never logged in full
- Error messages are descriptive but safe

Example safe log:
```
🔧 Configuration Loaded Successfully
  Environment: production
  Debug Mode: false
  Server: 0.0.0.0:8000
  Database: ep-shy-tree-ah0y8hv8-pooler.c-3.us-east-1.aws.neon.tech
  Storage Backend: s3
  Log Level: WARNING
```

### 🔐 Validation & Fail-Fast

Configuration is validated immediately at startup:
- Missing required variables → Clear error message
- Invalid values → Descriptive validation error
- Application exits if config is invalid
- No partial or degraded startup

Example error:
```
❌ Configuration Validation Failed
  ❌ JWT_SECRET: JWT_SECRET must be at least 32 characters long. Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Troubleshooting

### "Application refused to start"

Check for configuration errors:
```bash
# Run configuration validation
python -c "from app.core.config import settings; print('✅ OK')"

# View logs for specific errors
tail -50 logs/app.log
```

### "DATABASE_URL invalid"

Ensure correct PostgreSQL format:
```bash
# ✅ Correct
postgresql://user:pass@host:5432/dbname?sslmode=require

# ❌ Wrong
postgres://user:pass@host:5432/dbname
mysql://user:pass@host:3306/dbname
```

### "JWT_SECRET too weak"

Generate a strong secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output and set JWT_SECRET=...
```

### "MASTER_ENCRYPTION_KEY too weak"

Generate a strong key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output and set MASTER_ENCRYPTION_KEY=...
```

---

## Configuration Loading Performance

Configuration is loaded once at application startup:
- **Load Time**: < 100ms
- **Validation**: All variables checked atomically
- **Caching**: Settings cached in global `settings` object
- **No Reload**: Requires server restart for config changes

Access configuration in code:
```python
from app.core.config import settings

# Read configuration
db_url = settings.DATABASE_URL
debug_mode = settings.DEBUG
max_file_size = settings.MAX_FILE_SIZE_MB

# Check environment
if settings.is_production():
    # Production-specific logic
    pass
```

---

## Environment Variable Validation Rules

| Variable | Min Length | Format | Allowed Values |
|----------|-----------|--------|-----------------|
| `DATABASE_URL` | - | URL | Must start with `postgresql://` |
| `JWT_SECRET` | 32 chars | String | Any alphanumeric + symbols |
| `MASTER_ENCRYPTION_KEY` | 32 chars | String | Any alphanumeric + symbols |
| `ENVIRONMENT` | - | Enum | `development`, `staging`, `production` |
| `STORAGE_BACKEND` | - | Enum | `local`, `s3`, `minio` |
| `LOG_LEVEL` | - | Enum | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `JWT_EXPIRATION_HOURS` | - | Integer | Positive integer |
| `MAX_FILE_SIZE_MB` | - | Integer | Positive integer |

---

## Related Files

- [`.env.example`](backend/.env.example) - Configuration template
- [`app/core/config.py`](backend/app/core/config.py) - Configuration loading logic
- [`.gitignore`](.gitignore) - Ensures secrets aren't committed
- [`docs/CYBORGDB_SETUP.md`](docs/CYBORGDB_SETUP.md) - CyborgDB configuration
- [`docs/DATABASE_OPERATIONS.md`](docs/DATABASE_OPERATIONS.md) - Database setup

---

## Checklist: Deploying Configuration

- [ ] Copy `.env.example` to `.env`
- [ ] Generate strong `JWT_SECRET`
- [ ] Generate strong `MASTER_ENCRYPTION_KEY`
- [ ] Set `DATABASE_URL` to Neon/production database
- [ ] Set `ENVIRONMENT` to `production`
- [ ] Set `DEBUG=false`
- [ ] Configure `STORAGE_BACKEND` (local/s3/minio)
- [ ] Run configuration validation: `python -c "from app.core.config import settings"`
- [ ] Test application startup: `python main.py`
- [ ] Verify no secrets in logs
- [ ] Ensure `.env` is in `.gitignore`
- [ ] Document any custom configuration in team wiki
