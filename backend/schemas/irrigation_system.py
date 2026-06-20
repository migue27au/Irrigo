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
    owner_username: str | None = None
    role: str | None = None


    class Config:
        from_attributes = True

