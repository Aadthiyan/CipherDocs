"""
Create CyborgDB index for existing tenant
"""
import sys
from app.db.database import get_db
from app.models.database import Tenant, User, EncryptionKey
from app.core.cyborg import CyborgDBManager
from app.core.encryption import KeyManager

def create_index_for_tenant(user_email: str):
    """Create CyborgDB index for a tenant via user email"""
    db = next(get_db())
    
    try:
        # Find user
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"❌ User not found: {user_email}")
            return
        
        tenant = user.tenant
        print(f"✅ Found user: {user.email}")
        print(f"✅ Found tenant: {tenant.name} (ID: {tenant.id})")
        
        # Get encryption key
        try:
            raw_key = KeyManager.get_tenant_key(db, tenant.id)
            print(f"✅ Retrieved encryption key")
            print(f"   Key type: {type(raw_key)}, length: {len(raw_key)}")
            
            # Decode to verify it's 32 bytes
            import base64
            key_bytes = base64.urlsafe_b64decode(raw_key)
            print(f"   Decoded key length: {len(key_bytes)} bytes")
            
        except ValueError:
            print(f"⚠️ No encryption key found, creating one...")
            _, raw_key = KeyManager.create_tenant_key(db, tenant.id)
            print(f"✅ Created encryption key")
        
        # Create CyborgDB index
        try:
            index_name = CyborgDBManager.create_tenant_index(
                str(tenant.id),
                dimension=384,
                key=raw_key
            )
            print(f"✅ Created CyborgDB index: {index_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"⚠️ Index already exists for tenant")
            else:
                raise e
        
        print(f"\n🎉 Index setup complete for {user.email}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_email = sys.argv[1]
    else:
        user_email = input("Enter user email: ")
    
    create_index_for_tenant(user_email)
