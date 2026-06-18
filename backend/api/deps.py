from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.core.security import decode_access_token
from backend.db.db import SessionLocal

from backend.models.user import User
from backend.models.irrigation_system import IrrigationSystem
from backend.models.system_user import SystemUser

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
    apikey: str = Header(..., alias="APIKEY"),
    db: Session = Depends(get_db),
) -> IrrigationSystem:

    # hash de la key recibida
    api_key_hash = hashlib.sha256(apikey.encode()).hexdigest()

    system = db.query(IrrigationSystem).filter(
        IrrigationSystem.api_key_hash == api_key_hash
    ).first()

    if not system:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

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

    system = db.query(IrrigationSystem).filter(
        IrrigationSystem.id == system_id
    ).first()

    if not system:
        raise HTTPException(status_code=404, detail="System not found")

    relation = db.query(SystemUser).filter_by(
        system_id=system_id,
        user_id=user_id
    ).first()

    if not relation:
        raise HTTPException(status_code=403, detail="No access to system")

    user_role = relation.role

    if require_role:
        if not _has_required_role(user_role, require_role):
            raise HTTPException(
                status_code=403,
                detail=f"Requires {require_role} role"
            )

    return system, user_role