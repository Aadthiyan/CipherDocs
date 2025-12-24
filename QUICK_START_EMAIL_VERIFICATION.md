# Quick Start: Email Verification Setup

## ⚡ 5-Minute Setup Guide

### Step 1: Configure Gmail (2 minutes)

1. **Enable 2-Factor Authentication** on your Google Account
   - Go to: https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Click "Generate"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

3. **Update `.env` file**
   ```env
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=abcdefghijklmnop    # 16 chars, no spaces
   MAIL_FROM=your_email@gmail.com
   ```

### Step 2: Install & Migrate (2 minutes)

```bash
cd c:\Users\AADHITHAN\Downloads\Cipherdocs\backend

# Install dependencies
pip install -r requirements.txt

# Apply database migration
alembic upgrade head
```

### Step 3: Test (1 minute)

```bash
# Start backend
cd c:\Users\AADHITHAN\Downloads\Cipherdocs\backend
python main.py
```

Then test signup:
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_real_email@gmail.com",
    "password": "TestPass123!",
    "company_name": "Test Company"
  }'
```

**Check your email!** You'll receive a 6-digit code.

---

## 🧪 Complete Test Flow

### 1. Signup (Creates unverified user)
```powershell
$signupData = @{
    email = "test@example.com"
    password = "StrongPassword123!"
    company_name = "Test Company"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/signup" `
    -Method POST `
    -ContentType "application/json" `
    -Body $signupData
```

**Response:** User created, email sent with OTP

---

### 2. Try Login (Should Fail - Email Not Verified)
```powershell
$loginData = @{
    email = "test@example.com"
    password = "StrongPassword123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $loginData
```

**Response:** `403 Forbidden` - "Email not verified. Please check your email for the verification code."

---

### 3. Verify Email (Use code from email)
```powershell
$verifyData = @{
    email = "test@example.com"
    code = "123456"    # Replace with actual code from email
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/verify-email" `
    -Method POST `
    -ContentType "application/json" `
    -Body $verifyData
```

**Response:** JWT tokens + user info (now verified)

---

### 4. Login Again (Should Work)
```powershell
$loginData = @{
    email = "test@example.com"
    password = "StrongPassword123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $loginData
```

**Response:** Success! JWT tokens returned

---

### 5. Resend OTP (If code expired)
```powershell
$resendData = @{
    email = "test@example.com"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/resend-otp" `
    -Method POST `
    -ContentType "application/json" `
    -Body $resendData
```

**Response:** New OTP sent to email

---

## 🔍 Verify Database

Check user verification status:
```sql
-- Connect to your Neon database
SELECT 
    email, 
    is_verified, 
    verification_code, 
    code_expires_at,
    created_at
FROM users
WHERE email = 'test@example.com';
```

---

## 🚨 Troubleshooting

### Problem: "Failed to send verification email"

**Solution 1: Check Email Settings**
```powershell
# Test if environment variables are loaded
cd c:\Users\AADHITHAN\Downloads\Cipherdocs\backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'MAIL_USERNAME: {os.getenv(\"MAIL_USERNAME\")}'); print(f'MAIL_PASSWORD: {os.getenv(\"MAIL_PASSWORD\")[:4]}****')"
```

**Solution 2: Test SMTP Connection**
```python
# Create test file: test_smtp.py
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

try:
    server = smtplib.SMTP(os.getenv('MAIL_SERVER'), int(os.getenv('MAIL_PORT')))
    server.starttls()
    server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
    print("✅ SMTP connection successful!")
    server.quit()
except Exception as e:
    print(f"❌ SMTP error: {e}")
```

Run: `python test_smtp.py`

---

### Problem: Migration fails

**Solution:**
```bash
# Rollback and retry
cd c:\Users\AADHITHAN\Downloads\Cipherdocs\backend
alembic downgrade -1
alembic upgrade head
```

---

### Problem: Code expired

**Solution:**
1. Use resend endpoint: `POST /api/v1/auth/resend-otp`
2. Or increase expiration in `.env`: `OTP_EXPIRATION_MINUTES=30`

---

## 📧 Email Preview

Your users will receive:

```
Subject: Verify Your Email - CipherDocs

Hello Test Company,

Thank you for signing up with CipherDocs!

To complete your registration, please verify your email address by entering 
the following verification code:

        ┌─────────────┐
        │  1 2 3 4 5 6  │
        └─────────────┘

This code will expire in 10 minutes.

⚠️ Security Notice: Never share this code with anyone. CipherDocs will 
never ask for your verification code via email or phone.

If you didn't create an account with CipherDocs, please ignore this email.

Best regards,
The CipherDocs Team
```

---

## 🎯 What's Protected Now?

### ✅ Secure Endpoints:
- `POST /api/v1/auth/login` - Requires email verification
- All document endpoints - Require valid JWT (user must be verified)
- Search endpoints - Require valid JWT (user must be verified)

### ⚠️ Public Endpoints:
- `POST /api/v1/auth/signup` - Anyone can signup (but can't login until verified)
- `POST /api/v1/auth/verify-email` - Verify OTP code
- `POST /api/v1/auth/resend-otp` - Resend verification code

---

## 🔐 Security Checklist

- [x] OTP uses cryptographically secure random (via `secrets` module)
- [x] OTP expires after 10 minutes
- [x] OTP is single-use (cleared after verification)
- [x] Unverified users cannot login
- [x] Rate limiting on all endpoints (5 attempts / 5 minutes)
- [x] Email sent over TLS (STARTTLS)
- [x] HTML email template includes security warning
- [x] Database migration preserves existing users

---

## 📊 System Status

Check if everything is working:

```powershell
# Check backend status
curl http://localhost:8000/health

# Check database connection
cd c:\Users\AADHITHAN\Downloads\Cipherdocs\backend
python -c "from app.db.database import get_db; next(get_db()); print('✅ Database connected')"

# Check email service
python -c "from app.utils.email_service import send_verification_email; import asyncio; result = asyncio.run(send_verification_email('your_email@gmail.com', '123456', 'Test')); print('✅ Email sent!' if result else '❌ Email failed')"
```

---

## 🎉 You're Done!

Your authentication system is now secure with email verification!

**Next steps:**
1. Update frontend to show verification page
2. Add countdown timer on frontend
3. Style verification email template
4. Consider adding SMS backup (Twilio)

**Questions?** Check [`EMAIL_VERIFICATION_GUIDE.md`](EMAIL_VERIFICATION_GUIDE.md) for detailed documentation.
