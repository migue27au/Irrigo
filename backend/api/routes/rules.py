from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import (
    get_db,
    get_system_by_api_key,
    get_current_user,
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
# ESP32 - GET RULES FOR COMMAND (ONLY AUTOMATIC)
# =====================================================

@router.get("/{command_id}", response_model=RuleGetResponse)
def get_rules(
    command_id: int,
    db: Session = Depends(get_db),
    system=Depends(get_system_by_api_key),
):

    command = (
        db.query(ActuatorCommand)
        .filter(
            ActuatorCommand.id == command_id,
            ActuatorCommand.system_id == system.id,
            ActuatorCommand.trigger_type == "automatic",
        )
        .first()
    )

    if not command:
        raise HTTPException(status_code=404, detail="Command not found")

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

    result = []

    for group in groups:
        conditions = (
            db.query(RuleCondition)
            .filter(RuleCondition.group_id == group.id)
            .all()
        )

        result.append(
            RuleGroupOut(
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
                ]
            )
        )

    return RuleGetResponse(
        command_id=command.id,
        groups=result
    )


# =====================================================
# CREATE RULE GROUP
# =====================================================

@router.post("/group/{command_id}")
def create_rule_group(
    command_id: int,
    payload: RuleGroupCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    command = (
        db.query(ActuatorCommand)
        .filter(ActuatorCommand.id == command_id)
        .first()
    )

    if not command:
        raise HTTPException(status_code=404, detail="Command not found")

    system_id = command.system_id

    group = RuleGroup(
        system_id=system_id,
        name=payload.name,
        description=payload.description,
        enabled=True,
    )

    db.add(group)
    db.flush()

    db.add(
        RuleGroupActuator(
            group_id=group.id,
            command_id=command.id
        )
    )

    db.commit()

    return {
        "group_id": group.id,
        "status": "created"
    }


# =====================================================
# ADD CONDITION
# =====================================================

@router.post("/group/{group_id}/condition")
def add_condition(
    group_id: int,
    payload: RuleConditionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    group = db.query(RuleGroup).filter_by(id=group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    condition = RuleCondition(
        group_id=group.id,
        type=payload.type,
        sensor_id=payload.sensor_id,
        operator=payload.operator,
        value=payload.value,
        cron=payload.cron
    )

    db.add(condition)
    db.commit()

    return {
        "condition_id": condition.id,
        "status": "created"
    }


# =====================================================
# UPDATE GROUP
# =====================================================

@router.put("/group/{group_id}")
def update_group(
    group_id: int,
    payload: RuleGroupCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    group = db.query(RuleGroup).filter_by(id=group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group.name = payload.name
    group.description = payload.description

    db.commit()

    return {"status": "updated"}


# =====================================================
# DELETE GROUP
# =====================================================

@router.delete("/group/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    group = db.query(RuleGroup).filter_by(id=group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    db.delete(group)
    db.commit()

    return {"status": "deleted"}


# =====================================================
# DELETE CONDITION
# =====================================================

@router.delete("/condition/{condition_id}")
def delete_condition(
    condition_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    condition = db.query(RuleCondition).filter_by(id=condition_id).first()

    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")

    db.delete(condition)
    db.commit()

    return {"status": "deleted"}