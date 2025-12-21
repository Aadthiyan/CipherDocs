"""
User management endpoints for admin users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
import secrets
import string

from app.db.database import get_db
from app.models.database import User, Tenant
from app.schemas.users import (
    UserCreate, UserUpdate, UserRoleUpdate,
    UserDetailResponse, UserListResponse, UsersListResponse,
    UserInviteResponse
)
from app.api.deps import get_current_user, get_current_tenant
from app.core import security
from app.core.rbac import UserRole, require_role, check_role_hierarchy
from app.db.tenant_scoping import get_tenant_scoped_query
import logging

router = APIRouter(prefix="/users", tags=["User Management"])
logger = logging.getLogger(__name__)


def generate_temporary_password(length: int = 12) -> str:
    """
    Generate a secure temporary password.
    
    Args:
        length: Password length (default 12)
        
    Returns:
        Random password string
    """
    # Ensure password meets complexity requirements
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Ensure it has at least one uppercase, lowercase, and digit
    password = (
        secrets.choice(string.ascii_uppercase) +
        secrets.choice(string.ascii_lowercase) +
        secrets.choice(string.digits) +
        password[3:]
    )
    
    return password


@router.post(
    "",
    response_model=UserInviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite new user (Admin only)",
    description="Create a new user account and generate a temporary password. Admin role required."
)
@require_role(UserRole.ADMIN)
async def invite_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Invite a new user to the tenant.
    
    - **email**: User's email address (must be unique)
    - **role**: User role (admin, user, or viewer)
    
    Returns user details and temporary password.
    Admin should send the temporary password to the user securely.
    """
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Generate temporary password
    temp_password = generate_temporary_password()
    password_hash = security.hash_password(temp_password)
    
    try:
        # Create new user
        new_user = User(
            id=uuid.uuid4(),
            email=request.email,
            password_hash=password_hash,
            tenant_id=current_tenant.id,
            role=request.role.value,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Log user creation
        logger.info(
            f"User invited: user_id={new_user.id} email={new_user.email} "
            f"role={new_user.role} by={current_user.email} tenant_id={current_tenant.id}"
        )
        
        return UserInviteResponse(
            user=UserDetailResponse.model_validate(new_user),
            temporary_password=temp_password,
            message="User invited successfully. Send them the temporary password."
        )
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered or database constraint violation"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get(
    "",
    response_model=UsersListResponse,
    summary="List tenant users (Admin only)",
    description="Get a list of all users in the current tenant. Admin role required."
)
@require_role(UserRole.ADMIN)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    List all users in the current tenant.
    
    - **skip**: Number of users to skip (pagination)
    - **limit**: Maximum number of users to return
    
    Returns paginated list of users.
    """
    
    # Get tenant-scoped query
    tq = get_tenant_scoped_query(db)
    
    # Get total count
    total = tq.query(User).count()
    
    # Get paginated users
    users = (
        tq.query(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return UsersListResponse(
        users=[UserListResponse.model_validate(user) for user in users],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Get user details (Admin only)",
    description="Get detailed information about a specific user. Admin role required."
)
@require_role(UserRole.ADMIN)
async def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get details of a specific user.
    
    - **user_id**: The user's UUID
    
    Returns user details if found and belongs to current tenant.
    """
    
    # Get tenant-scoped query
    tq = get_tenant_scoped_query(db)
    
    # Get user
    user = tq.get_by_id(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserDetailResponse.model_validate(user)


@router.patch(
    "/{user_id}/role",
    response_model=UserDetailResponse,
    summary="Update user role (Admin only)",
    description="Change a user's role. Admin role required."
)
@require_role(UserRole.ADMIN)
async def update_user_role(
    user_id: uuid.UUID,
    request: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Update a user's role.
    
    - **user_id**: The user's UUID
    - **role**: New role (admin, user, or viewer)
    
    Returns updated user details.
    """
    
    # Get tenant-scoped query
    tq = get_tenant_scoped_query(db)
    
    # Get user
    user = tq.get_by_id(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-demotion
    if user.id == current_user.id and request.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role from admin"
        )
    
    # Check role hierarchy
    if not check_role_hierarchy(current_user.role, user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to modify this user"
        )
    
    # Update role
    old_role = user.role
    user.role = request.role.value
    
    db.commit()
    db.refresh(user)
    
    # Log role change
    logger.info(
        f"User role updated: user_id={user.id} email={user.email} "
        f"old_role={old_role} new_role={user.role} by={current_user.email}"
    )
    
    return UserDetailResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete user (Admin only)",
    description="Remove a user from the tenant. Admin role required."
)
@require_role(UserRole.ADMIN)
async def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Delete a user from the tenant.
    
    - **user_id**: The user's UUID
    
    Returns success message.
    """
    
    # Get tenant-scoped query
    tq = get_tenant_scoped_query(db)
    
    # Get user
    user = tq.get_by_id(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Check role hierarchy
    if not check_role_hierarchy(current_user.role, user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete this user"
        )
    
    # Delete user
    user_email = user.email
    db.delete(user)
    db.commit()
    
    # Log user deletion
    logger.info(
        f"User deleted: user_id={user_id} email={user_email} "
        f"by={current_user.email} tenant_id={current_tenant.id}"
        )
    
    return {
        "message": "User deleted successfully",
        "user_id": str(user_id),
        "email": user_email
    }


@router.patch(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Update user (Admin only)",
    description="Update user details. Admin role required."
)
@require_role(UserRole.ADMIN)
async def update_user(
    user_id: uuid.UUID,
    request: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Update user details.
    
    - **user_id**: The user's UUID
    - **role**: Optional new role
    - **is_active**: Optional active status
    
    Returns updated user details.
    """
    
    # Get tenant-scoped query
    tq = get_tenant_scoped_query(db)
    
    # Get user
    user = tq.get_by_id(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-modification in certain ways
    if user.id == current_user.id:
        if request.role and request.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own role from admin"
            )
        if request.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
    
    # Update fields
    if request.role:
        user.role = request.role.value
    if request.is_active is not None:
        user.is_active = request.is_active
    
    db.commit()
    db.refresh(user)
    
    # Log user update
    logger.info(
        f"User updated: user_id={user.id} email={user.email} "
        f"by={current_user.email}"
    )
    
    return UserDetailResponse.model_validate(user)
