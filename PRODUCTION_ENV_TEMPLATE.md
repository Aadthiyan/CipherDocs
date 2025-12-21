# Production Deployment Configuration
# Copy and use the settings below when deploying to Render

## Backend Environment Variables for Render

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Database (Use your existing Neon PostgreSQL connection string)
# Get from: https://console.neon.tech → Project → Connection string
# Format: postgresql://user:password@host:port/database
DATABASE_URL=postgresql://user:password@ec2-xxx.compute-1.amazonaws.com:5432/cipherdocs_db

# Redis (Using Upstash - cloud-hosted)
# Already configured and working with Upstash
# Format: redis://default:password@host:port
REDIS_URL=redis://default:<YOUR_UPSTASH_PASSWORD>@<YOUR_UPSTASH_HOST>:6379

# JWT Configuration (Generate a strong secret)
JWT_SECRET_KEY=your-very-secret-key-generate-with-secrets-library
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Groq LLM API
GROQ_API_KEY=your-groq-api-key-from-groq-console
GROQ_MODEL=openai/gpt-oss-120b

# LLM Settings
LLM_ANSWER_GENERATION_ENABLED=true
LLM_MAX_TOKENS=512
LLM_TEMPERATURE=0.3

# CORS (Update with your Vercel frontend domain)
CORS_ORIGINS=https://cipherdocs.vercel.app,https://www.your-domain.com,http://localhost:3000

# Document Processing
CHUNK_SIZE=700
CHUNK_OVERLAP=100
DEFAULT_TOP_K=7
MAX_TOP_K=15

# Vector Encryption
CYBORG_EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# File Upload
MAX_UPLOAD_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,txt,docx

# Email (if needed)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# AWS S3 (if using S3 for document storage)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=your-bucket-name
AWS_S3_REGION=us-east-1

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8001

---

## Frontend Environment Variables for Vercel

# API Configuration
REACT_APP_API_BASE_URL=https://cipherdocs-backend.onrender.com
REACT_APP_ENVIRONMENT=production
REACT_APP_LOG_LEVEL=info
REACT_APP_API_TIMEOUT=30000

# Optional: Analytics
REACT_APP_ANALYTICS_ENABLED=true
REACT_APP_SENTRY_DSN=your-sentry-dsn

---

## How to Set These Variables

### For Render Backend:
1. Go to Render Dashboard
2. Select your service
3. Go to Settings → Environment
4. Add each variable
5. Save and redeploy

### For Vercel Frontend:
1. Go to Vercel Dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add each variable
5. Redeploy

---

## Generating Secure Keys

### JWT Secret Key (Run in Python):
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Generate in Backend:
```bash
cd backend
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Pre-Deployment Checklist

- [ ] All environment variables documented
- [ ] Secret keys generated and secured
- [ ] Database URL obtained from Render
- [ ] Redis URL obtained from Render
- [ ] Groq API key ready
- [ ] Frontend domain/URL known
- [ ] CORS origins configured
- [ ] Database migrations tested locally
- [ ] Gunicorn added to requirements.txt
- [ ] render.yaml created
- [ ] vercel.json created
- [ ] Code committed to GitHub
- [ ] GitHub repository connected to both Render and Vercel
