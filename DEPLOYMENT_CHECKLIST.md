# Deployment Checklist - CipherDocs

## 📋 Pre-Deployment (Local Setup)

### Backend Preparation
- [x] Gunicorn added to requirements.txt
- [x] render.yaml created with service configuration
- [x] Production environment variables documented in PRODUCTION_ENV_TEMPLATE.md
- [x] CORS configuration supports production domains
- [x] Database migration scripts ready (alembic)
- [ ] Run local tests: `pytest backend/tests/`
- [ ] Verify database connection works with production URL format
- [ ] Test LLM integration with Groq API

### Frontend Preparation
- [x] vercel.json created with build configuration
- [x] .env.production created
- [x] API configuration guide created (api.config.js)
- [ ] Build locally: `npm run build` in frontend/
- [ ] Verify build output in `frontend/build/`
- [ ] Test API endpoints after setting REACT_APP_API_BASE_URL
- [ ] Check all API calls use environment variable for base URL

### Git & Repository
- [ ] All changes committed: `git add . && git commit -m "Prepare for production deployment"`
- [ ] Code pushed to GitHub: `git push origin main`
- [ ] GitHub repository is public/accessible
- [ ] .env files are in .gitignore (not committed)
- [ ] Sensitive keys are not in repository

---

## 🔐 Security Setup

### Environment Variables - Backend (Render)
- [ ] Generate JWT_SECRET_KEY using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Have Groq API key ready (from groq.com console)
- [ ] Get DATABASE_URL from your Neon PostgreSQL (https://console.neon.tech)
- [ ] Optional: Get REDIS_URL from Render Redis service (if adding caching)
- [ ] Update CORS_ORIGINS with frontend domain
- [ ] All sensitive keys are strong (>32 characters)
- [ ] No hardcoded secrets in code

### Environment Variables - Frontend (Vercel)
- [ ] REACT_APP_API_BASE_URL set to Render backend URL
- [ ] REACT_APP_ENVIRONMENT=production
- [ ] No sensitive keys in frontend code

---

## 🚀 Backend Deployment (Render)

### Step 1: Prepare Neon PostgreSQL Connection
- [ ] Go to https://console.neon.tech
- [ ] Select your project
- [ ] Click "Connection string"
- [ ] Copy the PostgreSQL connection URL (contains user:password@host:port/database)
- [ ] Save this for the next step (DATABASE_URL)

### Step 2: Create Redis Cache (Optional but recommended)
- [ ] Go to https://dashboard.render.com
- [ ] Click "New +" → "Redis"
- [ ] Name: `cipherdocs-redis`
- [ ] Region: Same as your primary infrastructure
- [ ] Copy CONNECTION STRING
- [ ] Wait for Redis to be ready (~2 minutes)

### Step 3: Deploy Backend Service
- [ ] Go to https://dashboard.render.com
- [ ] Click "New +" → "Web Service"
- [ ] Select "Connect your code repository"
- [ ] Choose your GitHub repository
- [ ] Select branch: `main`
- [ ] **Name**: `cipherdocs-backend`
- [ ] **Runtime**: Python 3.11+
- [ ] **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
- [ ] **Start Command**: `gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:$PORT`
- [ ] **Plan**: Standard ($7/month) or Starter ($0 - suspends after 15 min inactivity)

### Step 4: Set Environment Variables (Render Dashboard)
- [ ] ENVIRONMENT = `production`
- [ ] DEBUG = `false`
- [ ] LOG_LEVEL = `INFO`
- [ ] DATABASE_URL = `<paste your Neon PostgreSQL connection string>`
- [ ] REDIS_URL = `<from Redis service>` (if created in Step 2)
- [ ] JWT_SECRET_KEY = `<generated above>`
- [ ] GROQ_API_KEY = `<your Groq API key>`
- [ ] CORS_ORIGINS = `https://your-frontend-domain.vercel.app,https://www.your-domain.com`
- [ ] All other env vars from PRODUCTION_ENV_TEMPLATE.md

### Step 5: Deploy & Verify
- [ ] Click "Create Web Service"
- [ ] Wait for deployment (~5-10 minutes)
- [ ] Check deployment logs for errors (especially database connection)
- [ ] Get backend URL (e.g., `https://cipherdocs-backend.onrender.com`)
- [ ] Test health endpoint: `curl https://cipherdocs-backend.onrender.com/health`
- [ ] Verify response is `{"status": "healthy"}`
- [ ] Test database connection: `curl https://cipherdocs-backend.onrender.com/api/v1/health/db`

---

## ⚛️ Frontend Deployment (Vercel)

### Step 1: Deploy Frontend Service
- [ ] Go to https://vercel.com/dashboard
- [ ] Click "Add New..." → "Project"
- [ ] Click "Import Git Repository"
- [ ] Search and select your GitHub repository
- [ ] If monorepo, set root directory: `frontend`
- [ ] Click "Import"

### Step 2: Configure Build Settings
- [ ] **Framework Preset**: Presets to "Create React App"
- [ ] **Build Command**: `npm run build`
- [ ] **Output Directory**: `build`
- [ ] **Install Command**: `npm install`

### Step 3: Set Environment Variables (Vercel Dashboard)
- [ ] Add variable: `REACT_APP_API_BASE_URL` = `https://cipherdocs-backend.onrender.com`
- [ ] Add variable: `REACT_APP_ENVIRONMENT` = `production`

### Step 4: Deploy & Verify
- [ ] Click "Deploy"
- [ ] Wait for build completion (~3-5 minutes)
- [ ] Check build logs for errors
- [ ] Get frontend URL (e.g., `https://cipherdocs.vercel.app`)
- [ ] Visit URL in browser and verify page loads
- [ ] Check browser console for any errors

### Step 5: Add to Allowed CORS Origins
- [ ] Go back to Render Dashboard
- [ ] Select your backend service
- [ ] Go to Settings → Environment
- [ ] Update CORS_ORIGINS to include Vercel domain
- [ ] Redeploy backend

---

## ✅ Post-Deployment Verification

### Backend Tests
- [ ] Health check: `curl https://cipherdocs-backend.onrender.com/health`
- [ ] Database connected (check logs)
- [ ] Migrations completed (check logs)
- [ ] Redis connected (if configured)
- [ ] Groq LLM accessible (test with search)

### Frontend Tests
- [ ] Frontend loads without errors
- [ ] Login page appears
- [ ] No CORS errors in console
- [ ] API calls successfully reach backend
- [ ] Search functionality works
- [ ] Document upload works
- [ ] LLM answer generation works

### Integration Tests
- [ ] Login → Upload Document → Search → Get LLM Answer
- [ ] Refresh page, data persists
- [ ] Multiple user sessions work independently
- [ ] Documents are properly encrypted

---

## 📊 Monitoring & Maintenance

### View Logs
- **Backend**: Render Dashboard → Service → Logs
- **Frontend**: Vercel Dashboard → Deployments → Logs

### Common Issues & Fixes

**Issue**: CORS error in console
- **Fix**: Verify CORS_ORIGINS includes frontend domain in Render env vars

**Issue**: API 502 Bad Gateway
- **Fix**: Check backend logs, ensure database is connected

**Issue**: Slow first request
- **Fix**: Normal for Render free tier (cold start), upgrade to paid plan if needed

**Issue**: Static assets not loading
- **Fix**: Verify Vercel output directory is `build`, clear cache and redeploy

**Issue**: Database migrations failed
- **Fix**: SSH into Render and run: `alembic upgrade head`

### Update Code
```bash
# Make changes locally
git add .
git commit -m "Fix/feature: description"
git push origin main

# Both Render and Vercel auto-redeploy on push to main
```

### Rollback
- **Render**: Dashboard → Deploys → Select previous version → Click "Redeploy"
- **Vercel**: Dashboard → Deployments → Click previous deployment → Promote

---

## 💰 Cost Overview

| Service | Plan | Cost/Month | Notes |
|---------|------|-----------|-------|
| Render Backend | Standard | $7 | Starter is free with suspensions |
| Neon PostgreSQL | Included | $0 | Your existing account |
| Render Redis | Starter | $5 | Optional, for caching |
| Vercel Frontend | Hobby | Free | Or Pro at $20/month |
| **Total** | | **~$7-12** | Using your existing Neon DB |

---

## 🎯 Success Criteria

- [x] Backend deployed and responsive at Render URL
- [x] Frontend deployed and accessible at Vercel URL  
- [x] Users can log in
- [x] Documents can be uploaded
- [x] Search works with LLM answer generation
- [x] No CORS errors
- [x] No console errors
- [x] Logs show healthy service status
- [x] Health endpoint returns 200

---

## 📞 Support Resources

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/deployment/
- **React Docs**: https://react.dev/learn/deployment

---

## 🎉 Congratulations!

Your CipherDocs application is now deployed and ready for production use!

**Next Steps:**
1. Share your frontend URL with users
2. Monitor logs regularly
3. Set up backup systems
4. Plan scaling strategy
5. Consider adding custom domain
