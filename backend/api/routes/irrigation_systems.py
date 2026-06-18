from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import secrets
import hashlib

from backend.api.deps import get_db, get_current_user, get_system_with_access

from backend.models.irrigation_system import IrrigationSystem
from backend.models.system_user import SystemUser

from backend.schemas.irrigation_system import (
    IrrigationSystemCreate,
    IrrigationSystemUpdate,
    IrrigationSystemOut,
    ShareSystemRequest,
)

router = APIRouter(prefix="/irrigation-systems", tags=["Irrigation Systems"])

# -----------------------------------------------------
# CREATE SYSTEM
# -----------------------------------------------------
@router.post("/", response_model=IrrigationSystemOut)
def create_system(
    data: IrrigationSystemCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    raw_api_key = secrets.token_hex(32)
    api_key_hash = hashlib.sha256(raw_api_key.encode()).hexdigest()

    system = IrrigationSystem(
        alias=data.alias,
        description=data.description,
        api_key_hash=api_key_hash,
    )

    db.add(system)
    db.flush()

    db.add(SystemUser(
        system_id=system.id,
        user_id=user.id,
        role="owner"
    ))

    db.commit()
    db.refresh(system)

    # solo se devuelve una vez
    system.api_key_plain = raw_api_key

    return system


# -----------------------------------------------------
# GET ALL SYSTEMS (owner + shared)
# -----------------------------------------------------
@router.get("/", response_model=list[IrrigationSystemOut])
def get_my_systems(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    systems = db.query(IrrigationSystem).join(
        SystemUser,
        SystemUser.system_id == IrrigationSystem.id
    ).filter(
        SystemUser.user_id == user.id
    ).all()

    return systems


# -----------------------------------------------------
# GET SYSTEM BY ID
# -----------------------------------------------------
@router.get("/{system_id}", response_model=IrrigationSystemOut)
def get_system(
    system_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    system, role = get_system_with_access(
        db=db,
        system_id=system_id,
        user_id=user.id,
        require_role="viewer"
    )

    return system


# -----------------------------------------------------
# UPDATE SYSTEM (owner + maintainer)
# -----------------------------------------------------
@router.put("/{system_id}", response_model=IrrigationSystemOut)
def update_system(
    system_id: int,
    data: IrrigationSystemUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    system, role = get_system_with_access(
        db=db,
        system_id=system_id,
        user_id=user.id,
        require_role="maintainer"
    )

    if data.alias is not None:
        system.alias = data.alias

    if data.description is not None:
        system.description = data.description

    if data.firmware_version is not None:
        system.firmware_version = data.firmware_version

    db.commit()
    db.refresh(system)

    return system


# -----------------------------------------------------
# DELETE SYSTEM (owner only)
# -----------------------------------------------------
@router.delete("/{system_id}")
def delete_system(
    system_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    system, role = get_system_with_access(
        db=db,
        system_id=system_id,
        user_id=user.id,
        require_role="owner"
    )

    db.delete(system)
    db.commit()

    return {"status": "deleted"}


@router.post("/{system_id}/share")
def share_system(
    system_id: int,
    payload: ShareSystemRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    system, user_role = get_system_with_access(
        db=db,
        system_id=system_id,
        user_id=user.id,
        require_role="owner"
    )

    if payload.user_id == user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify your own role"
        )

    if payload.role not in ["viewer", "maintainer"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    relation = db.query(SystemUser).filter_by(
        system_id=system_id,
        user_id=payload.user_id
    ).first()

    if relation:
        relation.role = payload.role
    else:
        db.add(
            SystemUser(
                system_id=system_id,
                user_id=payload.user_id,
                role=payload.role
            )
        )

    db.commit()

    return {
        "status": "ok",
        "role": payload.role
    }