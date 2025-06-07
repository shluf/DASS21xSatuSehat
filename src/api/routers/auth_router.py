from fastapi import APIRouter, Depends, status
from pymongo.database import Database

from src.core.security import get_current_user
from src.models.user_models import UserCreate, UserLogin, UserPublic, Token
from src.api.controllers import auth_controller
from src.db import get_database
from src.core.security import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user_route(
    payload: UserCreate, 
    db: Database = Depends(get_database)
):
    return auth_controller.register_user_controller(payload=payload, db=db)

@router.post("/login", response_model=Token)
def login_user_route(
    payload: UserLogin,
    db: Database = Depends(get_database)
):
    return auth_controller.login_user_controller(payload=payload, db=db) 

@router.get("/user", response_model=UserPublic)
def get_user_details_route(
    current_user: UserPublic = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    return auth_controller.get_user_details_controller(current_user=current_user, db=db)


