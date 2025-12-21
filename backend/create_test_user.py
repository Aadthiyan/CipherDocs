"""
Create a new test user with a fresh password hash
This bypasses the old password hash issue
"""
import sys
sys.path.insert(0, '.')

from app.db.database import get_db
from app.models.database import User, Tenant
from app.core.security import hash_password
import uuid

def create_new_user():
    """Create a fresh test user"""
    db = next(get_db())
    
    try:
        # Get the first tenant
        tenant = db.query(Tenant).first()
        
        if not tenant:
            print("❌ No tenant found! Please create a tenant first.")
            return
        
        print(f"Found tenant: {tenant.name}")
        
        # Check if test user already exists
        existing_user = db.query(User).filter(User.email == "test@cyborgdb.com").first()
        if existing_user:
            print(f"User test@cyborgdb.com already exists, deleting...")
            db.delete(existing_user)
            db.commit()
        
        # Create new user with fresh password
        new_password = "Test123!"
        password_hash = hash_password(new_password)
        
        new_user = User(
            id=uuid.uuid4(),
            email="test@cyborgdb.com",
            tenant_id=tenant.id,
            password_hash=password_hash,
            role="admin",
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        
        print(f"\n✅ New user created successfully!")
        print(f"\n📧 Login Credentials:")
        print(f"  Email: test@cyborgdb.com")
        print(f"  Password: {new_password}")
        print(f"\n🎯 Try logging in at: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_new_user()
