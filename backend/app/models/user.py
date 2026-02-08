import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.db.session import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(50), nullable=False, default="developer")
    department = Column(String(100), nullable=True)
    team = Column(String(100), nullable=True)
    
    # Permissions
    permissions = Column(ARRAY(String), default=list)
    teams = Column(ARRAY(String), default=list)  # Multiple team membership
    
    # Status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    
    # Metadata
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('ix_users_role', 'role'),
        Index('ix_users_team', 'team'),
    )
    
    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True
        if self.permissions:
            return permission in self.permissions or "*" in self.permissions
        return False
    
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "role": self.role,
            "department": self.department,
            "team": self.team,
            "teams": self.teams,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
