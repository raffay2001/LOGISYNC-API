from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    rider = "rider"
    admin = "admin"

class UserSchema(BaseModel):
    fullname: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)
    phone: str = Field(...)
    role: UserRole = Field(...)
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "fullname": "Abdul Raffay",
                "email": "raffay@gmail.com",
                "password": "Abc@123",
                "phone": "03154425478",
                "role": "rider"
            }
        }

class GPSPingSchema(BaseModel):
    journey_id: str = Field(...)
    latitude: float = Field(...)
    longitude: float = Field(...)

class EndJourneySchema(BaseModel):
    journey_id: str = Field(...)

class LoginSchema(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

def ResponseModel(data, message):
    return {
        "data": [data],
        "code": 200,
        "message": message,
    }

def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}

class Journey(BaseModel):
    rider_id: str = Field(...)
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)

    class Config:
        schema_extra = {
            "example": {
                "rider_id": "60d5f77a2f8fb814c8fdd207",
                "createdAt": "2023-06-01T00:00:00.000Z",
                "updatedAt": "2023-06-01T00:00:00.000Z",
            }
        }

class RiderJourneysResponse(BaseModel):
    fullName: str
    riderId: str
    journeyNo: int
    journeyId: str