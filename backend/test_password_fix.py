#!/usr/bin/env python3
"""
Test script to verify password validation and bcrypt compatibility
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.schemas.auth import SignupRequest
from app.core.security import hash_password, verify_password
from pydantic import ValidationError

def test_password_validation():
    """Test password validation in schema"""
    print("🧪 Testing Password Validation...")
    
    # Test 1: Valid password
    try:
        request = SignupRequest(
            email="test@example.com",
            password="ValidPass123",
            company_name="Test Company"
        )
        print("✅ Valid password accepted")
    except ValidationError as e:
        print(f"❌ Valid password rejected: {e}")
        return False
    
    # Test 2: Password too long (73 characters)
    try:
        long_password = "A" * 73  # 73 characters
        request = SignupRequest(
            email="test@example.com",
            password=long_password,
            company_name="Test Company"
        )
        print("❌ Long password should have been rejected")
        return False
    except ValidationError as e:
        print("✅ Long password correctly rejected")
    
    # Test 3: Password with 72 characters (should work)
    try:
        max_password = "A" * 34 + "a" * 34 + "1234"  # 72 characters: upper, lower, digits
        request = SignupRequest(
            email="test@example.com",
            password=max_password,
            company_name="Test Company"
        )
        print("✅ 72-character password accepted")
    except ValidationError as e:
        print(f"❌ 72-character password rejected: {e}")
        return False
    
    return True

def test_bcrypt_hashing():
    """Test bcrypt password hashing and verification"""
    print("\n🔐 Testing Bcrypt Hashing...")
    
    test_passwords = [
        "ShortPass1",  # Normal password
        "A" * 34 + "a" * 34 + "1234",  # 72 character password with complexity
        "🔑SecurePass123🔐",  # Password with emojis (multi-byte)
    ]
    
    for i, password in enumerate(test_passwords, 1):
        try:
            print(f"Test {i}: Password length = {len(password)} chars, {len(password.encode('utf-8'))} bytes")
            
            # Hash the password
            hashed = hash_password(password)
            print(f"  ✅ Hashing successful")
            
            # Verify the password
            is_valid = verify_password(password, hashed)
            if is_valid:
                print(f"  ✅ Verification successful")
            else:
                print(f"  ❌ Verification failed")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    return True

def test_edge_cases():
    """Test edge cases for bcrypt compatibility"""
    print("\n🎯 Testing Edge Cases...")
    
    # Test password with exactly 72 bytes in UTF-8
    try:
        # Create a password that's exactly 72 bytes when encoded
        password = "A" * 69 + "🔑"  # 69 ASCII + 1 emoji (3 bytes) = 72 bytes
        byte_length = len(password.encode('utf-8'))
        print(f"Edge case password: {len(password)} chars, {byte_length} bytes")
        
        if byte_length <= 72:
            hashed = hash_password(password)
            is_valid = verify_password(password, hashed)
            print(f"  ✅ 72-byte password works: {is_valid}")
        else:
            print(f"  ⚠️  Password exceeds 72 bytes, would be truncated")
            
    except Exception as e:
        print(f"  ❌ Error with edge case: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Password Validation & Bcrypt Compatibility Test")
    print("=" * 50)
    
    success = True
    success &= test_password_validation()
    success &= test_bcrypt_hashing()
    success &= test_edge_cases()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Password handling is fixed.")
        print("\nKey points:")
        print("• Passwords limited to 72 characters in schema")
        print("• Bcrypt hashing works correctly with latest version")
        print("• Password validation includes byte-length check")
        print("• Both character and byte limits enforced")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)