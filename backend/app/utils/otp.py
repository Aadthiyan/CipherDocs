"""
OTP (One-Time Password) utility functions
Handles OTP generation, validation, and expiry checking
"""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Tuple
import os
from dotenv import load_dotenv

load_dotenv()

# OTP expiration time in minutes (default: 10 minutes)
OTP_EXPIRATION_MINUTES = int(os.getenv("OTP_EXPIRATION_MINUTES", 10))


def generate_otp_code(length: int = 6) -> str:
    """
    Generate a secure random OTP code
    
    Args:
        length: Length of OTP code (default: 6 digits)
    
    Returns:
        str: Random OTP code (e.g., "123456")
    """
    # Generate cryptographically secure random digits
    digits = string.digits
    otp = ''.join(secrets.choice(digits) for _ in range(length))
    return otp


def get_otp_expiry_time() -> datetime:
    """
    Calculate OTP expiration timestamp
    
    Returns:
        datetime: Timestamp when OTP expires
    """
    return datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRATION_MINUTES)


def is_otp_expired(expiry_time: datetime) -> bool:
    """
    Check if OTP has expired
    
    Args:
        expiry_time: OTP expiration timestamp
    
    Returns:
        bool: True if expired, False otherwise
    """
    if expiry_time is None:
        return True
    
    # Make comparison timezone-aware
    current_time = datetime.now(timezone.utc)
    
    # If expiry_time is naive, make it aware (assume UTC)
    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=timezone.utc)
    
    return current_time > expiry_time


def verify_otp(provided_code: str, stored_code: str, expiry_time: datetime) -> Tuple[bool, str]:
    """
    Verify OTP code
    
    Args:
        provided_code: Code provided by user
        stored_code: Code stored in database
        expiry_time: OTP expiration timestamp
    
    Returns:
        Tuple[bool, str]: (success, error_message)
    """
    # Check if OTP exists
    if not stored_code:
        return False, "No verification code found. Please request a new code."
    
    # Check if OTP has expired
    if is_otp_expired(expiry_time):
        return False, "Verification code has expired. Please request a new code."
    
    # Verify the code matches
    if provided_code.strip() != stored_code.strip():
        return False, "Invalid verification code. Please try again."
    
    return True, "Verification successful"


def format_time_remaining(expiry_time: datetime) -> str:
    """
    Format remaining time until OTP expires
    
    Args:
        expiry_time: OTP expiration timestamp
    
    Returns:
        str: Human-readable time remaining (e.g., "5 minutes")
    """
    if is_otp_expired(expiry_time):
        return "expired"
    
    remaining = expiry_time - datetime.utcnow()
    minutes = int(remaining.total_seconds() / 60)
    seconds = int(remaining.total_seconds() % 60)
    
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
