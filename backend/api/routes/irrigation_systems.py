from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import secrets
import hashlib

from api.deps import get_db, get_current_user, get_system_with_access

from models.irrigation_system import IrrigationSystem
from models.system_user import SystemUser
from models.user import User

from schemas.irrigation_system import (
    IrrigationSystemCreate,
    IrrigationSystemUpdate,
    IrrigationSystemOut,
)

from schemas.system_user import (
    ShareSystemRequest,
    SharedUserOut
)

router = APIRouter(prefix="/irrigation-systems", tags=["Irrigation Systems"])

# -----------------------------------------------------
# CREATE SYSTEM
# -----------------------------------------------------
@router.post("/", response_model=IrrigationSystemOut)
def create_system(
    data: IrrigationSystemCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    raw_api_key = secrets.token_hex(32)

    system = IrrigationSystem(
        alias=data.alias,
        description=data.description,
        api_key=raw_api_key,
    )

    db.add(system)
    db.flush()

    db.add(
        SystemUser(
            system_id=system.id,
            user_id=user.id,
            role="owner",
        )
    )

    db.commit()
    db.refresh(system)

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
    user=Depends(get_current_user),
):
    system, role = get_system_with_access(
        db=db,
        system_id=system_id,
        user_id=user.id,
        require_role="viewer"
    )

    owner_relation = db.query(SystemUser).filter(
        SystemUser.system_id == system_id,
        SystemUser.role == "owner"
    ).first()

    owner_username = None

    if owner_relation:
        owner_username = db.query(User.username).filter(
            User.id == owner_relation.user_id
        ).scalar()

    system.owner_username = owner_username

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


# -----------------------------------------------------
# GET APIKEY (owner only)
# -----------------------------------------------------
@router.get("/{system_id}/apikey")
def get_api_key(
    system_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    system, role = get_system_with_access(
        db=db,
        system_id=system_id,
        user_id=user.id,
        require_role="owner",
    )

    return {
        "api_key": system.api_key
    }

# -----------------------------------------------------
# REGENERATE APIKEY (owner only)
# -----------------------------------------------------
@router.post("/{system_id}/apikey/regenerate")
def regenerate_api_key(
    system_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    system, role = get_system_with_access(
        db=db,
        system_id=system_id,
        user_id=user.id,
        require_role="owner",
    )

    new_api_key = secrets.token_hex(32)

    system.api_key = new_api_key

    db.commit()
    db.refresh(system)

    return {
        "api_key": new_api_key
    }


# -----------------------------------------------------
# SHARE SYSTEM (owner only)
# -----------------------------------------------------
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

    target_user = db.query(User).filter(
        User.username == payload.username
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if target_user.id == user.id:
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
        user_id=target_user.id
    ).first()

    if relation:
        relation.role = payload.role
    else:
        db.add(
            SystemUser(
                system_id=system_id,
                user_id=target_user.id,
                role=payload.role
            )
        )

    db.commit()

    return {
        "status": "ok",
        "username": target_user.username,
        "role": payload.role
    }

# -----------------------------------------------------
# GET USERS SHARED SYSTEM (maintainer only)
# -----------------------------------------------------
@router.get("/{system_id}/shared-users", response_model=list[SharedUserOut])
def get_shared_users(
    system_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    system, role = get_system_with_access(
        db=db,
        system_id=system_id,
        user_id=user.id,
        require_role="maintainer"
    )

    relations = (
        db.query(SystemUser, User)
        .join(User, User.id == SystemUser.user_id)
        .filter(SystemUser.system_id == system_id)
        .all()
    )

    return [
        SharedUserOut(
            id=rel.id,
            user_id=u.id,
            username=u.username,
            name=u.name,
            role=rel.role
        )
        for rel, u in relations
    ]

# -----------------------------------------------------
# DELETE USERS SHARED SYSTEM (owner only)
# -----------------------------------------------------
@router.delete("/{system_id}/share/{user_id}")
def unshare_user_from_system(
    system_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    system, role = get_system_with_access(
        db=db,
        system_id=system_id,
        user_id=user.id,
        require_role="owner"
    )

    relation = db.query(SystemUser).filter_by(
        system_id=system_id,
        user_id=user_id
    ).first()

    if not relation:
        raise HTTPException(
            status_code=404,
            detail="User is not shared with this system"
        )
    # No permitir eliminarse a uno mismo de los share
    if relation.user_id == user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove yourself from system"
        )

    # no permitir quitar al owner
    if relation.role == "owner":
        raise HTTPException(
            status_code=400,
            detail="Cannot remove owner from system"
        )

    db.delete(relation)
    db.commit()

    return {"status": "removed"}