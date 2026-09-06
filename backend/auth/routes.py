from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from database import get_db
from .models import UserCreate, UserLogin, Token, UserResponse
from .auth_service import AuthService, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from models.database_models import User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account
    
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters recommended)
    """
    # Validate password length
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    # Create user
    user = AuthService.create_user(db, user_data.email, user_data.password)
    
    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password
    
    Returns JWT access token for authenticated requests
    """
    user = AuthService.authenticate_user(db, user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Requires valid JWT token in Authorization header
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at.isoformat()
    )

@router.post("/demo-login", response_model=Token)
def demo_login(db: Session = Depends(get_db)):
    """
    Quick demo login (no credentials required)
    
    Returns token for demo user account
    """
    demo_user = db.query(User).filter(User.email == "demo@marketpulse.com").first()
    
    if not demo_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo user not found. Please run seed_database.py"
        )
    
    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": demo_user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
