# CipherDocs Deployment with Neon PostgreSQL
## Complete Setup Guide

---

## 🎯 Overview

Your deployment architecture:
- **Frontend**: React app hosted on Vercel
- **Backend**: FastAPI app hosted on Render
- **Database**: Your existing Neon PostgreSQL (external)
- **Cache**: Optional Redis (Render or external)

This simplified setup reduces costs and complexity by reusing your existing Neon database.

---

## 📋 Pre-Deployment Checklist

### 1. Gather Required Information

**From Neon Console** (https://console.neon.tech):
```
☐ PostgreSQL Connection String (looks like):
  postgresql://user:password@ep-xxx.us-east-1.neon.tech/cipherdocs_db?sslmode=require
```

**From Groq Console** (https://console.groq.com):
```
☐ GROQ_API_KEY
```

**Generate New Secrets**:
```bash
# Generate JWT secret (run in terminal/PowerShell)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Verify Code is Ready

```bash
# Make sure all changes are committed
git add .
git commit -m "Ready for production deployment"
git push origin main
```

### 3. Create Accounts

```
☐ Render account: https://render.com
☐ Vercel account: https://vercel.com
☐ GitHub connected to both platforms
```

---

## 🚀 Step 1: Deploy Backend to Render

### 1a. Create Render Web Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Select your GitHub repository
4. Choose **"main"** branch
5. Click **"Connect"**

### 1b. Configure Service Settings

| Setting | Value |
|---------|-------|
| **Name** | `cipherdocs-backend` |
| **Runtime** | `Python 3.11+` |
| **Build Command** | `pip install -r requirements.txt && alembic upgrade head` |
| **Start Command** | `gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:$PORT` |
| **Plan** | Standard ($7/month) |

### 1c. Set Environment Variables

Click **"Environment"** section and add these variables:

```
ENVIRONMENT                = production
DEBUG                      = false
LOG_LEVEL                  = INFO
DATABASE_URL               = <paste your Neon connection string>
REDIS_URL                  = (leave empty or set if you want caching)
JWT_SECRET_KEY             = <your generated secret>
GROQ_API_KEY               = <your Groq API key>
CORS_ORIGINS               = https://cipherdocs.vercel.app,http://localhost:3000
```

### 1d. Deploy

1. Review all settings
2. Click **"Create Web Service"**
3. Wait for deployment (2-3 minutes)
4. Check build logs for any errors
5. Once deployed, copy your backend URL (e.g., `https://cipherdocs-backend.onrender.com`)

### 1e. Verify Backend

```bash
# Test in browser or terminal
curl https://cipherdocs-backend.onrender.com/health

# Expected response
{"status": "healthy"}
```

---

## 🎨 Step 2: Deploy Frontend to Vercel

### 2a. Create Vercel Project

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Select your GitHub repository
5. Click **"Import"**

### 2b. Configure Build Settings

| Setting | Value |
|---------|-------|
| **Framework Preset** | Create React App |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `build` |

### 2c. Set Environment Variables

In Project Settings → Environment Variables, add:

```
REACT_APP_API_BASE_URL    = https://cipherdocs-backend.onrender.com
REACT_APP_ENVIRONMENT     = production
```

### 2d. Deploy

1. Review all settings
2. Click **"Deploy"**
3. Wait for build and deployment (1-2 minutes)
4. Once complete, copy your frontend URL (e.g., `https://cipherdocs.vercel.app`)

### 2e. Update Backend CORS

1. Go back to Render Dashboard
2. Open your `cipherdocs-backend` service
3. Go to **"Environment"** section
4. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS = https://cipherdocs.vercel.app,http://localhost:3000
   ```
5. Click **"Save"** (Render auto-redeploys)

---

## ✅ Post-Deployment Verification

### Check Backend Health

```bash
curl https://your-backend-url.onrender.com/health
```

Expected response:
```json
{"status": "healthy"}
```

### Check Database Connection

```bash
curl https://your-backend-url.onrender.com/api/v1/health/db
```

Expected response:
```json
{"database": "connected"}
```

### Test Frontend

1. Open `https://your-frontend-url.vercel.app` in browser
2. Try to login
3. Check browser console (F12) for errors
4. Try uploading a document
5. Try searching and getting LLM responses

### Check Logs

**Backend Logs** (Render):
- Dashboard → Service → Logs

**Frontend Logs** (Vercel):
- Dashboard → Deployments → Logs tab

---

## 🔐 Security Considerations

### Database Connection
- ✅ Your Neon connection is SSL/TLS encrypted
- ✅ Credentials are secure in Render environment variables
- ✅ Connection string should never be in code

### API Keys
- ✅ JWT_SECRET_KEY is secure in Render environment variables
- ✅ GROQ_API_KEY is never exposed to frontend
- ✅ Frontend only receives signed JWT tokens

### CORS
- ✅ Only your Vercel domain can access backend
- ✅ Localhost included for development testing

---

## 💰 Cost Estimate

| Service | Cost | Details |
|---------|------|---------|
| **Render Backend** | $7/month | Python Standard plan |
| **Neon PostgreSQL** | Included | Your existing plan |
| **Vercel Frontend** | Free | Free tier sufficient |
| **Optional Redis** | $5+/month | Only if you add caching |
| **TOTAL** | **~$7/month** | Just backend + existing DB |

---

## 🐛 Troubleshooting

### Issue: "502 Bad Gateway" error

**Possible causes:**
1. Backend hasn't finished deploying (wait 2-3 minutes)
2. Environment variables not set correctly
3. Database connection string is wrong

**Solution:**
1. Check Render service logs: Dashboard → Logs
2. Verify DATABASE_URL is correct from Neon
3. Look for specific error messages in logs

### Issue: CORS errors in browser console

**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Solution:**
1. Check CORS_ORIGINS is set correctly in Render
2. Verify frontend URL matches exactly
3. Wait 1 minute for changes to take effect
4. Hard refresh browser (Ctrl+Shift+R)

### Issue: Database migrations failing

**Error:** `alembic upgrade head failed`

**Solution:**
1. Check DATABASE_URL connection string is correct
2. Verify Neon database is accessible
3. Check that user has proper permissions
4. Try running manually in Render shell

### Issue: Slow page loads

**Cause:** Render free/starter plan has limited resources

**Solution:**
1. Upgrade to Render Standard plan ($7+/month)
2. Implement caching with Redis
3. Optimize frontend bundle size

---

## 🔄 Updating Your Application

### Deploy Code Updates

```bash
# Make changes, then:
git add .
git commit -m "Your update message"
git push origin main

# Both Render and Vercel auto-deploy on push!
```

### Update Database Schema

If you modify models or add migrations:

```bash
# Locally create migration
alembic revision --autogenerate -m "Your change"

# Commit and push
git push origin main

# Render automatically runs: alembic upgrade head
```

---

## 🆘 Getting Help

### Documentation
- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Neon Docs**: https://neon.tech/docs
- **FastAPI Production**: https://fastapi.tiangolo.com/deployment/

### Support
- **Render Support**: https://render.com/contact
- **Vercel Support**: https://vercel.com/support
- **Neon Support**: https://neon.tech/contact

---

## ✨ Next Steps

1. ✅ Deploy backend to Render
2. ✅ Deploy frontend to Vercel
3. ✅ Verify all connections working
4. ✅ Add custom domain (optional)
5. ✅ Set up monitoring/alerts
6. ✅ Configure analytics
7. ✅ Update DNS records (if custom domain)

---

**Deployment Date**: [Your Date]
**Backend URL**: https://cipherdocs-backend.onrender.com
**Frontend URL**: https://cipherdocs.vercel.app
**Database**: Neon PostgreSQL (External)
