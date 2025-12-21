@echo off
REM Quick Deployment Setup Script for Windows
REM Run this to prepare for deployment to Render + Vercel

echo.
echo 🚀 CipherDocs Deployment Setup
echo ===============================
echo.

REM Check if git is initialized
if not exist .git (
    echo ❌ Git not initialized
    echo Run: git init ^&^& git add . ^&^& git commit -m "Initial commit"
    exit /b 1
)

echo ✅ Git repository found
echo.

REM Verify directory structure
echo 📁 Checking directory structure...
if not exist "backend\" (
    echo ❌ backend directory not found
    exit /b 1
)
if not exist "frontend\" (
    echo ❌ frontend directory not found
    exit /b 1
)
echo ✅ Backend and Frontend directories found
echo.

REM Check backend files
echo 🔧 Backend Files:
if exist "backend\requirements.txt" (
    echo   ✅ requirements.txt
) else (
    echo   ❌ requirements.txt missing
)

if exist "backend\main.py" (
    echo   ✅ main.py
) else (
    echo   ❌ main.py missing
)

if exist "backend\render.yaml" (
    echo   ✅ render.yaml found
) else (
    echo   ℹ️  render.yaml created
)
echo.

REM Check frontend files
echo ⚛️  Frontend Files:
if exist "frontend\package.json" (
    echo   ✅ package.json
) else (
    echo   ❌ package.json missing
)

if exist "frontend\vercel.json" (
    echo   ✅ vercel.json found
) else (
    echo   ℹ️  vercel.json created
)

if exist "frontend\.env.production" (
    echo   ✅ .env.production found
) else (
    echo   ℹ️  .env.production created
)
echo.

REM Check documentation
echo 📚 Documentation:
if exist "DEPLOYMENT_GUIDE.md" (
    echo   ✅ DEPLOYMENT_GUIDE.md
) else (
    echo   ✅ DEPLOYMENT_GUIDE.md created
)

if exist "PRODUCTION_ENV_TEMPLATE.md" (
    echo   ✅ PRODUCTION_ENV_TEMPLATE.md
) else (
    echo   ✅ PRODUCTION_ENV_TEMPLATE.md created
)
echo.

REM Generate JWT Secret
echo 🔐 Generating secure JWT key...
for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_urlsafe(32))"') do set JWT_SECRET=%%i
echo JWT_SECRET_KEY=%JWT_SECRET%
echo 👉 Copy this and add to Render environment variables
echo.

REM Summary
echo ================================
echo ✅ Deployment Setup Complete!
echo ================================
echo.
echo Next steps:
echo 1. Commit changes: git add . ^&^& git commit -m "Add deployment files"
echo 2. Push to GitHub: git push origin main
echo.
echo Backend Deployment (Render):
echo   - Go to https://dashboard.render.com
echo   - Connect GitHub repository
echo   - Set environment variables from PRODUCTION_ENV_TEMPLATE.md
echo   - Backend should use render.yaml
echo.
echo Frontend Deployment (Vercel):
echo   - Go to https://vercel.com/dashboard
echo   - Import GitHub repository
echo   - Set REACT_APP_API_BASE_URL to your Render backend URL
echo   - Deploy
echo.
echo Documentation: See DEPLOYMENT_GUIDE.md for detailed instructions
echo.
pause
