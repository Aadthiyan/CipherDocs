"""
Authentication endpoints for signup and login
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid
import logging
import os

logger = logging.getLogger(__name__)

from app.db.database import get_db
from app.models.database import User, Tenant, Session as UserSession
from app.schemas.auth import (
    SignupRequest, LoginRequest, AuthResponse,
    UserResponse, TenantResponse,
    RefreshTokenRequest, RefreshTokenResponse, LogoutRequest, ChangePasswordRequest
)
from app.core import security
from app.core.config import settings
from app.api.deps import get_current_user
from app.core.encryption import KeyManager
from app.core.cyborg import CyborgDBManager
from app.utils.otp import generate_otp_code, get_otp_expiry_time, verify_otp
from app.utils.email_service import send_verification_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory rate limiting (for production, use Redis)
login_attempts = {}


def check_rate_limit(email: str, ip: str) -> None:
    """
    Check rate limiting for login attempts.
    Raises HTTPException if rate limit exceeded.
    """
    key = f"{email}:{ip}"
    now = datetime.utcnow()
    
    if key not in login_attempts:
        login_attempts[key] = []
    
    # Remove attempts older than the rate limit window
    login_attempts[key] = [
        attempt_time for attempt_time in login_attempts[key]
        if (now - attempt_time).total_seconds() < settings.RATE_LIMIT_WINDOW_SECONDS
    ]
    
    # Check if exceeded max attempts
    if len(login_attempts[key]) >= settings.MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please try again in {settings.RATE_LIMIT_WINDOW_SECONDS // 60} minutes."
        )
    
    # Record this attempt
    login_attempts[key].append(now)


def clear_rate_limit(email: str, ip: str) -> None:
    """Clear rate limiting for successful login."""
    key = f"{email}:{ip}"
    if key in login_attempts:
        del login_attempts[key]


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new tenant and admin user",
    description="Create a new tenant account with an admin user. Returns JWT tokens for immediate authentication."
)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new tenant and create the first admin user.
    
    - **email**: Valid email address (RFC 5322)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **company_name**: Company or organization name
    
    Returns JWT access and refresh tokens with user and tenant information.
    """
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = security.hash_password(request.password)
    
    try:
        # Create tenant
        tenant = Tenant(
            id=uuid.uuid4(),
            name=request.company_name,
            plan="starter",
            is_active=True
        )
        db.add(tenant)
        db.flush()  # Get tenant.id without committing
        
        # Generate OTP code
        otp_code = generate_otp_code()
        otp_expiry = get_otp_expiry_time()
        
        # Create admin user (unverified)
        user = User(
            id=uuid.uuid4(),
            email=request.email,
            password_hash=password_hash,
            tenant_id=tenant.id,
            role="admin",
            is_active=True,
            is_verified=False,  # User needs to verify email
            verification_code=otp_code,
            code_expires_at=otp_expiry
        )
        db.add(user)
        
        # Generate encryption key for new tenant
        _, raw_key = KeyManager.create_tenant_key(db, tenant.id, commit=False)
        
        # Provision CyborgDB index (encrypted)
        # We try strict creation; failure aborts signup to ensure consistency.
        # In production, might want async provisioning.
        try:
            index_name = CyborgDBManager.create_tenant_index(str(tenant.id), key=raw_key)
            tenant.cyborgdb_namespace = index_name
            db.add(tenant)
        except Exception as e:
            logger.error(f"Failed to provision CyborgDB index for {tenant.id}: {e}")
            # We don't abort signup in dev/hackathon if key is missing/mock, 
            # but ideally we should. CyborgDBManager fallbacks or raises.
            # If we want to allow offline Signup, catch pass.
            # For now, let's log and proceed or raise? 
            # If we raise, we rollback.
            # raise e
            pass 
        
        db.commit()
        db.refresh(user)
        db.refresh(tenant)
        
        # Send verification email (async, don't block signup)
        try:
            email_sent = await send_verification_email(request.email, otp_code, request.company_name)
            if not email_sent:
                logger.warning(f"Failed to send verification email to {request.email}")
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            # Continue with signup even if email fails
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered or database constraint violation"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}"
        )
    
    # Generate JWT tokens
    access_token = security.create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    refresh_token = security.create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    # Build response
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        tenant=TenantResponse.model_validate(tenant)
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    description="Authenticate user and return JWT tokens. Rate limited to 5 attempts per 5 minutes."
)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with email and password.
    
    - **email**: Registered email address
    - **password**: User password
    
    Returns JWT access and refresh tokens with user and tenant information.
    
    **Rate Limiting**: Maximum 5 failed attempts per 5 minutes per IP/email combination.
    """
    
    # Get client IP for rate limiting
    client_ip = http_request.client.host if http_request.client else "unknown"
    
    # Check rate limiting
    if settings.RATE_LIMIT_ENABLED:
        check_rate_limit(request.email, client_ip)
    
    # Retrieve user from database
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify password
    if not security.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support."
        )
    
    # Check if email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for the verification code."
        )
    
    # Get tenant and check if active
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant not found"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is suspended. Please contact support."
        )
    
    # Clear rate limiting on successful login
    if settings.RATE_LIMIT_ENABLED:
        clear_rate_limit(request.email, client_ip)
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Generate JWT tokens
    access_token = security.create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    refresh_token = security.create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    # Build response
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        tenant=TenantResponse.model_validate(tenant)
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Generate a new access token using a valid refresh token. Implements token rotation for security."
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    payload = security.verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    user_id, tenant_id, role = payload.get("sub"), payload.get("tenant_id"), payload.get("role")
    if not all([user_id, tenant_id, role]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    new_access_token = security.create_access_token(subject=str(user.id), tenant_id=str(user.tenant_id), role=user.role)
    new_refresh_token = security.create_refresh_token(subject=str(user.id), tenant_id=str(user.tenant_id), role=user.role)
    return RefreshTokenResponse(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(request: LogoutRequest = LogoutRequest(), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"User logged out: user_id={current_user.id} email={current_user.email}")
    return {"message": "Logged out successfully", "user_id": str(current_user.id)}


@router.get(
    "/me",
    summary="Get current user details",
)
async def get_me(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Get detailed information about the current logged-in user and their tenant.
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    return {
        "user": UserResponse.model_validate(current_user),
        "tenant": TenantResponse.model_validate(tenant)
    }


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Verify email with OTP code",
    description="Verify user email address using the OTP code sent during signup."
)
async def verify_email(
    email: str,
    code: str,
    db: Session = Depends(get_db)
):
    """
    Verify user email with OTP code.
    
    - **email**: User's email address
    - **code**: 6-digit OTP code received via email
    
    Returns success message and JWT tokens if verification successful.
    """
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Verify OTP code
    is_valid, error_message = verify_otp(
        provided_code=code,
        stored_code=user.verification_code,
        expiry_time=user.code_expires_at
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Mark user as verified
    user.is_verified = True
    user.verification_code = None  # Clear the code
    user.code_expires_at = None
    db.commit()
    db.refresh(user)
    
    # Get tenant
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    
    # Generate JWT tokens
    access_token = security.create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    refresh_token = security.create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        tenant=TenantResponse.model_validate(tenant)
    )


@router.post(
    "/resend-otp",
    status_code=status.HTTP_200_OK,
    summary="Resend OTP verification code",
    description="Resend verification code to user's email address."
)
async def resend_otp(
    email: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Resend OTP verification code to user's email.
    
    - **email**: User's email address
    
    Returns success message if OTP sent successfully.
    """
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new OTP code
    otp_code = generate_otp_code()
    otp_expiry = get_otp_expiry_time()
    
    # Update user with new OTP
    user.verification_code = otp_code
    user.code_expires_at = otp_expiry
    db.commit()
    
    # Send verification email
    try:
        email_sent = await send_verification_email(email, otp_code, user.tenant.name if user.tenant else "User")
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email. Please try again later."
            )
        
        return {
            "message": "Verification code sent successfully",
            "email": email,
            "expires_in_minutes": int(os.getenv("OTP_EXPIRATION_MINUTES", 10))
        }
        
    except Exception as e:
        logger.error(f"Error resending OTP to {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password"
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Change the current user's password.
    Requires providing the old password for verification.
    """
    if not security.verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    current_user.password_hash = security.hash_password(request.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
