"""
Security utilities for JWT authentication and password hashing.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
import secrets

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        The encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_hex(16)  # Unique token ID
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: The JWT token to decode
        
    Returns:
        The decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token_type(token: str, expected_type: str) -> Optional[Dict[str, Any]]:
    """
    Verify token type matches expected.
    
    Args:
        token: The JWT token to verify
        expected_type: Either 'access' or 'refresh'
        
    Returns:
        The decoded token data or None if invalid or wrong type
    """
    payload = decode_token(token)
    if payload and payload.get("type") == expected_type:
        return payload
    return None


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        A random 32-character hex string
    """
    return secrets.token_hex(32)


def is_token_expired(payload: Dict[str, Any]) -> bool:
    """
    Check if a token has expired.
    
    Args:
        payload: The decoded token payload
        
    Returns:
        True if expired, False otherwise
    """
    exp = payload.get("exp")
    if not exp:
        return True
    
    if isinstance(exp, int):
        exp = datetime.fromtimestamp(exp)
    
    return datetime.utcnow() > exp
