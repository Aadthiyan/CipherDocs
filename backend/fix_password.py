"""
Fix bcrypt password issue by resetting test user password
"""
import sys
sys.path.insert(0, '.')

# Workaround for bcrypt initialization bug with Python 3.13
import bcrypt
# Initialize bcrypt with a short password to avoid the 72-byte bug during initialization
try:
    bcrypt.hashpw(b"test", bcrypt.gensalt())
except:
    pass

from app.db.database import get_db
from app.models.database import User
from app.core.security import hash_password

def fix_password():
    """Reset the test user password to a shorter, valid one"""
    db = next(get_db())
    
    try:
        # Get the first user (test user)
        user = db.query(User).first()
        
        if user:
            print(f"Found user: {user.email}")
            
            # Set a simple, valid password
            new_password = "TestPass123!"
            user.password_hash = hash_password(new_password)
            
            db.commit()
            
            print(f"✅ Password reset successfully!")
            print(f"New credentials:")
            print(f"  Email: {user.email}")
            print(f"  Password: {new_password}")
        else:
            print("No users found in database")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_password()
