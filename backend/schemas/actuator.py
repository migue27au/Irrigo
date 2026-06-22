from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# =====================================================
# ACTUATOR COMMAND OUT (IrrigationSystem + BACKEND VIEW)
# =====================================================
class ActuatorCommandOut(BaseModel):
    id: int
    actuator_id: int
    name: Optional[str] = None

    trigger_type: str  # manual | automatic

    intensity: Optional[float] = None
    duration_seconds: Optional[int] = None

    executed_count: int

    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# IrrigationSystem GET RESPONSE
# =====================================================
class ActuatorGetResponse(BaseModel):
    commands: List[ActuatorCommandOut]


# =====================================================
# EXECUTION CONFIRMATION (IrrigationSystem → BACKEND)
# =====================================================
class ActuatorExecutedIn(BaseModel):
    command_id: int
    actuator_id: int

    intensity: Optional[float] = None
    duration_seconds: Optional[int] = None
    trigger_type: str


# =====================================================
# CREATE / UPDATE COMMAND (BACKEND USER)
# =====================================================
class ActuatorCommandCreate(BaseModel):
    system_id: int
    actuator_id: int
    name: Optional[str] = None

    trigger_type: str  # manual | automatic

    intensity: Optional[float] = None
    duration_seconds: Optional[int] = None


class ActuatorCommandUpdate(BaseModel):
    name: Optional[str] = None

    intensity: Optional[float] = None
    duration_seconds: Optional[int] = None

    disabled: Optional[bool] = None
    disabled_reason: Optional[str] = None


# =====================================================
# BACKEND LIST RESPONSE
# =====================================================
class ActuatorCommandListResponse(BaseModel):
    commands: List[ActuatorCommandOut]

class ActuatorOut(BaseModel):
    id: int
    system_id: int

    name: str
    channel: int

    description: Optional[str] = None

    is_on: bool
    intensity: Optional[float] = None

    last_changed_at: Optional[datetime] = None
    last_changed_by: Optional[int] = None

    class Config:
        from_attributes = True