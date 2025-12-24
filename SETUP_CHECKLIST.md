# ✅ Email Verification - Setup Checklist

## 📋 Pre-Deployment Checklist

Use this checklist to ensure everything is configured correctly before deploying.

---

## 🔧 1. Environment Configuration

### Gmail Setup (Required)
- [ ] Enabled 2-Factor Authentication on Google Account
- [ ] Generated App Password at https://myaccount.google.com/apppasswords
- [ ] Updated `backend/.env` with Gmail credentials:
  ```env
  MAIL_USERNAME=your_email@gmail.com
  MAIL_PASSWORD=your_16_char_app_password
  MAIL_FROM=your_email@gmail.com
  MAIL_SERVER=smtp.gmail.com
  MAIL_PORT=587
  MAIL_STARTTLS=true
  MAIL_SSL_TLS=false
  OTP_EXPIRATION_MINUTES=10
  ```

### Database Configuration
- [ ] `DATABASE_URL` is set in `.env`
- [ ] `JWT_SECRET` is set (32+ characters)
- [ ] `MASTER_ENCRYPTION_KEY` is set

---

## 📦 2. Dependencies

### Backend Packages
- [ ] Installed fastapi-mail: `pip install -r requirements.txt`
- [ ] Verified installation: `python -c "import fastapi_mail; print('✅ Installed')"`

---

## 🗄️ 3. Database Migration

### Apply Migration
- [ ] Generated migration: `alembic revision --autogenerate -m "Add email verification"`
- [ ] Applied migration: `alembic upgrade head`
- [ ] Verified new columns exist:
  ```sql
  SELECT column_name 
  FROM information_schema.columns 
  WHERE table_name = 'users' 
    AND column_name IN ('is_verified', 'verification_code', 'code_expires_at');
  ```

### Expected Columns in `users` Table:
- [ ] `is_verified` (Boolean, default: false)
- [ ] `verification_code` (String(6), nullable)
- [ ] `code_expires_at` (DateTime, nullable)

---

## 🧪 4. Testing

### Test Email Sending
- [ ] Create test file `test_email.py`:
  ```python
  import asyncio
  import sys
  sys.path.insert(0, 'c:/Users/AADHITHAN/Downloads/Cipherdocs/backend')
  
  from app.utils.email_service import send_verification_email
  
  async def test():
      result = await send_verification_email(
          email="your_email@gmail.com",
          otp_code="123456",
          user_name="Test User"
      )
      print("✅ Email sent!" if result else "❌ Email failed")
  
  asyncio.run(test())
  ```
- [ ] Run: `python test_email.py`
- [ ] Check inbox for verification email

### Test OTP Generation
- [ ] Test OTP utility:
  ```python
  import sys
  sys.path.insert(0, 'c:/Users/AADHITHAN/Downloads/Cipherdocs/backend')
  
  from app.utils.otp import generate_otp_code, get_otp_expiry_time
  
  otp = generate_otp_code()
  expiry = get_otp_expiry_time()
  
  print(f"✅ OTP: {otp}")
  print(f"✅ Expires: {expiry}")
  ```

### Test Complete Flow
- [ ] **Step 1:** Signup with real email
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/signup \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "TestPass123!",
      "company_name": "Test Company"
    }'
  ```
- [ ] **Step 2:** Check email for OTP code
- [ ] **Step 3:** Try login (should fail with 403)
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "TestPass123!"
    }'
  ```
- [ ] **Step 4:** Verify email
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/verify-email \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "code": "123456"
    }'
  ```
- [ ] **Step 5:** Login again (should succeed)

---

## 📝 5. API Endpoints

### Verify All Endpoints Work
- [ ] `POST /api/v1/auth/signup` - Creates user + sends OTP
- [ ] `POST /api/v1/auth/verify-email` - Verifies OTP code
- [ ] `POST /api/v1/auth/resend-otp` - Resends OTP
- [ ] `POST /api/v1/auth/login` - Checks email verification
- [ ] `GET /api/v1/auth/me` - Returns current user

---

## 🎨 6. Email Template

### Verify Email Rendering
- [ ] Email has proper formatting (HTML)
- [ ] OTP code is clearly visible
- [ ] Expiration time shown (10 minutes)
- [ ] Security warning included
- [ ] Company name displayed correctly
- [ ] Email works on mobile devices
- [ ] Plain text fallback works

---

## 🔒 7. Security

### Security Checklist
- [ ] OTP uses `secrets` module (not `random`)
- [ ] OTP expires after 10 minutes
- [ ] OTP cleared after successful verification
- [ ] Rate limiting active (5 attempts / 5 min)
- [ ] Passwords hashed with bcrypt
- [ ] JWT tokens have expiration
- [ ] HTTPS enabled in production
- [ ] CORS origins configured correctly

---

## 📊 8. Database

### Verify Data Integrity
- [ ] Existing users marked as `is_verified = True`
- [ ] New users created with `is_verified = False`
- [ ] Tenant IDs generated correctly (UUID v4)
- [ ] User-Tenant relationships intact
- [ ] No orphaned records

### Run Verification Query:
```sql
-- Check user verification status
SELECT 
    email,
    is_verified,
    verification_code,
    code_expires_at,
    created_at,
    tenant_id
FROM users
ORDER BY created_at DESC
LIMIT 10;
```

---

## 🚀 9. Deployment

### Pre-Deployment
- [ ] All environment variables set in production `.env`
- [ ] Database migration applied on production database
- [ ] Email credentials verified (not using test credentials)
- [ ] CORS origins updated for production domain
- [ ] Rate limiting enabled
- [ ] Debug mode disabled (`DEBUG=false`)

### Production Environment Variables
```env
# Production settings
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# CORS for production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email (use production credentials)
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=production_app_password
MAIL_FROM=noreply@yourdomain.com

# Database (production URL)
DATABASE_URL=postgresql://user:pass@production-host/dbname
```

---

## 📱 10. Frontend Integration

### Frontend Checklist
- [ ] Signup form redirects to verification page
- [ ] Verification page created with OTP input
- [ ] OTP input supports 6 digits
- [ ] Countdown timer shows time remaining
- [ ] Resend button available after timeout
- [ ] Error messages displayed correctly
- [ ] Success redirects to login/dashboard
- [ ] Mobile-responsive design

### Example Verification Page:
```typescript
// components/VerifyEmail.tsx
import { useState, useEffect } from 'react';

export default function VerifyEmail({ email }) {
  const [code, setCode] = useState('');
  const [timer, setTimer] = useState(600); // 10 minutes

  useEffect(() => {
    const interval = setInterval(() => {
      setTimer(prev => prev > 0 ? prev - 1 : 0);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleVerify = async () => {
    const response = await fetch('/api/v1/auth/verify-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, code })
    });
    
    if (response.ok) {
      // Redirect to dashboard
      router.push('/dashboard');
    }
  };

  return (
    <div>
      <h1>Verify Your Email</h1>
      <p>Enter the 6-digit code sent to {email}</p>
      <input 
        value={code} 
        onChange={e => setCode(e.target.value)} 
        maxLength={6}
      />
      <p>Expires in: {Math.floor(timer / 60)}:{timer % 60}</p>
      <button onClick={handleVerify}>Verify</button>
    </div>
  );
}
```

---

## 🐛 11. Troubleshooting

### Common Issues Checklist

#### Email Not Sending
- [ ] Check Gmail App Password (not regular password)
- [ ] Verify 2FA enabled on Google Account
- [ ] Check `.env` file loaded correctly
- [ ] Test SMTP connection manually
- [ ] Check firewall/antivirus blocking port 587
- [ ] Verify internet connection

#### Migration Failed
- [ ] Check database connection
- [ ] Verify Alembic configuration
- [ ] Check for duplicate migration files
- [ ] Try rollback and reapply: `alembic downgrade -1 && alembic upgrade head`

#### Login Still Fails After Verification
- [ ] Check database: `SELECT is_verified FROM users WHERE email = '...'`
- [ ] Verify OTP was cleared after verification
- [ ] Check JWT token contains correct user info
- [ ] Verify tenant is active

---

## 📚 12. Documentation

### Documentation Checklist
- [ ] Read [`EMAIL_VERIFICATION_GUIDE.md`](EMAIL_VERIFICATION_GUIDE.md)
- [ ] Read [`QUICK_START_EMAIL_VERIFICATION.md`](QUICK_START_EMAIL_VERIFICATION.md)
- [ ] Read [`TENANT_ID_EXPLAINED.md`](TENANT_ID_EXPLAINED.md)
- [ ] Read [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md)
- [ ] Understand comparison: [`EMAIL_OTP_VS_CLERK.md`](EMAIL_OTP_VS_CLERK.md)

---

## ✅ Final Verification

### System Health Check
```bash
# 1. Backend running
curl http://localhost:8000/health

# 2. Database connected
python -c "from app.db.database import get_db; next(get_db()); print('✅ DB OK')"

# 3. Email service ready
python test_email.py

# 4. All tests passing
pytest backend/tests/

# 5. API documentation accessible
curl http://localhost:8000/docs
```

---

## 🎉 Ready for Production?

### Pre-Launch Checklist
- [ ] All above checkboxes completed
- [ ] Tested on staging environment
- [ ] Load testing completed (optional)
- [ ] Backup strategy in place
- [ ] Monitoring/logging configured
- [ ] Error tracking setup (Sentry, etc.)
- [ ] Rate limiting verified
- [ ] Security audit passed

---

## 📞 Support Resources

### If You Need Help:
1. Check logs: `backend/logs/app.log`
2. Review documentation files
3. Test individual components
4. Check environment variables
5. Verify database schema

### Useful Commands:
```bash
# Check environment
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('MAIL_USERNAME:', os.getenv('MAIL_USERNAME'))"

# Test database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"

# Check migration status
alembic current

# View logs
tail -f backend/logs/app.log
```

---

## 🎯 Success Criteria

Your system is ready when:
- ✅ New users can signup
- ✅ Verification emails sent successfully
- ✅ OTP codes verified correctly
- ✅ Unverified users cannot login
- ✅ Verified users can login
- ✅ Existing users unaffected
- ✅ All API endpoints working
- ✅ Frontend integrated (if applicable)

---

**Congratulations!** 🎉

Your email verification system is production-ready!

**Quick reference:** [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md)
