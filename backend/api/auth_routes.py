"""
Authentication routes for the Blank App.

This module provides user registration, login, and token management
endpoints with proper database persistence and JWT token issuance.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from backend.db import get_db
from backend.models.auth import User

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# Request/Response schemas
class UserRegister(BaseModel):
    """Schema for user registration requests."""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login requests."""
    username: str
    password: str


class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    """Schema for user data in responses."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    email: Optional[str] = None
    full_name: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str


def _get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username (case-insensitive)."""
    return db.query(User).filter(User.username.ilike(username)).first()


def _get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email (case-insensitive)."""
    return db.query(User).filter(User.email.ilike(email)).first()


@router.post("/register", response_model=UserResponse, summary="Register a new user")
async def register_user(payload: UserRegister, db: Session = Depends(get_db)) -> User:
    """Register a new user.
    
    Creates a new user account with the provided credentials.
    Validates that username and email are unique.
    """
    # Validate input
    if not payload.username or not payload.password or not payload.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username, email, and password are required",
        )
    
    # Check username uniqueness
    if _get_user_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    
    # Check email uniqueness
    if _get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    hashed_password = get_password_hash(payload.password)
    new_user = User(
        username=payload.username.lower().strip(),
        email=payload.email.lower().strip(),
        hashed_password=hashed_password,
        full_name=payload.full_name,
        is_active=True,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/token", response_model=Token, summary="Login and get access token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> dict:
    """Authenticate user and return JWT access token.
    
    Accepts OAuth2 password credentials and returns a JWT token
    for use in subsequent authenticated requests.
    """
    # Find user by username
    user = _get_user_by_username(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/login", response_model=Token, summary="Authenticate and get token (JSON)")
async def login_user(payload: UserLogin, db: Session = Depends(get_db)) -> dict:
    """Authenticate a user and return JWT token (JSON endpoint).
    
    Similar to /token but accepts JSON payload instead of form data.
    """
    return await login_for_access_token(
        form_data=OAuth2PasswordRequestForm(
            username=payload.username,
            password=payload.password,
            scope="",
            client_id=None,
            client_secret=None,
        ),
        db=db
    )


@router.get("/me", response_model=UserResponse, summary="Get current user info")
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> User:
    """Get information about the currently authenticated user."""
    return current_user


@router.put("/me", response_model=UserResponse, summary="Update current user profile")
async def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Update the current user's profile information."""
    if payload.email and payload.email != current_user.email:
        # Check email uniqueness
        if _get_user_by_email(db, payload.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = payload.email.lower().strip()
    
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password", summary="Change current user password")
async def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Change the current user's password."""
    # Verify current password
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout", summary="Logout current user")
async def logout() -> dict:
    """Logout endpoint.
    
    Note: With JWT tokens, actual logout is handled client-side by
    deleting the token. This endpoint is provided for consistency
    and can be extended to implement token blacklisting.
    """
    return {"message": "Logout successful"}
