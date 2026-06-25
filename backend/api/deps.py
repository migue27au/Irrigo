from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.security import decode_access_token
from db.db import SessionLocal

from models.user import User
from models.system import System
from models.system_user import SystemUser
from models.system_sensor import Sensor
from models.system_actuator import SystemActuator
from models.rule_group import RuleGroup

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload["user_id"]

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_current_admin(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    return current_user


def get_system_by_api_key(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    system = db.query(System).filter(
        System.api_key == x_api_key
    ).first()

    if not system:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return system


ROLE_HIERARCHY = {
    "viewer": 1,
    "maintainer": 2,
    "owner": 3,
}


def _has_required_role(user_role: str, required_role: str) -> bool:
    return ROLE_HIERARCHY[user_role] >= ROLE_HIERARCHY[required_role]


def get_system_with_access(
    db: Session,
    system_id: int,
    user_id: int,
    require_role: str | None = None,
):
    """
    Returns (system, user_role)

    require_role:
        - None → any access
        - "viewer"
        - "maintainer"
        - "owner"

    Roles are hierarchical:
        owner > maintainer > viewer
    """

    system = db.query(System).filter(
        System.id == system_id
    ).first()

    if not system:
        raise HTTPException(
            status_code=404,
            detail="System not found"
        )

    relation = db.query(SystemUser).filter_by(
        system_id=system_id,
        user_id=user_id
    ).first()

    if not relation:
        raise HTTPException(
            status_code=403,
            detail="No access to system"
        )

    user_role = relation.role

    if require_role:
        if not _has_required_role(user_role, require_role):
            raise HTTPException(
                status_code=403,
                detail=f"Requires {require_role} role"
            )

    return system, user_role


def get_sensor_with_access(
    db: Session,
    sensor_id: int,
    user_id: int,
    require_role: str | None = None,
):
    """
    Returns (sensor, user_role)

    require_role:
        - None → any access
        - "viewer"
        - "maintainer"
        - "owner"

    Roles are hierarchical:
        owner > maintainer > viewer
    """

    sensor = db.query(Sensor).filter(
        Sensor.id == sensor_id
    ).first()

    if not sensor:
        raise HTTPException(
            status_code=404,
            detail="Sensor not found"
        )

    relation = db.query(SystemUser).filter_by(
        system_id=sensor.system_id,
        user_id=user_id
    ).first()

    if not relation:
        raise HTTPException(
            status_code=403,
            detail="No access to sensor"
        )

    user_role = relation.role

    if require_role:
        if not _has_required_role(user_role, require_role):
            raise HTTPException(
                status_code=403,
                detail=f"Requires {require_role} role"
            )

    return sensor, user_role


def get_actuator_with_access(
    db: Session,
    actuator_id: int,
    user_id: int,
    require_role: str | None = None,
):
    actuator = (
        db.query(SystemActuator)
        .filter(SystemActuator.id == actuator_id)
        .first()
    )

    if not actuator:
        raise HTTPException(
            status_code=404,
            detail="Actuator not found"
        )

    relation = db.query(SystemUser).filter_by(
        system_id=actuator.system_id,
        user_id=user_id
    ).first()

    if not relation:
        raise HTTPException(
            status_code=403,
            detail="No access to actuator"
        )

    role = relation.role

    if require_role:
        if not _has_required_role(role, require_role):
            raise HTTPException(
                status_code=403,
                detail=f"Requires {require_role} role"
            )

    return actuator, role


def get_rule_group_with_access(
    db: Session,
    group_id: int,
    user_id: int,
    require_role: str | None = None,
):
    group = (
        db.query(RuleGroup)
        .filter(RuleGroup.id == group_id)
        .first()
    )

    if not group:
        raise HTTPException(
            status_code=404,
            detail="Rule group not found"
        )

    relation = db.query(SystemUser).filter_by(
        system_id=group.system_id,
        user_id=user_id
    ).first()

    if not relation:
        raise HTTPException(
            status_code=403,
            detail="No access to rule group"
        )

    role = relation.role

    if require_role:
        if not _has_required_role(role, require_role):
            raise HTTPException(
                status_code=403,
                detail=f"Requires {require_role} role"
            )

    return group, role