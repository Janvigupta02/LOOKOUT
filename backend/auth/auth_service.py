from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os

from models.database_models import User
from database import get_db
from .models import TokenData

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-please-make-it-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer for token authentication
security = HTTPBearer()

class AuthService:
    """Authentication service for user management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        # Truncate to 72 bytes for bcrypt compatibility
        if len(password.encode()) > 72:
            password = password[:72]
        return pwd_context.hash(password)
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def create_user(db: Session, email: str, password: str) -> User:
        """Create a new user"""
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        hashed_password = AuthService.get_password_hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Verify JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
        
        return TokenData(email=email)
    
    except JWTError:
        raise credentials_exception

def get_current_user(
    token_data: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    user = db.query(User).filter(User.email == token_data.email).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return demo user"""
    if not credentials:
        # Return demo user for backwards compatibility
        user = db.query(User).filter(User.email == "demo@marketpulse.com").first()
        return user
    
    try:
        token_data = verify_token(credentials)
        user = db.query(User).filter(User.email == token_data.email).first()
        return user
    except HTTPException:
        # Return demo user on auth failure
        user = db.query(User).filter(User.email == "demo@marketpulse.com").first()
        return user
