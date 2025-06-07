from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Any
from datetime import datetime
from bson import ObjectId # Import ObjectId

# Helper to convert ObjectId to str for Pydantic models
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, validation_info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class PatientData(BaseModel):
    nik: str = Field(..., description="Nomor Induk Kependudukan", example="3210123456780001")
    name: str = Field(..., description="Nama lengkap pasien", example="Rina Sari")
    birthdate: str = Field(..., description="Tanggal lahir YYYY-MM-DD", example="1998-10-21")
    gender: str = Field(..., description="Jenis kelamin (male/female)", example="female")
    telecom: Optional[str] = Field(None, description="Nomor telepon/HP")
    address: Optional[str] = Field(None, description="Alamat lengkap")

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="strongpassword")
    patient_details: PatientData
    participant_id: str = Field(default=None, example="participant_xyz")
    response_id: str = Field(default=None, example="response_abc")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., example="strongpassword")

class UserInDBBase(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    patient_details: PatientData
    participant_id: Optional[str] = None
    response_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
        populate_by_name = True 
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            PyObjectId: str, # Ensure ObjectId is serialized as str
            ObjectId: str # Also handle raw ObjectId if it appears
        }

class UserInDB(UserInDBBase):
    hashed_password: str

class UserPublic(UserBase):
    patient_details: PatientData
    participant_id: Optional[str] = None
    response_id: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            ObjectId: str
        }

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None 