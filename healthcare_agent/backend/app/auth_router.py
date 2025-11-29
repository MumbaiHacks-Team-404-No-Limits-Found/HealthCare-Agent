"""Authentication REST endpoints: login and user info."""
from fastapi import APIRouter, HTTPException, status, Depends, Form
from pydantic import BaseModel, EmailStr

from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.database import get_collection


router = APIRouter()


class LoginRequest(BaseModel):
    """Request model for login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response model for login token."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Response model for user info."""
    id: str
    email: str
    role: str


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    Authenticate user with email and password.
    
    MongoDB Collections:
        - users: Queries by email to find user record
    
    Behavior:
        - Looks up user by email in the 'users' collection
        - Verifies password using bcrypt hash comparison
        - Creates JWT access token with email as subject (sub)
        - Returns token response on success
        
    Args:
        login_data: LoginRequest with email (EmailStr) and password (str)
        
    Returns:
        TokenResponse with:
        - access_token: JWT token string
        - token_type: "bearer"
        
    Raises:
        HTTPException 401: If email not found or password incorrect
            Detail: "Incorrect email or password"
    """
    users_collection = get_collection("users")
    
    # Find user by email
    user_doc = await users_collection.find_one({"email": login_data.email})
    if user_doc is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Login attempt failed: User not found for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    stored_password_hash = user_doc.get("password_hash")
    if not stored_password_hash:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"User {login_data.email} has no password_hash! Run 'python seed_admin.py' to fix.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    password_valid = verify_password(login_data.password, stored_password_hash)
    if not password_valid:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Login attempt failed: Invalid password for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    # Use email as subject (sub) in JWT payload
    access_token = create_access_token(data={"sub": login_data.email})
    
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
async def login_token(
    username: str = Form(..., description="Email address"),
    password: str = Form(..., description="Password"),
    grant_type: str = Form(default="password", description="OAuth2 grant type")
):
    """
    OAuth2 token endpoint for Swagger UI compatibility.
    
    This endpoint accepts form-encoded data (as required by OAuth2 password flow)
    and returns the same token response as /login.
    
    This is a compatibility endpoint for Swagger UI's OAuth2 password flow.
    Regular API clients should use /auth/login with JSON.
    
    Args:
        username: Email address (OAuth2 uses 'username' field)
        password: Password
        grant_type: OAuth2 grant type (must be 'password')
        
    Returns:
        TokenResponse with access_token and token_type
        
    Raises:
        HTTPException 401: If email not found or password incorrect
    """
    users_collection = get_collection("users")
    
    # Find user by email (username in OAuth2 terms)
    user_doc = await users_collection.find_one({"email": username})
    if user_doc is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Login attempt failed: User not found for email: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    stored_password_hash = user_doc.get("password_hash")
    if not stored_password_hash:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"User {username} has no password_hash! Run 'python seed_admin.py' to fix.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    password_valid = verify_password(password, stored_password_hash)
    if not password_valid:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Login attempt failed: Invalid password for email: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": username})
    
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    MongoDB Collections:
        - users: Queries by email (extracted from JWT token)
    
    Authentication:
        - Requires Authorization: Bearer <JWT> header
        - Uses get_current_user() dependency to extract and validate token
        - Token must be valid and not expired
        
    Args:
        current_user: User info dict from JWT token (injected by dependency)
            Contains: id, email, role
        
    Returns:
        UserResponse with:
        - id: User ID string
        - email: User email address
        - role: User role (typically "admin")
        
    Raises:
        HTTPException 401: If token is invalid, expired, or user not found
            Headers: WWW-Authenticate: Bearer
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user["role"]
    )

