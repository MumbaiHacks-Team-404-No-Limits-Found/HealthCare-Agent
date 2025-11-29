"""Authentication utilities: password hashing, JWT tokens, and user verification."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt

from app.config import settings
from app.database import get_collection
from app.models import PyObjectId

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(plain: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        plain: Plain text password
        
    Returns:
        Hashed password string (bcrypt format)
    """
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain: Plain text password
        hashed: Hashed password string
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing token payload (typically user info)
        expires_delta: Optional expiration time delta. If None, uses default from settings.
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Get current authenticated user from JWT token.
    
    This is a dependency function that can be used in FastAPI route handlers.
    It extracts the token from the Authorization header, decodes it, and fetches
    the user from the database.
    
    Args:
        token: JWT token (automatically extracted from Authorization header)
        
    Returns:
        Dictionary with user info (id, email, role)
        
    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Fetch user from database
    users_collection = get_collection("users")
    user_doc = await users_collection.find_one({"email": email})
    if user_doc is None:
        raise credentials_exception
    
    return {
        "id": str(user_doc.get("_id")),
        "email": user_doc.get("email"),
        "role": user_doc.get("role", "admin")
    }

