"""Authentication dependencies."""

import json
import requests
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from api.core.config import get_settings
from api.core.logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer()

# Cache for Cognito public keys
_cognito_keys_cache = None
_cache_expiry = None


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    roles: list[str] = []


class User(BaseModel):
    """User model."""
    id: str
    username: str
    email: str
    roles: list[str] = []
    is_active: bool = True


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def get_cognito_public_keys():
    """Get Cognito public keys for JWT verification."""
    global _cognito_keys_cache, _cache_expiry
    
    # Check cache
    if _cognito_keys_cache and _cache_expiry and datetime.utcnow() < _cache_expiry:
        return _cognito_keys_cache
    
    settings = get_settings()
    region = settings.AWS_REGION
    user_pool_id = settings.COGNITO_USER_POOL_ID
    
    # Fetch public keys from Cognito
    url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        keys = response.json()
        
        # Cache for 1 hour
        _cognito_keys_cache = keys
        _cache_expiry = datetime.utcnow() + timedelta(hours=1)
        
        return keys
    except Exception as e:
        logger.error("Failed to fetch Cognito public keys", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


def verify_cognito_token(token: str) -> TokenData:
    """Verify Cognito JWT token."""
    settings = get_settings()
    
    try:
        # Get token header
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header"
            )
        
        # Get public keys
        keys = get_cognito_public_keys()
        
        # Find the correct key
        public_key = None
        for key in keys['keys']:
            if key['kid'] == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break
        
        if not public_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token key"
            )
        
        # Verify token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=settings.COGNITO_APP_CLIENT_ID,
            issuer=f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
        )
        
        # Extract user data from Cognito token
        username = payload.get("cognito:username") or payload.get("email")
        user_id = payload.get("sub")
        email = payload.get("email")
        roles = payload.get("cognito:groups", [])
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return TokenData(
            username=username,
            user_id=user_id,
            email=email,
            roles=roles
        )
        
    except JWTError as e:
        logger.error("Cognito JWT verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token(token: str) -> TokenData:
    """Verify JWT token and extract data."""
    # Use Cognito verification instead of custom JWT
    return verify_cognito_token(token)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user."""
    token_data = verify_token(credentials.credentials)
    
    # In a real application, you would fetch user from database
    # For now, we'll create a user from token data
    user = User(
        id=token_data.user_id or "unknown",
        username=token_data.username or "unknown",
        email=token_data.email or "unknown@example.com",
        roles=token_data.roles,
    )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_roles(required_roles: list[str]):
    """Dependency to require specific roles."""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker