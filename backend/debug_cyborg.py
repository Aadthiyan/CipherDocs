
import os
import sys
import logging

# Add backend to path
sys.path.append(os.getcwd())

# Mock settings environment if needed
os.environ["CYBORGDB_API_KEY"] = "test-key"

from app.core.config import settings
from app.core.cyborg import CyborgDBManager, get_cyborg_client

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_cyborg_setup():
    print("🤖 Testing CyborgDB SDK Setup")
    
    print(f"API Key present: {bool(settings.CYBORGDB_API_KEY)}")
    
    try:
        # 1. Initialize
        client = get_cyborg_client()
        print(f"✅ Client initialized: {client}")
        print(f"   API Key: {client.api_key}")
        
        # 2. Check Health
        is_healthy = CyborgDBManager.check_health()
        print(f"✅ Health Check: {is_healthy}")
        
        if is_healthy:
            print("SUCCESS: CyborgDB Manager is working")
        else:
            print("FAILURE: Health check failed")
            
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_cyborg_setup()
