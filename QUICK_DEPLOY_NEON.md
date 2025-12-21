# 🚀 Quick Start: Deploy with Neon to Render + Vercel

**Time Estimate: 30 minutes total**

## ✅ Pre-Flight Checklist (2 minutes)

```bash
# 1. Have these open/ready:
- Neon Console: https://console.neon.tech
- Render Dashboard: https://dashboard.render.com
- Vercel Dashboard: https://vercel.com/dashboard
- GitHub Repository: your-repo-url
- Groq Console: https://console.groq.com

# 2. Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output - this is your JWT_SECRET_KEY
```

---

## 🗄️ Step 1: Get Neon Connection String (3 minutes)

1. Open https://console.neon.tech
2. Click your project name
3. Click **"Connection string"** button
4. Copy the connection string (PostgreSQL format):
   ```
   postgresql://user:password@ep-xxxxx.us-east-1.neon.tech/cipherdocs_db?sslmode=require
   ```
5. **Save this** - you'll need it in Step 3

---

## 🔧 Step 2: Deploy Backend to Render (15 minutes)

### Create Web Service

1. Open https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Select your GitHub repo → **"Connect"**
4. Branch: `main`
5. Fill in these settings:

| Field | Value |
|-------|-------|
| Name | `cipherdocs-backend` |
| Runtime | `Python 3.11` |
| Build Command | `pip install -r requirements.txt && alembic upgrade head` |
| Start Command | `gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:$PORT` |
| Plan | **Standard** ($7/month) |

### Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**, then add these:

```
ENVIRONMENT                = production
DEBUG                      = false
LOG_LEVEL                  = INFO
DATABASE_URL               = [PASTE YOUR NEON CONNECTION STRING]
JWT_SECRET_KEY             = [PASTE YOUR GENERATED SECRET]
GROQ_API_KEY               = [YOUR GROQ API KEY]
CORS_ORIGINS               = https://cipherdocs.vercel.app,http://localhost:3000
```

### Deploy

6. Click **"Create Web Service"**
7. **Wait 5-10 minutes** for deployment
8. Check logs for errors (Logs tab)
9. When complete, copy your backend URL:
   - Format: `https://cipherdocs-backend.onrender.com`
   - **Save this** - you'll need it in Step 3

### Verify Backend is Working

```bash
# Test in browser or terminal
curl https://cipherdocs-backend.onrender.com/health

# Should return: {"status": "healthy"}
```

---

## 🎨 Step 3: Deploy Frontend to Vercel (10 minutes)

### Create Project

1. Open https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. **"Import Git Repository"** → select your repo
4. **Root Directory**: `frontend`
5. Click **"Continue"**

### Configure Build

| Setting | Value |
|---------|-------|
| Framework | Create React App |
| Build Command | `npm run build` |
| Output Directory | `build` |

### Add Environment Variables

Under **"Environment Variables"**, add:

```
REACT_APP_API_BASE_URL  = https://cipherdocs-backend.onrender.com
REACT_APP_ENVIRONMENT   = production
```

(Replace with your actual Render URL from Step 2)

### Deploy

6. Click **"Deploy"**
7. **Wait 2-3 minutes** for build and deployment
8. When complete, copy your frontend URL:
   - Format: `https://cipherdocs.vercel.app`

---

## ✨ Step 4: Update CORS (1 minute)

Now that you have your Vercel frontend URL, update the backend:

1. Go back to **Render Dashboard** → `cipherdocs-backend`
2. Click **"Settings"** → **"Environment"**
3. Find `CORS_ORIGINS`
4. Update to: `https://cipherdocs.vercel.app,http://localhost:3000`
5. Click **"Save"** (auto-redeploys)

---

## 🧪 Step 5: Verify Everything Works (3 minutes)

### Test Backend
```bash
curl https://cipherdocs-backend.onrender.com/health
# Should return: {"status": "healthy"}
```

### Test Frontend
1. Open https://cipherdocs.vercel.app in browser
2. Open Developer Console (F12)
3. Try to **login**
4. Check for errors in console

### Test Full Flow
1. Login successfully
2. Upload a document
3. Search for something
4. Get LLM answer with sources

**✅ If all 3 work, you're done!**

---

## 🆘 Troubleshooting

### "502 Bad Gateway" from Render

**Check:**
1. Wait 2 more minutes (first deploy can be slow)
2. Render Logs: Check for `DATABASE_URL` connection errors
3. Verify Neon connection string is correct (copy-paste again)
4. Check Neon database is accessible

### CORS Errors in Browser

**Fix:**
1. Make sure `CORS_ORIGINS` in Render exactly matches your Vercel URL
2. Save and wait 1 minute for Render to redeploy
3. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)

### Frontend not connecting to backend

**Fix:**
1. Verify `REACT_APP_API_BASE_URL` in Vercel has your Render URL
2. Hard refresh browser
3. Check browser console for actual error message

### Database migration failed

**Check:**
1. Verify DATABASE_URL is correct from Neon console
2. Check Neon database is running (https://console.neon.tech)
3. Try redeploying from Render

---

## 📊 Verify Deployment

| Component | Check | Status |
|-----------|-------|--------|
| Backend Running | Render dashboard shows "Live" | ✅ |
| Frontend Running | Vercel dashboard shows "Ready" | ✅ |
| Database Connected | Backend logs show no DB errors | ✅ |
| API Working | `/health` endpoint returns 200 | ✅ |
| CORS Configured | Frontend can call backend | ✅ |
| Login Works | Can authenticate users | ✅ |
| Search Works | Can query documents | ✅ |
| LLM Works | Gets answers from Groq | ✅ |

---

## 💰 Your Costs

| Service | Cost | Notes |
|---------|------|-------|
| Render Backend | $7/month | Standard plan |
| Neon Database | Included | Your existing |
| Vercel Frontend | Free | Hobby tier |
| **Total** | **~$7/month** | Very affordable! |

---

## 🎉 You're Done!

Your application is now live in production:

- **Frontend**: https://cipherdocs.vercel.app
- **Backend**: https://cipherdocs-backend.onrender.com
- **Database**: Neon PostgreSQL (external)

**Auto-deployments are enabled:**
- Push to GitHub → Render auto-deploys backend
- Push to GitHub → Vercel auto-deploys frontend

---

## 📚 Next Steps

1. ✅ Monitor logs regularly
2. ✅ Share frontend URL with users
3. ✅ Set up monitoring/alerts (optional)
4. ✅ Add custom domain (optional)
5. ✅ Plan scaling strategy

**Need help?**
- Render: https://render.com/docs
- Vercel: https://vercel.com/docs
- Neon: https://neon.tech/docs

---

**Deployment completed!** 🎊
