# Tenant ID Creation & Management

## 📘 Understanding Tenant Architecture

Your CipherDocs system uses **multi-tenancy** - each company/organization is a separate tenant with isolated data.

---

## 🆔 What is a Tenant ID?

**Tenant ID** = Unique identifier (UUID) for each company/organization

Example: `660e8400-e29b-41d4-a716-446655440001`

---

## ⏰ When is Tenant ID Created?

### **During User Signup** ([`backend/app/api/auth.py#L103-L109`](backend/app/api/auth.py))

```python
# Step 1: User signs up
POST /api/v1/auth/signup
{
  "email": "admin@company.com",
  "password": "SecurePass123!",
  "company_name": "My Company"
}

# Step 2: System creates Tenant first
tenant = Tenant(
    id=uuid.uuid4(),              # ← Tenant ID created here!
    name="My Company",             # From company_name in request
    plan="starter",                # Default plan
    is_active=True
)
db.add(tenant)
db.flush()  # Save to get tenant.id

# Step 3: System creates Admin User linked to Tenant
user = User(
    id=uuid.uuid4(),               # User ID (separate from tenant)
    email="admin@company.com",
    tenant_id=tenant.id,           # ← Links user to tenant
    role="admin",                  # First user is always admin
    is_active=True,
    is_verified=False              # ← New: Requires email verification
)
db.add(user)
db.commit()
```

---

## 🔄 Full Signup Flow with Tenant Creation

### **Timeline:**

```
1. User submits signup form
   ↓
2. Backend checks if email exists (409 if duplicate)
   ↓
3. Backend hashes password
   ↓
4. Backend creates Tenant object
   ├─ Generates UUID for tenant.id
   ├─ Sets name = company_name
   └─ Sets plan = "starter"
   ↓
5. Backend saves Tenant to database
   ↓
6. Backend creates User object
   ├─ Generates UUID for user.id
   ├─ Links to tenant via tenant_id
   ├─ Sets role = "admin"
   └─ Sets is_verified = False
   ↓
7. Backend generates OTP code
   ↓
8. Backend sends verification email
   ↓
9. User receives OTP in email
   ↓
10. User verifies email with OTP
    ↓
11. Backend sets is_verified = True
    ↓
12. User can now login!
```

---

## 📊 Database Relationships

### **Entity Relationship Diagram:**

```
┌─────────────────┐           ┌──────────────────┐
│     Tenant      │           │      User        │
├─────────────────┤           ├──────────────────┤
│ id (UUID) PK    │◄─────────│ id (UUID) PK     │
│ name            │    1:N   │ tenant_id (FK)   │
│ plan            │           │ email            │
│ is_active       │           │ role             │
│ cyborgdb_ns     │           │ is_verified ✨   │
└─────────────────┘           └──────────────────┘
         │                             │
         │                             │
         │ 1:N                         │ 1:N
         │                             │
         ▼                             ▼
┌─────────────────┐           ┌──────────────────┐
│   Document      │           │   SearchLog      │
├─────────────────┤           ├──────────────────┤
│ id (UUID)       │           │ id (UUID)        │
│ tenant_id (FK)  │           │ tenant_id (FK)   │
│ filename        │           │ user_id (FK)     │
│ storage_path    │           │ query            │
└─────────────────┘           └──────────────────┘
```

**Key Points:**
- 1 Tenant → Many Users
- 1 Tenant → Many Documents
- 1 User → Many SearchLogs
- All data isolated by `tenant_id`

---

## 🔍 How Tenant ID is Used

### **1. Data Isolation**

Every query filters by tenant_id:

```python
# Get user's documents (automatically filtered by tenant)
documents = db.query(Document).filter(
    Document.tenant_id == current_user.tenant_id
).all()

# Users from Company A cannot see Company B's documents!
```

---

### **2. JWT Token Payload**

Tenant ID is embedded in JWT tokens:

```python
# Token creation (auth.py)
access_token = security.create_access_token(
    subject=str(user.id),
    tenant_id=str(tenant.id),  # ← Tenant ID in token
    role=user.role
)

# Token payload looks like:
{
  "sub": "user-uuid-here",
  "tenant_id": "tenant-uuid-here",
  "role": "admin",
  "exp": 1735084800
}
```

---

### **3. CyborgDB Index**

Each tenant gets isolated vector index:

```python
# During tenant creation
index_name = CyborgDBManager.create_tenant_index(
    str(tenant.id),
    key=encryption_key
)

# Index name: "tenant_660e8400-e29b-41d4-a716-446655440001"
# Documents from Tenant A stored in their own encrypted index
# Tenant B cannot access Tenant A's index
```

---

## 🧪 Testing Tenant Isolation

### **Create 2 Tenants:**

```powershell
# Tenant 1: Company A
$company1 = @{
    email = "admin@companyA.com"
    password = "Pass123!"
    company_name = "Company A"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/signup" `
    -Method POST -ContentType "application/json" -Body $company1

# Tenant 2: Company B
$company2 = @{
    email = "admin@companyB.com"
    password = "Pass123!"
    company_name = "Company B"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/signup" `
    -Method POST -ContentType "application/json" -Body $company2
```

---

### **Check Database:**

```sql
SELECT 
    t.id as tenant_id,
    t.name as company_name,
    u.email,
    u.role,
    u.is_verified
FROM tenants t
JOIN users u ON u.tenant_id = t.id
ORDER BY t.created_at DESC;
```

**Result:**
```
tenant_id                              | company_name | email              | role  | is_verified
---------------------------------------|--------------|-----------------------|-------|-------------
660e8400-e29b-41d4-a716-446655440001  | Company A    | admin@companyA.com   | admin | false
772f9500-f3ac-52e5-b827-557766551112  | Company B    | admin@companyB.com   | admin | false
```

**Each tenant has unique ID!**

---

## 🔐 Tenant Data Isolation Flow

### **Example: Document Upload**

```python
# User from Company A uploads document
POST /api/v1/documents/upload
Headers: Authorization: Bearer <token_with_tenant_A_id>

# Backend extracts tenant_id from JWT
current_user = get_current_user(token)  # Has tenant_id

# Document saved with tenant_id
document = Document(
    id=uuid.uuid4(),
    tenant_id=current_user.tenant_id,  # Company A's tenant_id
    filename="contract.pdf",
    storage_path="storage/tenant_660e8400/contract.pdf"
)

# User from Company B CANNOT access this document!
# Because their JWT has different tenant_id
```

---

## 📝 Tenant Model Schema

### **Full Tenant Model** ([`backend/app/models/database.py`](backend/app/models/database.py))

```python
class Tenant(Base):
    __tablename__ = "tenants"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Info
    name = Column(String(255), nullable=False)  # Company name
    plan = Column(String(50), default="starter")  # starter, pro, enterprise
    
    # Security
    key_fingerprint = Column(String(255), unique=True)  # Encryption key fingerprint
    cyborgdb_namespace = Column(String(255), unique=True)  # Vector DB namespace
    
    # Status
    is_active = Column(Boolean, default=True)  # Can tenant access system?
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant")
    search_logs = relationship("SearchLog", back_populates="tenant")
```

---

## 🎯 Key Takeaways

### **Tenant ID is:**
- ✅ Created during **signup**
- ✅ A **UUID v4** (e.g., `660e8400-e29b-41d4-a716-446655440001`)
- ✅ Generated **before user creation**
- ✅ Used for **data isolation**
- ✅ Embedded in **JWT tokens**
- ✅ Stored in **database as primary key**

### **Multi-Tenant Benefits:**
- 🏢 Each company has isolated data
- 🔒 Company A cannot see Company B's documents
- 📊 Separate analytics per tenant
- 💰 Different pricing plans per tenant
- 🔑 Separate encryption keys per tenant

---

## 🔄 Tenant Lifecycle

### **1. Creation (Signup)**
```python
tenant = Tenant(id=uuid.uuid4(), name="Company", plan="starter")
```

### **2. Active Usage**
```python
# All operations filtered by tenant_id
documents = query(Document).filter(Document.tenant_id == tenant.id)
```

### **3. Suspension (if needed)**
```python
tenant.is_active = False  # Tenant can no longer access system
```

### **4. Deletion (cascade)**
```python
db.delete(tenant)  # Deletes tenant + all users + all documents
```

---

## 🚀 Advanced: Multi-User Tenants

### **Add more users to existing tenant:**

```python
# Admin adds new user to their company
POST /api/v1/users/invite
{
  "email": "newuser@company.com",
  "role": "user"
}

# Backend creates user with same tenant_id
new_user = User(
    id=uuid.uuid4(),
    email="newuser@company.com",
    tenant_id=current_user.tenant_id,  # ← Same tenant!
    role="user",
    is_verified=False
)
```

**Result:** Both users share the same documents, same tenant data!

---

## 📊 Tenant Statistics Query

```sql
-- Count users per tenant
SELECT 
    t.name as company_name,
    t.plan,
    COUNT(u.id) as user_count,
    COUNT(d.id) as document_count,
    t.is_active
FROM tenants t
LEFT JOIN users u ON u.tenant_id = t.id
LEFT JOIN documents d ON d.tenant_id = t.id
GROUP BY t.id, t.name, t.plan, t.is_active
ORDER BY user_count DESC;
```

---

## 🔍 Debug: Find Your Tenant ID

### **After Signup:**
```python
# The signup response includes tenant info
{
  "access_token": "eyJ0eXAi...",
  "user": {
    "id": "user-uuid",
    "email": "admin@company.com",
    "tenant_id": "660e8400-e29b-41d4-a716-446655440001"  # ← Here!
  },
  "tenant": {
    "id": "660e8400-e29b-41d4-a716-446655440001",  # ← And here!
    "name": "My Company",
    "plan": "starter"
  }
}
```

### **From JWT Token:**
```python
import jwt

token = "eyJ0eXAiOiJKV1QiLCJhbGc..."
decoded = jwt.decode(token, verify=False)  # For debugging only!
print(decoded["tenant_id"])  # ← Tenant ID here
```

### **From Database:**
```sql
SELECT tenant_id FROM users WHERE email = 'your_email@company.com';
```

---

## ✨ Summary

**When user signs up:**
1. System generates `tenant_id = uuid.uuid4()` ✨
2. Creates Tenant with that ID
3. Creates User linked to that Tenant
4. Sends verification email
5. User verifies → can login
6. All future operations filtered by `tenant_id`

**Your tenant system is:**
- 🔒 **Secure** - Data isolated per company
- ⚡ **Automatic** - Created during signup
- 🎯 **Simple** - One company = One tenant
- 📈 **Scalable** - Supports millions of tenants

---

**Questions?** Check these files:
- Tenant Model: [`backend/app/models/database.py`](backend/app/models/database.py)
- Signup Logic: [`backend/app/api/auth.py`](backend/app/api/auth.py)
- JWT Tokens: [`backend/app/core/security.py`](backend/app/core/security.py)
