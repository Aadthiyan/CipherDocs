
import os
import sys
import uuid
import logging

# Add backend to path
sys.path.append(os.getcwd())

# Force api key for mock
os.environ["CYBORGDB_API_KEY"] = "test-key"

from app.core.config import settings
from app.core.cyborg import CyborgDBManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_index_mgmt():
    print("🧠 Testing CyborgDB Index Management")
    
    tenant_id = str(uuid.uuid4())
    print(f"Tenant ID: {tenant_id}")
    
    try:
        # 1. Create Index
        name = CyborgDBManager.create_tenant_index(tenant_id)
        print(f"✅ Created index: {name}")
        
        # 2. Idempotency Check (Create again)
        name2 = CyborgDBManager.create_tenant_index(tenant_id)
        print(f"✅ Created index again (Idempotent): {name2}")
        assert name == name2
        
        # 3. Delete Index
        CyborgDBManager.delete_tenant_index(tenant_id)
        print(f"✅ Deleted index: {name}")
        
        # 4. Delete non-existent (should handle gracefully)
        CyborgDBManager.delete_tenant_index(tenant_id)
        print(f"✅ Delete non-existent: OK")
        
        print("SUCCESS: Index lifecycle verified")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_index_mgmt()
