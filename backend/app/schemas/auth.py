"""
Authentication and user schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Ensure passwords match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_new_password(cls, v, values):
        """Validate new password if provided."""
        if v and not values.get('current_password'):
            raise ValueError('Current password is required to change password')
        if v:
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not re.search(r'[a-z]', v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not re.search(r'\d', v):
                raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Schema for decoded token data."""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str
