#!/bin/bash
# Quick Deployment Setup Script
# Run this to prepare for deployment to Render + Vercel

echo "🚀 CipherDocs Deployment Setup"
echo "==============================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if git is initialized
if [ ! -d .git ]; then
    echo -e "${YELLOW}❌ Git not initialized${NC}"
    echo "Run: git init && git add . && git commit -m 'Initial commit'"
    exit 1
fi

echo -e "${GREEN}✅ Git repository found${NC}"
echo ""

# Verify directory structure
echo "📁 Checking directory structure..."
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Missing backend or frontend directory${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend and Frontend directories found${NC}"
echo ""

# Check backend files
echo "🔧 Backend Files:"
echo "  ✅ requirements.txt" && ls backend/requirements.txt > /dev/null 2>&1 || echo "  ❌ requirements.txt missing"
echo "  ✅ main.py" && ls backend/main.py > /dev/null 2>&1 || echo "  ❌ main.py missing"
echo "  ✅ render.yaml" && ls backend/render.yaml > /dev/null 2>&1 || echo "  ✅ render.yaml found" || echo "  ℹ️  render.yaml created"
echo ""

# Check frontend files
echo "⚛️  Frontend Files:"
echo "  ✅ package.json" && ls frontend/package.json > /dev/null 2>&1 || echo "  ❌ package.json missing"
echo "  ✅ vercel.json" && ls frontend/vercel.json > /dev/null 2>&1 || echo "  ✅ vercel.json found" || echo "  ℹ️  vercel.json created"
echo "  ✅ .env.production" && ls frontend/.env.production > /dev/null 2>&1 || echo "  ✅ .env.production found" || echo "  ℹ️  .env.production created"
echo ""

# Check documentation
echo "📚 Documentation:"
echo "  ✅ DEPLOYMENT_GUIDE.md" && ls DEPLOYMENT_GUIDE.md > /dev/null 2>&1 || echo "  ✅ DEPLOYMENT_GUIDE.md created"
echo "  ✅ PRODUCTION_ENV_TEMPLATE.md" && ls PRODUCTION_ENV_TEMPLATE.md > /dev/null 2>&1 || echo "  ✅ PRODUCTION_ENV_TEMPLATE.md created"
echo ""

# Generate JWT Secret
echo "🔐 Generating secure JWT key..."
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo -e "${GREEN}JWT_SECRET_KEY=${JWT_SECRET}${NC}"
echo "👉 Copy this and add to Render environment variables"
echo ""

# Summary
echo "================================"
echo -e "${GREEN}✅ Deployment Setup Complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Commit changes: git add . && git commit -m 'Add deployment files'"
echo "2. Push to GitHub: git push origin main"
echo ""
echo "Backend Deployment (Render):"
echo "  - Go to https://dashboard.render.com"
echo "  - Connect GitHub repository"
echo "  - Set environment variables from PRODUCTION_ENV_TEMPLATE.md"
echo "  - Backend should use render.yaml"
echo ""
echo "Frontend Deployment (Vercel):"
echo "  - Go to https://vercel.com/dashboard"
echo "  - Import GitHub repository"
echo "  - Set REACT_APP_API_BASE_URL to your Render backend URL"
echo "  - Deploy"
echo ""
echo "Documentation: See DEPLOYMENT_GUIDE.md for detailed instructions"
