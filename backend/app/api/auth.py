from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "developer"
    department: Optional[str] = None
    team: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: str
    role: str
    department: Optional[str]
    team: Optional[str]
    is_active: bool


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    try:
        user = await auth_service.create_user(
            db=db,
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            department=user_data.department,
            team=user_data.team,
        )
        return user.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Login and get access token."""
    user = await auth_service.authenticate_user(
        db=db,
        username=form_data.username,
        password=form_data.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return auth_service.create_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token."""
    tokens = await auth_service.refresh_access_token(db, request.refresh_token)
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""
    return current_user.to_dict()


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password."""
    success = await auth_service.change_password(
        db=db,
        user_id=str(current_user.id),
        current_password=current_password,
        new_password=new_password,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password",
        )
    
    return {"message": "Password changed successfully"}
