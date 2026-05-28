from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from app.database import get_session
from app.models import User, UserCreate, UserLogin, UserResponse
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(
    payload: UserCreate, 
    session: Session = Depends(get_session)
):
    """Sign up a new user securely."""
    # Validate fields
    email = payload.email.strip().lower()
    username = payload.username.strip()
    
    if not email or not username or not payload.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All fields are required."
        )
        
    # Check duplicate email
    existing_email = session.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )
        
    # Check duplicate username
    existing_user = session.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken."
        )
        
    # Hash password securely
    hashed_pw = hash_password(payload.password)
    
    new_user = User(
        username=username,
        email=email,
        password=hashed_pw,
        is_admin=False
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@router.post("/login")
async def login(
    payload: UserLogin, 
    response: Response,
    session: Session = Depends(get_session)
):
    """Authenticate credentials and set JWT in HttpOnly cookie."""
    email = payload.email.strip().lower()
    user = session.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
        
    # Issue access token
    access_token = create_access_token(data={"sub": user.email})
    
    # Secure Cookie Injection: Set HttpOnly, SameSite cookie
    # secure=False is used for local HTTP development; must be secure=True in production (HTTPS)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="strict",
        secure=False,  # Set to True over HTTPS production
        path="/"
    )
    
    return {
        "success": True, 
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }


@router.post("/logout")
async def logout(response: Response):
    """Clear authorization session cookie."""
    response.delete_cookie(
        key="access_token", 
        path="/",
        samesite="strict",
        secure=False
    )
    return {"success": True, "message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Fetch profile data for currently authenticated session."""
    return current_user
