from fastapi import HTTPException, status
from pymongo.database import Database
from datetime import datetime

from src.models.user_models import UserCreate, UserInDB, UserPublic
from src.core.hashing import get_password_hash, verify_password
from src.core.config import settings

def get_user_by_email(db: Database, email: str) -> UserInDB | None:
    user_doc = db[settings.USER_COLLECTION].find_one({"email": email})
    if user_doc:
        return UserInDB(**user_doc)
    return None

def create_user(db: Database, user_data: UserCreate) -> UserPublic:
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    
    user_db_data = user_data.model_dump(exclude={"password"})
    user_db_data["hashed_password"] = hashed_password
    user_db_data["created_at"] = datetime.utcnow()
    user_db_data["updated_at"] = datetime.utcnow()
    
    user_db_data["patient_details"] = user_data.patient_details.model_dump()

    result = db[settings.USER_COLLECTION].insert_one(user_db_data)
    
    created_user_doc = db[settings.USER_COLLECTION].find_one({"_id": result.inserted_id})
    if not created_user_doc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user."
        )
    return UserPublic(**created_user_doc)

def authenticate_user(db: Database, email: str, password: str) -> UserPublic | None:
    user = get_user_by_email(db, email)
    if not user:
        return None 
    
    if not verify_password(password, user.hashed_password):
        return None 
        
    return UserPublic(**user.model_dump(exclude={"hashed_password"})) 