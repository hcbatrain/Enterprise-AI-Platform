from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_role_permissions,
)
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)


class AuthService:
    """Service for authentication and user management."""
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        username: str,
        password: str,
    ) -> Optional[User]:
        """Authenticate a user by username and password."""
        
        result = await db.execute(
            select(User).where(
                (User.username == username) | (User.email == username)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        return user
    
    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        username: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: str = "developer",
        department: Optional[str] = None,
        team: Optional[str] = None,
        is_superuser: bool = False,
    ) -> User:
        """Create a new user."""
        
        # Check for existing user
        existing = await db.execute(
            select(User).where(
                (User.email == email) | (User.username == username)
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User with this email or username already exists")
        
        # Get permissions for role
        permissions = get_role_permissions(role)
        
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            department=department,
            team=team,
            permissions=permissions,
            is_superuser=is_superuser,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User created: {username} ({email})")
        
        return user
    
    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> Optional[User]:
        """Get a user by ID."""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """Get a user by email."""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def update_user(
        self,
        db: AsyncSession,
        user_id: str,
        update_data: Dict[str, Any],
    ) -> Optional[User]:
        """Update user information."""
        
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Update fields
        allowed_fields = [
            "first_name", "last_name", "department", "team",
            "teams", "preferences", "is_active"
        ]
        
        for field in allowed_fields:
            if field in update_data:
                setattr(user, field, update_data[field])
        
        # Handle password update separately
        if "password" in update_data:
            user.hashed_password = get_password_hash(update_data["password"])
        
        # Handle role update (update permissions too)
        if "role" in update_data:
            user.role = update_data["role"]
            user.permissions = get_role_permissions(update_data["role"])
        
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        return user
    
    def create_tokens(self, user: User) -> Dict[str, str]:
        """Create access and refresh tokens for a user."""
        
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    
    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token."""
        
        payload = decode_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = await self.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            return None
        
        return self.create_tokens(user)
    
    async def change_password(
        self,
        db: AsyncSession,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        if not verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        await db.commit()
        
        return True


# Global instance
auth_service = AuthService()
