# Deployment Guide - CipherDocs

## Backend Deployment (Render)

### Prerequisites
- Render account (https://render.com)
- GitHub repository with your code
- Environment variables ready

### Step 1: Prepare Backend for Production

#### Update Configuration
Update `backend/app/core/config.py` for production settings:

```python
# Set in production environment
ENVIRONMENT = "production"
DEBUG = False
LOG_LEVEL = "INFO"
```

#### Database Setup (Use Existing Neon PostgreSQL)
- Get your existing Neon PostgreSQL connection string from: https://console.neon.tech
- Navigate to your project and copy the PostgreSQL connection URL
- This will be your `DATABASE_URL` (no need to create new database)

#### Redis Setup (Upstash - Already Configured ✅)
- Using Upstash Redis (cloud-hosted)
- Connection string: Set `REDIS_URL` in Render dashboard from your Upstash console (keep private!)
- No additional setup needed

### Step 2: Deploy Backend to Render

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for production deployment"
   git push origin main
   ```

2. **Connect to Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select branch (main/master)

3. **Configure Render Service**
   - **Name**: `cipherdocs-backend`
   - **Runtime**: Python 3.11+
   - **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command**: `gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:$PORT`
   - **Plan**: Standard ($7/month) or Pro

4. **Set Environment Variables** in Render Dashboard:
   ```
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=INFO
   DATABASE_URL=<postgresql_url>
   REDIS_URL=<redis_url>
   JWT_SECRET_KEY=<your-secret-key>
   GROQ_API_KEY=<your-groq-api-key>
   CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://www.your-domain.com
   ```

5. **Database Migrations**
   - Render will run `alembic upgrade head` during build
   - Verify migrations completed successfully in logs

6. **Get Backend URL**
   - After deployment, Render provides a URL like: `https://cipherdocs-backend.onrender.com`
   - Save this for frontend configuration

---

## Frontend Deployment (Vercel)

### Prerequisites
- Vercel account (https://vercel.com)
- GitHub repository with your code

### Step 1: Prepare Frontend for Production

#### Create `frontend/.env.production`
```env
REACT_APP_API_BASE_URL=https://cipherdocs-backend.onrender.com
REACT_APP_ENVIRONMENT=production
```

#### Update API Configuration
Edit `frontend/src/config/api.js` or similar:
```javascript
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
export const API_ENDPOINTS = {
  SEARCH: `${API_BASE_URL}/api/v1/search`,
  SEARCH_ADVANCED: `${API_BASE_URL}/api/v1/search/advanced`,
  DOCUMENTS: `${API_BASE_URL}/api/v1/documents`,
  AUTH: `${API_BASE_URL}/api/v1/auth`,
  // ... other endpoints
};
```

#### Create `frontend/vercel.json`
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "env": {
    "REACT_APP_API_BASE_URL": "@react_app_api_base_url"
  },
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### Step 2: Deploy Frontend to Vercel

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare frontend for production"
   git push origin main
   ```

2. **Connect to Vercel**
   - Go to https://vercel.com/dashboard
   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - Select the project folder: `frontend` (if monorepo)

3. **Configure Build Settings**
   - **Framework Preset**: Create React App
   - **Build Command**: `npm run build` (or `yarn build`)
   - **Output Directory**: `build`
   - **Install Command**: `npm install` (or `yarn install`)

4. **Set Environment Variables** in Vercel Project Settings:
   ```
   REACT_APP_API_BASE_URL=https://cipherdocs-backend.onrender.com
   REACT_APP_ENVIRONMENT=production
   ```

5. **Custom Domain** (Optional)
   - Go to Project Settings → Domains
   - Add your custom domain
   - Configure DNS records as instructed by Vercel

6. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy your frontend
   - Get the production URL (e.g., https://cipherdocs.vercel.app)

---

## Post-Deployment Configuration

### Step 1: Update Backend CORS

Update `backend/app/core/config.py`:
```python
CORS_ORIGINS = [
    "https://cipherdocs.vercel.app",
    "https://www.your-domain.com",
    "http://localhost:3000",  # Development
]
```

### Step 2: Verify Connectivity

Test the API from frontend:
```javascript
// In frontend console
fetch('https://cipherdocs-backend.onrender.com/health')
  .then(r => r.json())
  .then(d => console.log(d))
```

### Step 3: Monitor Logs

- **Backend**: Render Dashboard → Service Logs
- **Frontend**: Vercel Dashboard → Deployments → Logs

---

## Common Issues & Solutions

### Issue 1: CORS Errors
**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**:
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 2: Cold Start Delays
**Problem**: First request takes 10-30 seconds

**Solution**: 
- Use Render's paid plans for faster CPU
- Implement connection pooling for database

### Issue 3: Environment Variables Not Loading
**Solution**:
- Verify env vars in Render/Vercel dashboard
- Check `.env` files are not committed
- Restart services after updating env vars

### Issue 4: Database Migrations Failing
**Solution**:
```bash
# Manually run in Render shell
alembic upgrade head
```

### Issue 5: Static Files Not Loading (Frontend)
**Solution**: Ensure `public/` folder is included in build

---

## Production Checklist

- [ ] Backend environment variables set in Render
- [ ] Frontend environment variables set in Vercel
- [ ] Database migrations completed successfully
- [ ] CORS properly configured for frontend domain
- [ ] SSL/TLS certificates auto-configured (both platforms provide this)
- [ ] Error logging configured
- [ ] Health checks passing
- [ ] API connectivity verified
- [ ] User authentication working
- [ ] Search functionality tested
- [ ] LLM integration tested
- [ ] Document upload working
- [ ] Analytics tracking enabled

---

## Maintenance

### View Logs
- **Render Backend**: Dashboard → Service Logs
- **Vercel Frontend**: Dashboard → Deployments → Logs

### Update Code
```bash
git add .
git commit -m "Update features"
git push origin main
# Both Render and Vercel auto-redeploy on push
```

### Rollback
- **Render**: Dashboard → Deploys → Select previous version
- **Vercel**: Dashboard → Deployments → Redeploy previous

---

## Cost Estimate

- **Render Backend**: $7/month (Starter) - $20+/month (Standard)
- **Neon PostgreSQL**: Included with your existing plan
- **Render Redis** (Optional): $5/month (Starter) - $30+/month (Production)
- **Vercel Frontend**: Free tier available ($20/month for Pro features)

**Total Starting Cost**: ~$7-12/month (using your existing Neon database)

---

## Support & Resources

- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- FastAPI Production: https://fastapi.tiangolo.com/deployment/
- React Production: https://create-react-app.dev/docs/deployment/
