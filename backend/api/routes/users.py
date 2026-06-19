from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.user import User
from schemas.user import UserCreate, UserResponse, UserDetailedResponse
from core.security import hash_password
from api.deps import get_db, get_current_admin, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


# LIST ALL USERS
@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).all()
    return users


# GET USER BY ID
@router.get("/{user_id}", response_model=UserDetailedResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# CREATE USER
@router.post("/", response_model=UserDetailedResponse)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    existing = db.query(User).filter(User.username == payload.username).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        name=payload.name
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# DELETE USER
@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db.delete(user)
    db.commit()