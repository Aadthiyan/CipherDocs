# Email Verification Implementation Guide

## Overview

Your CipherDocs authentication system now includes **email verification with OTP (One-Time Password)** codes. Users must verify their email address before they can log in, significantly improving security.

---

## 🔐 Security Improvements

### Before (Insecure):
- ❌ Anyone could sign up with fake emails
- ❌ No email validation
- ❌ Immediate access after signup

### After (Secure):
- ✅ Real email required for signup
- ✅ 6-digit OTP code sent to email
- ✅ 10-minute code expiration
- ✅ Cannot login without verification
- ✅ Secure code generation using `secrets` module

---

## 📋 What Changed

### 1. **Database Schema (User Model)**
New fields added to `users` table:
```python
is_verified: Boolean (default: False)
verification_code: String(6) (nullable)
code_expires_at: DateTime (nullable)
```

### 2. **Email Configuration (.env)**
New environment variables:
```env
# Email Configuration (for OTP verification)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_FROM=your_email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=CipherDocs
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
OTP_EXPIRATION_MINUTES=10
```

### 3. **New Files Created**
- [`backend/app/utils/email_service.py`](backend/app/utils/email_service.py) - Email sending with FastAPI-Mail
- [`backend/app/utils/otp.py`](backend/app/utils/otp.py) - OTP generation and validation

### 4. **New API Endpoints**

#### **POST /api/v1/auth/verify-email**
Verify user email with OTP code.

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "admin",
    "is_verified": true
  },
  "tenant": {
    "id": "uuid",
    "name": "Company Name"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid/expired code
- `404 Not Found` - User not found

---

#### **POST /api/v1/auth/resend-otp**
Resend OTP verification code.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Verification code sent successfully",
  "email": "user@example.com",
  "expires_in_minutes": 10
}
```

**Error Responses:**
- `400 Bad Request` - Email already verified
- `404 Not Found` - User not found
- `500 Internal Server Error` - Failed to send email

---

### 5. **Modified API Endpoints**

#### **POST /api/v1/auth/signup** (Modified)
Now sends verification email after signup.

**Behavior Changes:**
- User account created with `is_verified = false`
- 6-digit OTP generated and stored
- Verification email sent automatically
- Returns JWT tokens (but login will fail until verified)

**Response:** Same as before, but user cannot login yet

---

#### **POST /api/v1/auth/login** (Modified)
Now checks email verification status.

**New Error:**
```json
{
  "detail": "Email not verified. Please check your email for the verification code."
}
```
**Status Code:** `403 Forbidden`

---

## 🚀 How to Use

### 1. **Setup Email Configuration**

#### **For Gmail:**
1. Go to Google Account: https://myaccount.google.com/apppasswords
2. Create new App Password (NOT your regular password)
3. Update `.env`:
```env
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_16_char_app_password
MAIL_FROM=your_email@gmail.com
```

#### **For Other Email Providers:**
Update SMTP settings in `.env`:
```env
MAIL_SERVER=smtp.yourprovider.com
MAIL_PORT=587
MAIL_USERNAME=your_email@provider.com
MAIL_PASSWORD=your_password
```

### 2. **Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

### 3. **Apply Database Migration**
```bash
cd backend
alembic upgrade head
```

**Note:** Existing users are automatically marked as `is_verified = true` to prevent breaking existing accounts.

### 4. **Test the Flow**

#### **Step 1: Signup**
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "StrongP@ss123",
    "company_name": "Test Company"
  }'
```

**Check your email** for 6-digit OTP code.

---

#### **Step 2: Verify Email**
```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "123456"
  }'
```

**Response:** JWT tokens + user info

---

#### **Step 3: Login**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "StrongP@ss123"
  }'
```

**Success!** Now you can login.

---

#### **Step 4: Resend OTP (Optional)**
If code expired:
```bash
curl -X POST http://localhost:8000/api/v1/auth/resend-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com"
  }'
```

---

## 📧 Email Template

Users receive a beautiful HTML email with:
- 🔐 Header with "Email Verification"
- 📋 6-digit OTP code in large font
- ⏰ Expiration time (10 minutes)
- ⚠️ Security warning
- 📱 Mobile-responsive design

**Example:**
```
Hello User,

Thank you for signing up with CipherDocs!

To complete your registration, please verify your email address by entering the following verification code:

┌──────────────┐
│   1 2 3 4 5 6   │
└──────────────┘

This code will expire in 10 minutes.

⚠️ Security Notice: Never share this code with anyone.
```

---

## 🛡️ Security Features

### 1. **Cryptographically Secure OTP**
```python
import secrets
otp = ''.join(secrets.choice(string.digits) for _ in range(6))
```
- Uses `secrets` module (CSPRNG)
- Not `random` (predictable)

### 2. **Time-Based Expiration**
- OTP expires in 10 minutes (configurable)
- Prevents replay attacks

### 3. **One-Time Use**
- Code cleared after successful verification
- Cannot reuse same code

### 4. **Rate Limiting**
- Existing rate limiting applies to all endpoints
- 5 attempts per 5 minutes

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAIL_USERNAME` | - | SMTP username (email) |
| `MAIL_PASSWORD` | - | SMTP password or App Password |
| `MAIL_FROM` | - | From email address |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_STARTTLS` | `true` | Enable STARTTLS |
| `MAIL_SSL_TLS` | `false` | Enable SSL/TLS |
| `OTP_EXPIRATION_MINUTES` | `10` | OTP validity period |

---

## 🐛 Troubleshooting

### Issue: "Failed to send verification email"

**Causes:**
1. Invalid Gmail App Password
2. SMTP settings incorrect
3. Gmail security blocking

**Solutions:**
1. **Generate new App Password:**
   - Visit: https://myaccount.google.com/apppasswords
   - Create new password (NOT your regular password)
   - Copy all 16 characters

2. **Check Gmail Settings:**
   - 2FA must be enabled
   - "Less secure apps" NOT required with App Password

3. **Test SMTP Connection:**
```python
import smtplib
smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.starttls()
smtp.login('your_email@gmail.com', 'your_app_password')
smtp.quit()
```

---

### Issue: "Email not verified" when logging in

**Causes:**
- User never verified email
- OTP code expired

**Solutions:**
1. Resend OTP: `POST /api/v1/auth/resend-otp`
2. Check email spam folder
3. For testing, manually verify in database:
```sql
UPDATE users SET is_verified = true WHERE email = 'test@example.com';
```

---

### Issue: Migration fails

**Error:**
```
column "is_verified" of relation "users" contains null values
```

**Solution:**
Migration file already handles this by:
1. Adding column as nullable
2. Setting existing users to `is_verified = true`
3. Making column NOT NULL

If still fails, rollback and retry:
```bash
alembic downgrade -1
alembic upgrade head
```

---

## 📊 Database Changes

### Migration File
Located at: `backend/alembic/versions/ed4af5548d60_add_email_verification_fields_to_user_.py`

### Schema Changes
```sql
-- Add new columns
ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN verification_code VARCHAR(6);
ALTER TABLE users ADD COLUMN code_expires_at TIMESTAMP WITH TIME ZONE;

-- Set existing users as verified (migration only)
UPDATE users SET is_verified = true WHERE is_verified IS NULL;
```

---

## 🎯 Next Steps (Future Enhancements)

### 1. **Password Reset with OTP**
Already scaffolded in [`email_service.py`](backend/app/utils/email_service.py):
```python
await send_password_reset_email(email, reset_token)
```

### 2. **SMS Verification**
Add Twilio for SMS OTP:
```python
from twilio.rest import Client
client = Client(account_sid, auth_token)
message = client.messages.create(to=phone, from_=twilio_phone, body=f"Your code: {otp}")
```

### 3. **Two-Factor Authentication (2FA)**
- TOTP (Google Authenticator)
- Backup codes
- SMS fallback

### 4. **Email Change Verification**
Require OTP when user changes email

### 5. **Admin Panel**
- View unverified users
- Manually verify users
- Resend verification emails in bulk

---

## 📝 Frontend Integration Example

### React/Next.js Flow

#### 1. Signup Component
```typescript
const handleSignup = async (email: string, password: string, company: string) => {
  const response = await fetch('/api/v1/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, company_name: company })
  });
  
  if (response.ok) {
    // Redirect to verification page
    router.push(`/verify-email?email=${encodeURIComponent(email)}`);
  }
};
```

#### 2. Verification Component
```typescript
const handleVerify = async (email: string, code: string) => {
  const response = await fetch('/api/v1/auth/verify-email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code })
  });
  
  if (response.ok) {
    const { access_token, user } = await response.json();
    localStorage.setItem('token', access_token);
    router.push('/dashboard');
  }
};
```

#### 3. Resend OTP
```typescript
const handleResendOTP = async (email: string) => {
  const response = await fetch('/api/v1/auth/resend-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  
  if (response.ok) {
    toast.success('Verification code sent!');
  }
};
```

---

## 🎨 UI/UX Recommendations

### Verification Page Design
```
┌─────────────────────────────────┐
│  Verify Your Email              │
│                                 │
│  We sent a 6-digit code to:    │
│  user@example.com               │
│                                 │
│  [_] [_] [_] [_] [_] [_]      │
│                                 │
│  Code expires in: 9:45          │
│                                 │
│  [Verify Email]                 │
│                                 │
│  Didn't receive code?           │
│  [Resend Code]                  │
└─────────────────────────────────┘
```

### Features:
- Auto-focus first input
- Auto-submit when all 6 digits entered
- Copy-paste support (split into 6 boxes)
- Countdown timer
- Resend button (disabled during countdown)

---

## ✅ Summary

Your authentication system now has:
- ✅ Email verification with OTP
- ✅ Secure code generation
- ✅ Time-based expiration
- ✅ Beautiful HTML emails
- ✅ Resend functionality
- ✅ Database migrations
- ✅ Login protection

**All existing users are marked as verified** - no breaking changes!

---

## 📞 Support

For questions or issues:
1. Check logs: `backend/logs/`
2. Test email sending separately
3. Verify environment variables
4. Check database migrations

**Questions about this implementation?** Check the code in:
- [`backend/app/api/auth.py`](backend/app/api/auth.py) - Auth endpoints
- [`backend/app/utils/email_service.py`](backend/app/utils/email_service.py) - Email service
- [`backend/app/utils/otp.py`](backend/app/utils/otp.py) - OTP utilities
