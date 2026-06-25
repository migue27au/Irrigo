from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import (
    get_db,
    get_system_by_api_key,
    get_current_user,
    get_system_with_access,
)

from models.system_actuator import SystemActuator
from models.actuator_command import ActuatorCommand

from models.actuator_event import ActuatorEvent

from schemas.actuator import (
    ActuatorGetResponse,
    ActuatorCommandOut,
    ActuatorCommandCreate,
    ActuatorCommandUpdate,
    ActuatorExecutedIn,
    ActuatorOut,
    ActuatorCommandOutBatch,
)

router = APIRouter(prefix="/actuators", tags=["Actuators"])

MANUAL_COMMAND_TIMEOUT_MINUTES = 120


# =====================================================
# ACTUATORS CONFIG (USER WEB)
# =====================================================

@router.post("/")
def create_actuator(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    system, role = get_system_with_access(
        db=db,
        system_id=payload["system_id"],
        user_id=user.id,
        require_role="maintainer",
    )

    channel = payload.get("channel", 0)

    # VALIDATION: channel range
    if channel < 0 or channel >= 4:
        raise HTTPException(
            status_code=400,
            detail="Channel must be between 0 and 3",
        )

    # VALIDATION: unique channel per system
    existing = (
        db.query(SystemActuator)
        .filter(
            SystemActuator.system_id == system.id,
            SystemActuator.channel == channel,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Channel {channel} is already in use",
        )

    actuator = SystemActuator(
        system_id=system.id,
        name=payload["name"],
        channel=channel,
        description=payload.get("description"),
        enabled=False,
        intensity=None,
    )

    db.add(actuator)
    db.commit()
    db.refresh(actuator)

    return actuator

@router.put("/{actuator_id}")
def update_actuator(
    actuator_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    actuator = db.query(SystemActuator).filter(
        SystemActuator.id == actuator_id
    ).first()

    if not actuator:
        raise HTTPException(404, "Actuator not found")

    get_system_with_access(
        db=db,
        system_id=actuator.system_id,
        user_id=user.id,
        require_role="maintainer",
    )

    for k, v in payload.items():
        setattr(actuator, k, v)

    db.commit()
    db.refresh(actuator)

    return actuator


@router.delete("/{actuator_id}")
def delete_actuator(
    actuator_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    actuator = db.query(SystemActuator).filter(
        SystemActuator.id == actuator_id
    ).first()

    if not actuator:
        raise HTTPException(404, "Actuator not found")

    get_system_with_access(
        db=db,
        system_id=actuator.system_id,
        user_id=user.id,
        require_role="maintainer",
    )

    db.delete(actuator)
    db.commit()

    return {"status": "deleted"}


# =====================================================
# ESP32 - GET ACTUATORS
# =====================================================
@router.get("/get", response_model=list[ActuatorOut])
def list_actuators(
    db: Session = Depends(get_db),
    system=Depends(get_system_by_api_key),
):
    return (
        db.query(SystemActuator)
        .filter(SystemActuator.system_id == system.id)
        .order_by(SystemActuator.channel.asc())
        .all()
    )

# =====================================================
# ESP32 - GET COMMANDS
# =====================================================

@router.get("/{actuator_id}/commands", response_model=ActuatorCommandOutBatch)
def get_actuator_commands(
    actuator_id: int,
    db: Session = Depends(get_db),
    system=Depends(get_system_by_api_key),
):
    actuator = (
        db.query(SystemActuator)
        .filter(SystemActuator.id == actuator_id)
        .first()
    )

    if not actuator:
        raise HTTPException(404, "Actuator not found")

    commands = (
        db.query(ActuatorCommand)
        .filter(ActuatorCommand.actuator_id == actuator.id)
        .order_by(ActuatorCommand.id.desc())
        .all()
    )

    return ActuatorCommandOutBatch(
        actuator_id=actuator.id,
        commands=[
            ActuatorCommandOut.model_validate(command)
            for command in commands
        ]
)

@router.post("/commands", response_model=ActuatorCommandOut)
def create_command(
    payload: ActuatorCommandCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    system, role = get_system_with_access(
        db=db,
        system_id=payload.system_id,
        user_id=user.id,
        require_role="maintainer",
    )

    actuator = db.query(SystemActuator).filter(
        SystemActuator.id == payload.actuator_id,
        SystemActuator.system_id == system.id,
    ).first()

    if not actuator:
        raise HTTPException(404, "Actuator not found")

    cmd = ActuatorCommand(
        system_id=system.id,
        actuator_id=actuator.id,
        name=payload.name,
        trigger_type=payload.trigger_type,
        intensity=payload.intensity,
        duration_seconds=payload.duration_seconds,
        executed_count=0,
        enabled=True,
    )

    db.add(cmd)
    db.commit()
    db.refresh(cmd)

    return cmd

# =====================================================
# COMMANDS (WEB USER)
# =====================================================
@router.get("/{actuator_id}/commandsfromweb", response_model=list[ActuatorCommandOut])
def get_actuator_commands(
    actuator_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    actuator = (
        db.query(SystemActuator)
        .filter(SystemActuator.id == actuator_id)
        .first()
    )

    if not actuator:
        raise HTTPException(404, "Actuator not found")

    get_system_with_access(
        db=db,
        system_id=actuator.system_id,
        user_id=user.id,
        require_role="viewer",
    )

    commands = (
        db.query(ActuatorCommand)
        .filter(ActuatorCommand.actuator_id == actuator.id)
        .order_by(ActuatorCommand.id.desc())
        .all()
    )

    return commands

# =====================================================
# UPDATE COMMAND (WEB USER)
# =====================================================
@router.put("/commands/{command_id}", response_model=ActuatorCommandOut)
def update_command(command_id: int, payload: ActuatorCommandUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    cmd = db.query(ActuatorCommand).filter(ActuatorCommand.id == command_id).first()

    if not cmd:
        raise HTTPException(404, "Command not found")

    get_system_with_access(
        db=db,
        system_id=cmd.system_id,
        user_id=user.id,
        require_role="maintainer",
    )

    for k, v in payload.dict(exclude_unset=True).items():
        setattr(cmd, k, v)

    db.commit()
    db.refresh(cmd)

    return cmd

# =====================================================
# DELETE COMMAND (WEB USER)
# =====================================================
@router.delete("/commands/{command_id}")
def delete_command(command_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    cmd = db.query(ActuatorCommand).filter(ActuatorCommand.id == command_id).first()

    if not cmd:
        raise HTTPException(404, "Command not found")

    get_system_with_access(
        db=db,
        system_id=cmd.system_id,
        user_id=user.id,
        require_role="maintainer",
    )

    db.delete(cmd)
    db.commit()

    return {"status": "deleted"}


# =====================================================
# ESP32 CONFIRMATION
# =====================================================
@router.post("/executed")
def actuator_executed(payload: ActuatorExecutedIn, db: Session = Depends(get_db), system=Depends(get_system_by_api_key)):

    cmd = db.query(ActuatorCommand).filter(
        ActuatorCommand.id == payload.command_id,
        ActuatorCommand.system_id == system.id,
        ActuatorCommand.enabled == True,
    ).first()

    if not cmd:
        raise HTTPException(404, "Command not found")

    cmd.executed_count += 1
    cmd.last_executed_at = datetime.utcnow()

    db.add(
        ActuatorEvent(
            actuator_id=payload.actuator_id,
            command_id=payload.command_id,
            intensity=payload.intensity,
            duration_seconds=payload.duration_seconds,
            trigger_type=payload.trigger_type,
            recorded_at=datetime.utcnow(),
        )
    )

    db.commit()

    return {"status": "ok"}