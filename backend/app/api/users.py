from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.core.security import get_current_user, require_permissions
from app.models.user import User

router = APIRouter()


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    team: Optional[str] = None
    teams: Optional[List[str]] = None
    preferences: Optional[dict] = None


class UserListResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role: str
    department: Optional[str]
    team: Optional[str]
    is_active: bool


@router.get("/", response_model=List[UserListResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permissions(["read:org_data"])),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    
    users = result.scalars().all()
    return [user.to_dict() for user in users]


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific user."""
    user = await auth_service.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Users can only view their own profile unless they're admin
    if str(current_user.id) != user_id and current_user.role != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other users' profiles",
        )
    
    return user.to_dict()


@router.put("/me")
async def update_current_user(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile."""
    update_data = data.dict(exclude_unset=True)
    
    user = await auth_service.update_user(
        db=db,
        user_id=str(current_user.id),
        update_data=update_data,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user.to_dict()


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: User = Depends(require_permissions(["write:users"])),
    db: AsyncSession = Depends(get_db),
):
    """Update a user (admin only)."""
    update_data = data.dict(exclude_unset=True)
    
    user = await auth_service.update_user(
        db=db,
        user_id=user_id,
        update_data=update_data,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user.to_dict()
