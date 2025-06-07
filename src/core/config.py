from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Server Settings
    PORT: int = os.getenv("PORT") or 8000

    # MongoDB Settings
    MONGO_SRV_URI: str = os.getenv("MONGO_SRV_URI") or "mongodb+srv://shlsadibayk:<db_password>@cluster0.n6n5fri.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    DATABASE_NAME: str = os.getenv("DATABASE_NAME") or "mydatabase"
    USER_COLLECTION: str = os.getenv("USER_COLLECTION") or "users"
    MONGO_DETAILS: Optional[str] = None

    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY") or "your-secret-key"
    ALGORITHM: str = os.getenv("ALGORITHM") or "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or 100000

    # SATUSEHAT Client Settings
    AUTH_URL: Optional[str] = os.getenv("AUTH_URL")
    BASE_URL: Optional[str] = os.getenv("BASE_URL")
    CLIENT_ID: Optional[str] = os.getenv("CLIENT_ID")
    CLIENT_SECRET: Optional[str] = os.getenv("CLIENT_SECRET")
    ORGANIZATION_ID: Optional[str] = os.getenv("ORGANIZATION_ID")
    PRACTITIONER_ID: Optional[str] = os.getenv("PRACTITIONER_ID")


    class Config:
        env_file = ".env"

settings = Settings() 