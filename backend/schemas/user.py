from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    name: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    name: str | None
    role: str

    class Config:
        from_attributes = True


class UserDetailedResponse(BaseModel):
    id: int
    username: str
    name: str | None
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True