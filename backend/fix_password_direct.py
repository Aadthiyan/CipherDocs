"""
Fix bcrypt password issue by directly updating the database
Uses bcrypt directly to avoid passlib initialization issues
"""
import sys
sys.path.insert(0, '.')

import bcrypt
from app.db.database import get_db
from app.models.database import User

def fix_password():
    """Reset the test user password using direct bcrypt"""
    db = next(get_db())
    
    try:
        # Get the first user (test user)
        user = db.query(User).first()
        
        if user:
            print(f"Found user: {user.email}")
            
            # Set a simple, valid password using bcrypt directly
            new_password = "TestPass123!"
            # Truncate to 72 bytes as required by bcrypt
            password_bytes = new_password[:72].encode('utf-8')
            
            # Generate hash directly with bcrypt
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt)
            
            # Store as string (passlib format)
            user.password_hash = password_hash.decode('utf-8')
            
            db.commit()
            
            print(f"✅ Password reset successfully!")
            print(f"New credentials:")
            print(f"  Email: {user.email}")
            print(f"  Password: {new_password}")
            print(f"\nYou can now login with these credentials!")
        else:
            print("No users found in database")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_password()
