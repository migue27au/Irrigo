from pydantic import BaseModel
from datetime import datetime


class IrrigationSystemBase(BaseModel):
    alias: str
    description: str | None = None


class IrrigationSystemCreate(IrrigationSystemBase):
    pass


class IrrigationSystemUpdate(BaseModel):
    alias: str | None = None
    description: str | None = None
    firmware_version: str | None = None


class IrrigationSystemOut(IrrigationSystemBase):
    id: int
    firmware_version: str | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ShareSystemRequest(BaseModel):
    user_id: int
    role: str = "viewer"