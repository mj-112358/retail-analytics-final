"""
FINAL PRODUCTION AUTHENTICATION SYSTEM
Complete user management with database integration
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
import asyncpg
import logging

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "24"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30

# Refresh token secret (different from access token)
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "your-refresh-secret-key-change-in-production")

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

# Pydantic Models
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str
    store_name: str
    phone: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class User(BaseModel):
    id: int
    email: str
    name: str
    store_name: str
    phone: Optional[str]
    is_active: bool
    subscription_plan: str
    created_at: datetime

# Database functions
async def get_db_connection():
    """Get database connection"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

async def create_user_in_db(user_data: UserSignup) -> Optional[Dict]:
    """Create new user in database"""
    conn = await get_db_connection()
    try:
        # Check if user already exists
        existing_user = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            user_data.email
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = bcrypt.hashpw(
            user_data.password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Insert user
        user_record = await conn.fetchrow("""
            INSERT INTO users (email, password_hash, name, store_name, phone)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, email, name, store_name, phone, is_active, subscription_plan, created_at
        """, user_data.email, password_hash, user_data.name, user_data.store_name, user_data.phone)
        
        # Create default store
        store_record = await conn.fetchrow("""
            INSERT INTO stores (user_id, name, timezone)
            VALUES ($1, $2, $3)
            RETURNING id, name
        """, user_record['id'], user_data.store_name, 'UTC')
        
        user_dict = dict(user_record)
        user_dict['store_id'] = store_record['id']
        return user_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    finally:
        await conn.close()

async def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """Authenticate user with email and password"""
    conn = await get_db_connection()
    try:
        # Get user with password hash
        user_record = await conn.fetchrow("""
            SELECT u.id, u.email, u.password_hash, u.name, u.store_name, u.phone, 
                   u.is_active, u.subscription_plan, u.created_at, s.id as store_id
            FROM users u
            LEFT JOIN stores s ON u.id = s.user_id
            WHERE u.email = $1 AND u.is_active = true
            LIMIT 1
        """, email)
        
        if not user_record:
            return None
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user_record['password_hash'].encode('utf-8')):
            return None
        
        # Remove password hash from response
        user_dict = dict(user_record)
        del user_dict['password_hash']
        return user_dict
        
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return None
    finally:
        await conn.close()

async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    conn = await get_db_connection()
    try:
        user_record = await conn.fetchrow("""
            SELECT u.id, u.email, u.name, u.store_name, u.phone, 
                   u.is_active, u.subscription_plan, u.created_at, s.id as store_id
            FROM users u
            LEFT JOIN stores s ON u.id = s.user_id
            WHERE u.id = $1 AND u.is_active = true
        """, user_id)
        
        return dict(user_record) if user_record else None
        
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None
    finally:
        await conn.close()

# Token functions
def create_access_token(user_data: Dict) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": str(user_data["id"]),
        "email": user_data["email"],
        "store_id": user_data.get("store_id"),
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: int) -> str:
    """Create JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """Verify JWT token"""
    try:
        secret_key = JWT_SECRET_KEY if token_type == "access" else REFRESH_SECRET_KEY
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != token_type:
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Dependency functions for FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = int(sub)
    user = await get_user_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_store(current_user: Dict = Depends(get_current_user)) -> int:
    """Get current user's store ID"""
    store_id = current_user.get("store_id")
    if not store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No store associated with user"
        )
    return store_id

# Auth endpoints
async def signup_user(user_data: UserSignup) -> TokenResponse:
    """Register new user"""
    try:
        # Create user in database
        user_record = await create_user_in_db(user_data)
        
        if user_record is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Generate tokens
        access_token = create_access_token(user_record)
        refresh_token = create_refresh_token(user_record["id"])
        
        # Prepare user data (without sensitive info)
        user_info = {
            "id": user_record["id"],
            "email": user_record["email"],
            "name": user_record["name"],
            "store_name": user_record["store_name"],
            "store_id": user_record["store_id"],
            "subscription_plan": user_record["subscription_plan"]
        }
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

async def login_user(login_data: UserLogin) -> TokenResponse:
    """Login user"""
    try:
        # Authenticate user
        user_record = await authenticate_user(login_data.email, login_data.password)
        
        if not user_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate tokens
        access_token = create_access_token(user_record)
        refresh_token = create_refresh_token(user_record["id"])
        
        # Prepare user data
        user_info = {
            "id": user_record["id"],
            "email": user_record["email"],
            "name": user_record["name"],
            "store_name": user_record["store_name"],
            "store_id": user_record.get("store_id"),
            "subscription_plan": user_record["subscription_plan"]
        }
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

async def refresh_access_token(refresh_token: str) -> TokenResponse:
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user data
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject"
            )
        user_id = int(sub)
        user_record = await get_user_by_id(user_id)
        
        if not user_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Generate new access token
        new_access_token = create_access_token(user_record)
        
        # Prepare user data
        user_info = {
            "id": user_record["id"],
            "email": user_record["email"],
            "name": user_record["name"],
            "store_name": user_record["store_name"],
            "store_id": user_record.get("store_id"),
            "subscription_plan": user_record["subscription_plan"]
        }
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,  # Keep same refresh token
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )