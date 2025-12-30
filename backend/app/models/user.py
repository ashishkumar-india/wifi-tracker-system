"""
User model for authentication and authorization.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    VIEWER = "viewer"


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="viewer", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    acknowledged_alerts = relationship("Alert", back_populates="acknowledged_by_user", foreign_keys="Alert.acknowledged_by")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    def to_dict(self):
        """Convert user to dictionary (excluding password)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role == "admin"
