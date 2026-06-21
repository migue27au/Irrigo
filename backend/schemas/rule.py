from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# =====================================================
# CONDITION (OUTPUT - IrrigationSystem)
# =====================================================
class RuleConditionOut(BaseModel):
    id: int

    type: str
    sensor_id: Optional[int] = None

    operator: Optional[str] = None
    value: Optional[float] = None

    cron: Optional[str] = None

    class Config:
        from_attributes = True


# =====================================================
# RULE GROUP (AND LOGIC)
# =====================================================
class RuleGroupOut(BaseModel):
    id: int
    name: Optional[str] = None

    conditions: List[RuleConditionOut]

    class Config:
        from_attributes = True


# =====================================================
# IrrigationSystem RESPONSE (OR GROUPS)
# =====================================================
class RuleGetResponse(BaseModel):
    command_id: int
    groups: List[RuleGroupOut]


# =====================================================
# BACKEND CREATE CONDITION
# =====================================================
class RuleConditionCreate(BaseModel):
    type: str
    sensor_id: Optional[int] = None

    operator: Optional[str] = None
    value: Optional[float] = None

    cron: Optional[str] = None


# =====================================================
# BACKEND CREATE GROUP
# =====================================================
class RuleGroupCreate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: List[RuleConditionCreate]


# =====================================================
# BACKEND UPDATE GROUP
# =====================================================
class RuleGroupUpdate(BaseModel):
    name: Optional[str] = None


# =====================================================
# BACKEND RESPONSE (FULL RULE TREE)
# =====================================================
class RuleGroupDetailOut(BaseModel):
    id: int
    name: Optional[str] = None

    conditions: List[RuleConditionOut]

    class Config:
        from_attributes = True


class RuleFullResponse(BaseModel):
    command_id: int
    groups: List[RuleGroupDetailOut]


# =====================================================
# LINK RULE ↔ COMMAND (IMPORTANT FOR YOUR DESIGN)
# =====================================================
class RuleGroupActuatorOut(BaseModel):
    id: int
    rule_group_id: int
    actuator_command_id: int

    class Config:
        from_attributes = True