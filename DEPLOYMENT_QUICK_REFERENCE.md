# CipherDocs Deployment - Quick Reference

## 🚀 One-Page Deployment Guide

### Prerequisites Checklist
```
✅ GitHub account & repository
✅ Render account (render.com)
✅ Vercel account (vercel.com)
✅ Neon PostgreSQL account with connection string ready
✅ Groq API key
✅ All code committed to main branch
```

---

## 📋 Step-by-Step Summary

### STEP 1: Backend to Render (10 minutes)
```
1. Get Neon Connection String:
   - Go: https://console.neon.tech
   - Copy PostgreSQL connection URL
   
2. Deploy to Render:
   - Go: https://dashboard.render.com
   - New → Web Service
   - Connect GitHub repo, select branch (main)
   - Name: cipherdocs-backend
   - Runtime: Python 3.11
   - Build: pip install -r requirements.txt && alembic upgrade head
   - Start: gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:$PORT
   
3. Set Environment Variables:
   - ENVIRONMENT=production
   - DEBUG=false
   - DATABASE_URL=<paste your Neon connection string>
   - JWT_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
   - GROQ_API_KEY=<your-groq-api-key>
   - CORS_ORIGINS=https://cipherdocs.vercel.app (update later)
   
4. Deploy ✅
5. Copy backend URL: https://cipherdocs-backend.onrender.com
```

### STEP 2: Frontend to Vercel (5 minutes)
```
1. Go: https://vercel.com/dashboard
2. Add New → Project
3. Import GitHub repository
4. Root directory: frontend
5. Framework: Create React App
6. Set Environment Variables:
   - REACT_APP_API_BASE_URL=https://cipherdocs-backend.onrender.com
   - REACT_APP_ENVIRONMENT=production
7. Deploy ✅
8. Copy frontend URL: https://cipherdocs.vercel.app
```

### STEP 3: Update CORS (2 minutes)
```
1. Go: Render Dashboard → cipherdocs-backend
2. Settings → Environment
3. Update CORS_ORIGINS to:
   CORS_ORIGINS=https://cipherdocs.vercel.app,http://localhost:3000
4. Save & Redeploy ✅
```

---

## 🧪 Verification Tests

```bash
# Test Backend
curl https://cipherdocs-backend.onrender.com/health
# Expected: {"status": "healthy"}

# Test Frontend
# 1. Open https://cipherdocs.vercel.app in browser
# 2. Check console for errors
# 3. Try login
```

---

## 📁 Files Created for Deployment

```
backend/
├── render.yaml                 # Render configuration
└── requirements.txt            # Updated with gunicorn

frontend/
├── vercel.json                 # Vercel configuration
├── .env.production            # Production environment
└── src/config/api.config.js   # API endpoints

Root/
├── DEPLOYMENT_GUIDE.md        # Full deployment instructions
├── DEPLOYMENT_CHECKLIST.md    # Step-by-step checklist
├── PRODUCTION_ENV_TEMPLATE.md # Environment variable template
├── deploy.sh                  # Linux/Mac deployment script
└── deploy.bat                 # Windows deployment script
```

---

## 🔑 Important URLs After Deployment

```
Backend:  https://cipherdocs-backend.onrender.com
Frontend: https://cipherdocs.vercel.app
Render:   https://dashboard.render.com
Vercel:   https://vercel.com/dashboard
```

---

## ⚠️ Common Issues

| Issue | Solution |
|-------|----------|
| CORS Error | Update CORS_ORIGINS in Render env vars to include Vercel domain |
| 502 Bad Gateway | Check backend logs, ensure database connected |
| "Cannot find module" | Ensure requirements.txt has all dependencies |
| Slow first load | Normal for free tier, upgrade to paid for faster |
| Static files missing | Check Vercel output directory is `build` |

---

## 🔄 Update Workflow

```bash
# Make changes locally
git add .
git commit -m "Feature: description"
git push origin main

# Both Render and Vercel auto-redeploy!
```

---

## 📊 Monitoring

```
Render Logs:  Dashboard → Service → Logs
Vercel Logs:  Dashboard → Deployments → Logs
Render Metrics: Dashboard → Service → Metrics
```

---

## 💡 Pro Tips

1. **Keep .env files in .gitignore** - Never commit secrets
2. **Use strong JWT secrets** - Run secrets generation script
3. **Monitor first deployment** - Watch logs for migrations
4. **Test endpoints after deploy** - Use Postman or curl
5. **Set up error tracking** - Consider Sentry for production
6. **Regular backups** - Render provides database backups
7. **Custom domain** - Add later in Vercel/Render settings

---

## 🎯 Typical Deploy Time

- Backend: 5-10 minutes (including migrations)
- Frontend: 3-5 minutes
- Total: 10-15 minutes

---

## ✅ After Deployment

1. ✅ Verify health endpoint
2. ✅ Test login flow
3. ✅ Test document upload
4. ✅ Test search with LLM
5. ✅ Share frontend URL with users
6. ✅ Monitor logs for errors
7. ✅ Set up regular backups
8. ✅ Consider custom domain setup

---

## 📞 Help & Documentation

- Full Guide: See `DEPLOYMENT_GUIDE.md`
- Checklist: See `DEPLOYMENT_CHECKLIST.md`
- Env Template: See `PRODUCTION_ENV_TEMPLATE.md`
- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs

---

**Questions?** Check the deployment guide files or contact support.
