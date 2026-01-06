"""
Script to delete all users and tenants from the database
USE WITH CAUTION - This will delete ALL data!
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

print("⚠️  WARNING: This will delete ALL users and tenants from the database!")
print("Database:", DATABASE_URL.split("@")[1].split("/")[0])
confirm = input("Type 'DELETE ALL' to confirm: ")

if confirm != "DELETE ALL":
    print("❌ Deletion cancelled")
    exit(0)

try:
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Delete all users first (due to foreign key constraints)
            result = conn.execute(text("DELETE FROM users"))
            users_deleted = result.rowcount
            
            # Delete all tenants
            result = conn.execute(text("DELETE FROM tenants"))
            tenants_deleted = result.rowcount
            
            # Commit transaction
            trans.commit()
            
            print(f"✅ Successfully deleted:")
            print(f"   - {users_deleted} users")
            print(f"   - {tenants_deleted} tenants")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error during deletion: {e}")
            raise
            
except Exception as e:
    print(f"❌ Database connection error: {e}")
    exit(1)
