from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str | None
    role: str

    class Config:
        from_attributes = True


class UserDetailedResponse(BaseModel):
    id: int
    email: EmailStr
    name: str | None
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True