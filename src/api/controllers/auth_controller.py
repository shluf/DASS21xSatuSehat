from fastapi import Depends, HTTPException, status
from pymongo.database import Database
from datetime import timedelta

from src.services import user_service
from src.db import get_database
from src.models.user_models import UserCreate, UserLogin, UserPublic, Token
from src.core.security import create_access_token
from src.core.config import settings

def register_user_controller(
    payload: UserCreate, 
    db: Database = Depends(get_database)
) -> UserPublic:
    try:
        user = user_service.create_user(db=db, user_data=payload)
        return user
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Registration Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration."
        )

def login_user_controller(
    payload: UserLogin,
    db: Database = Depends(get_database)
) -> Token:
    user = user_service.authenticate_user(
        db=db, 
        email=payload.email, 
        password=payload.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer") 

def get_user_details_controller(
    current_user: UserPublic, 
    db: Database
) -> UserPublic:
    return current_user 