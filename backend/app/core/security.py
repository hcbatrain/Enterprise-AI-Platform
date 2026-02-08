from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the current user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_permissions(user: User, required_permissions: List[str]) -> bool:
    """Check if a user has all required permissions."""
    user_permissions = set(user.permissions or [])
    return all(perm in user_permissions for perm in required_permissions)


def require_permissions(required_permissions: List[str]):
    """Dependency factory to require specific permissions."""
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == "administrator":
            return current_user
        
        if not check_permissions(current_user, required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permissions}"
            )
        return current_user
    return permission_checker


# Role-based permission definitions
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "business_analyst": [
        "read:documents",
        "write:documents",
        "read:business_rules",
        "write:business_rules",
        "use:chat",
        "read:knowledge",
    ],
    "qa_tester": [
        "read:documents",
        "write:test_cases",
        "read:test_data",
        "use:chat",
        "read:knowledge",
        "read:code",
    ],
    "developer": [
        "read:documents",
        "read:code",
        "write:code",
        "read:api_docs",
        "use:chat",
        "read:knowledge",
        "read:data_models",
    ],
    "data_engineer": [
        "read:documents",
        "read:code",
        "write:etl",
        "read:data_models",
        "write:data_models",
        "use:chat",
        "read:knowledge",
    ],
    "technical_architect": [
        "read:documents",
        "write:architecture",
        "read:code",
        "read:all_systems",
        "use:chat",
        "read:knowledge",
        "write:knowledge",
    ],
    "project_manager": [
        "read:documents",
        "write:reports",
        "read:project_data",
        "use:chat",
        "read:knowledge",
        "read:team_metrics",
    ],
    "manager": [
        "read:documents",
        "read:team_metrics",
        "read:org_data",
        "write:reports",
        "use:chat",
        "read:knowledge",
        "read:dashboards",
    ],
    "administrator": [
        "*",  # All permissions
    ],
    "executive": [
        "read:dashboards",
        "read:org_data",
        "read:reports",
        "use:chat",
        "read:summary",
    ],
}


def get_role_permissions(role: str) -> List[str]:
    """Get permissions for a specific role."""
    return ROLE_PERMISSIONS.get(role, [])
