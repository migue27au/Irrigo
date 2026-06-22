from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from api.deps import (
    get_db,
    get_system_by_api_key,
    get_current_user,
    get_system_with_access,
)

from models.actuator_command import ActuatorCommand
from models.rule_group import RuleGroup
from models.rule_condition import RuleCondition
from models.rule_group_actuator import RuleGroupActuator

from schemas.rule import (
    RuleGetResponse,
    RuleGroupOut,
    RuleConditionOut,
    RuleGroupCreate,
    RuleConditionCreate,
)

router = APIRouter(prefix="/rules", tags=["Rules"])


# =====================================================
# HELPERS
# =====================================================

def resolve_system(command_id, db, system=None):
    command = (
        db.query(ActuatorCommand)
        .filter(ActuatorCommand.id == command_id)
        .first()
    )

    if not command:
        raise HTTPException(404, "Command not found")

    if system and command.system_id != system.id:
        raise HTTPException(403, "Invalid system")

    return command


def build_group_out(group: RuleGroup, db: Session):
    conditions = (
        db.query(RuleCondition)
        .filter(RuleCondition.group_id == group.id)
        .all()
    )

    return RuleGroupOut(
        id=group.id,
        name=group.name,
        description=group.description,
        conditions=[
            RuleConditionOut(
                id=c.id,
                type=c.type,
                sensor_id=c.sensor_id,
                operator=c.operator,
                value=float(c.value) if c.value is not None else None,
                cron=c.cron,
            )
            for c in conditions
        ],
    )


# =====================================================
# ESP32 + WEB - GET RULES (DUAL AUTH)
# =====================================================

@router.get("/{command_id}", response_model=RuleGetResponse)
def get_rules(
    command_id: int,
    db: Session = Depends(get_db),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
    user=Depends(get_current_user),
):
    system = None

    if api_key:
        system = get_system_by_api_key(db=db, api_key=api_key)
    else:
        cmd = db.query(ActuatorCommand).filter(
            ActuatorCommand.id == command_id
        ).first()

        if not cmd:
            raise HTTPException(404, "Command not found")

        system, role = get_system_with_access(
            db=db,
            system_id=cmd.system_id,
            user_id=user.id,
            require_role="viewer",
        )

    command = resolve_system(command_id, db, system)

    if command.trigger_type != "automatic":
        raise HTTPException(404, "Command not found")

    groups = (
        db.query(RuleGroup)
        .join(RuleGroupActuator, RuleGroupActuator.group_id == RuleGroup.id)
        .filter(
            RuleGroup.system_id == system.id,
            RuleGroupActuator.command_id == command.id,
            RuleGroup.enabled == True,
        )
        .all()
    )

    return RuleGetResponse(
        command_id=command.id,
        groups=[build_group_out(g, db) for g in groups],
    )


# =====================================================
# FRONTEND API - GET RULE GROUPS
# =====================================================

@router.get("/{command_id}/rulegroups")
def get_rule_groups(
    command_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    command = db.query(ActuatorCommand).filter_by(id=command_id).first()

    if not command:
        raise HTTPException(404, "Command not found")

    get_system_with_access(
        db=db,
        system_id=command.system_id,
        user_id=user.id,
        require_role="viewer",
    )

    groups = (
        db.query(RuleGroup)
        .join(RuleGroupActuator)
        .filter(RuleGroupActuator.command_id == command.id)
        .all()
    )

    return [build_group_out(g, db) for g in groups]


# =====================================================
# CREATE RULE GROUP (FRONTEND)
# =====================================================

@router.post("/{command_id}/rulegroups")
def create_rule_group(
    command_id: int,
    payload: RuleGroupCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    command = db.query(ActuatorCommand).filter_by(id=command_id).first()

    if not command:
        raise HTTPException(404, "Command not found")

    get_system_with_access(
        db=db,
        system_id=command.system_id,
        user_id=user.id,
        require_role="maintainer",
    )

    group = RuleGroup(
        system_id=command.system_id,
        name=payload.name,
        description=payload.description,
        enabled=True,
    )

    db.add(group)
    db.flush()

    db.add(
        RuleGroupActuator(
            group_id=group.id,
            command_id=command.id,
        )
    )

    db.commit()

    return {"group_id": group.id}


# =====================================================
# UPDATE GROUP
# =====================================================

@router.put("/rulegroups/{group_id}")
def update_group(
    group_id: int,
    payload: RuleGroupCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    group = db.query(RuleGroup).filter_by(id=group_id).first()

    if not group:
        raise HTTPException(404, "Group not found")

    get_system_with_access(
        db=db,
        system_id=group.system_id,
        user_id=user.id,
        require_role="maintainer",
    )

    group.name = payload.name
    group.description = payload.description

    db.commit()

    return {"status": "updated"}


# =====================================================
# DELETE GROUP
# =====================================================

@router.delete("/rulegroups/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    group = db.query(RuleGroup).filter_by(id=group_id).first()

    if not group:
        raise HTTPException(404, "Group not found")

    get_system_with_access(
        db=db,
        system_id=group.system_id,
        user_id=user.id,
        require_role="maintainer",
    )

    db.delete(group)
    db.commit()

    return {"status": "deleted"}


# =====================================================
# ADD CONDITION (NEW STRUCTURE)
# =====================================================

@router.post("/{command_id}/rulegroups/{group_id}/conditions")
def add_condition(
    command_id: int,
    group_id: int,
    payload: RuleConditionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    command = db.query(ActuatorCommand).filter_by(id=command_id).first()

    if not command:
        raise HTTPException(404, "Command not found")

    group = db.query(RuleGroup).filter_by(id=group_id).first()

    if not group:
        raise HTTPException(404, "Group not found")

    if group.system_id != command.system_id:
        raise HTTPException(403, "Invalid group")

    get_system_with_access(
        db=db,
        system_id=command.system_id,
        user_id=user.id,
        require_role="maintainer",
    )

    condition = RuleCondition(
        group_id=group.id,
        type=payload.type,
        sensor_id=payload.sensor_id,
        operator=payload.operator,
        value=payload.value,
        cron=payload.cron,
    )

    db.add(condition)
    db.commit()

    return {"condition_id": condition.id}


# =====================================================
# DELETE CONDITION
# =====================================================

@router.delete("/conditions/{condition_id}")
def delete_condition(
    condition_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    condition = db.query(RuleCondition).filter_by(id=condition_id).first()

    if not condition:
        raise HTTPException(404, "Condition not found")

    get_system_with_access(
        db=db,
        system_id=condition.group.system_id,
        user_id=user.id,
        require_role="maintainer",
    )

    db.delete(condition)
    db.commit()

    return {"status": "deleted"}