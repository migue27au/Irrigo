from pydantic import BaseModel
from datetime import datetime


class SensorCreate(BaseModel):
    sensor_key: str
    name: str | None = None
    unit: str | None = None
    sensor_type: str | None = None

class SensorUpdate(BaseModel):
    sensor_key: str | None = None
    name: str | None = None
    unit: str | None = None
    sensor_type: str | None = None

class SensorBatchCreate(BaseModel):
    sensors: list[SensorCreate]



class SensorOut(BaseModel):
    id: int
    system_id: int

    sensor_key: str

    name: str | None
    unit: str | None
    sensor_type: str | None

    enabled: bool

    created_at: datetime

    class Config:
        from_attributes = True