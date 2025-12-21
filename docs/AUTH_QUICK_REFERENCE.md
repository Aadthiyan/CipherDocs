# Authentication System Quick Reference

## Overview
The CyborgDB authentication system provides secure JWT-based authentication with tenant isolation, password hashing, and rate limiting.

## Endpoints

### 1. Signup (Register New Tenant)
**Endpoint:** `POST /api/v1/auth/signup`

**Request Body:**
```json
{
  "email": "admin@company.com",
  "password": "SecurePass123",
  "company_name": "My Company"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit

**Success Response (201):**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "admin@company.com",
    "role": "admin",
    "tenant_id": "uuid",
    "is_active": true,
    "created_at": "2025-12-15T08:00:00Z"
  },
  "tenant": {
    "id": "uuid",
    "name": "My Company",
    "plan": "starter",
    "is_active": true,
    "created_at": "2025-12-15T08:00:00Z"
  }
}
```

**Error Responses:**
- `409 Conflict` - Email already registered
- `422 Unprocessable Entity` - Invalid email or weak password

---

### 2. Login (Authenticate Existing User)
**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "admin@company.com",
  "password": "SecurePass123"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "user": { ... },
  "tenant": { ... }
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid email or password
- `403 Forbidden` - Account or tenant is deactivated
- `429 Too Many Requests` - Rate limit exceeded (5 attempts per 5 minutes)

---

## Using JWT Tokens

### Access Token
- **Expiration:** 24 hours
- **Usage:** Include in `Authorization` header for all protected endpoints
- **Format:** `Authorization: Bearer {access_token}`

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Refresh Token
- **Expiration:** 30 days
- **Usage:** Use to obtain new access token when it expires
- **Endpoint:** `POST /api/v1/auth/refresh` (to be implemented in Task 2.3)

### Token Payload Structure
```json
{
  "sub": "user_id",
  "tenant_id": "tenant_id",
  "role": "admin|user|viewer",
  "exp": 1234567890,
  "iat": 1234567890,
  "type": "access|refresh"
}
```

---

## Rate Limiting

**Configuration:**
- **Max Attempts:** 5 failed login attempts
- **Time Window:** 5 minutes (300 seconds)
- **Tracking:** Per email + IP address combination

**Behavior:**
- Failed login attempts are tracked
- After 5 failed attempts, returns `429 Too Many Requests`
- Counter resets on successful login
- Old attempts automatically expire after 5 minutes

**Production Note:** Current implementation uses in-memory storage. For production with multiple server instances, migrate to Redis.

---

## Security Features

### Password Security
- **Hashing:** Bcrypt with automatic salt generation
- **Verification:** Constant-time comparison (prevents timing attacks)
- **Storage:** Only hashed passwords stored, never plaintext
- **Validation:** Enforced complexity requirements

### JWT Security
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Secret:** Loaded from `JWT_SECRET` environment variable (min 32 chars)
- **Expiration:** Enforced on every token validation
- **Tenant Isolation:** Tenant ID embedded in every token
- **Role Claims:** User role included for RBAC

### Email Validation
- **Standard:** RFC 5322 compliant
- **Library:** `email-validator` package
- **Validation:** Performed by Pydantic on request

---

## Environment Variables

Required configuration in `.env`:

```bash
# JWT Configuration
JWT_SECRET=your-secret-key-min-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
REFRESH_TOKEN_EXPIRATION_DAYS=30

# Rate Limiting
RATE_LIMIT_ENABLED=true
MAX_LOGIN_ATTEMPTS=5
RATE_LIMIT_WINDOW_SECONDS=300
```

---

## Code Examples

### Python (using requests)
```python
import requests

# Signup
signup_response = requests.post(
    "http://localhost:8000/api/v1/auth/signup",
    json={
        "email": "admin@company.com",
        "password": "SecurePass123",
        "company_name": "My Company"
    }
)
tokens = signup_response.json()
access_token = tokens["access_token"]

# Use token for authenticated request
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(
    "http://localhost:8000/api/v1/documents",
    headers=headers
)
```

### JavaScript (using fetch)
```javascript
// Signup
const signupResponse = await fetch('http://localhost:8000/api/v1/auth/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'admin@company.com',
    password: 'SecurePass123',
    company_name: 'My Company'
  })
});
const tokens = await signupResponse.json();
const accessToken = tokens.access_token;

// Use token for authenticated request
const response = await fetch('http://localhost:8000/api/v1/documents', {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
```

### cURL
```bash
# Signup
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "SecurePass123",
    "company_name": "My Company"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "SecurePass123"
  }'

# Use token
curl -X GET "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

---

## Testing

### Run Tests
```bash
# Set environment variables
$env:JWT_SECRET="test_secret_key_must_be_very_long_to_pass_validation_32chars"
$env:MASTER_ENCRYPTION_KEY="test_master_key_must_be_very_long_to_pass_validation_32chars"
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test_db"

# Run auth tests
pytest tests/test_auth_endpoints.py -v

# Run all tests
pytest -v
```

### Test Coverage
- ✅ Successful signup and login
- ✅ Email validation
- ✅ Password strength validation
- ✅ Duplicate email handling
- ✅ Invalid credentials
- ✅ Rate limiting
- ✅ Password hashing
- ✅ JWT token generation and validation

---

## Common Issues & Solutions

### Issue: "Email already registered"
**Cause:** Email exists in database  
**Solution:** Use login endpoint or different email

### Issue: "Password must contain at least one uppercase letter"
**Cause:** Password doesn't meet complexity requirements  
**Solution:** Ensure password has uppercase, lowercase, and digit

### Issue: "Too many login attempts"
**Cause:** Rate limit exceeded  
**Solution:** Wait 5 minutes or use correct password

### Issue: "Could not validate credentials"
**Cause:** Invalid or expired JWT token  
**Solution:** Login again to get new token

### Issue: "Tenant account is suspended"
**Cause:** Tenant is_active = false  
**Solution:** Contact support to reactivate account

---

## Next Steps

After authentication is set up:
1. Use `get_current_user_claims` dependency in protected endpoints
2. Extract `tenant_id` for tenant isolation
3. Check `role` for role-based access control
4. Implement token refresh endpoint (Task 2.3)
5. Add tenant isolation middleware (Task 2.3)

---

## API Documentation

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Both provide:
- Interactive API testing
- Request/response schemas
- Example payloads
- Authentication flows
