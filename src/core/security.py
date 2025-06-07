from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pymongo.database import Database

from src.core.config import settings
from src.models.user_models import TokenData, UserPublic
from src.services import user_service
from src.db import get_database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Database = Depends(get_database)
) -> UserPublic:
    print(f"SECURITY: Received token: {token}") # DEBUG
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"SECURITY: Decoded payload: {payload}") # DEBUG
        email: Optional[str] = payload.get("sub")
        if email is None:
            print("SECURITY: Email ('sub') not in token payload") # DEBUG
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        print(f"SECURITY: JWTError during token decoding: {str(e)}") # DEBUG
        raise credentials_exception
    
    user = user_service.get_user_by_email(db, email=token_data.email)
    if user is None:
        print(f"SECURITY: User with email {token_data.email} not found in DB") # DEBUG
        raise credentials_exception
    print(f"SECURITY: User {token_data.email} found. Token validated.") # DEBUG
    return UserPublic(**user.model_dump()) 