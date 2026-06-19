from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.user import User
from schemas.auth import LoginRequest, TokenResponse
from core.security import verify_password, create_access_token
from api.deps import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


# LOGIN
@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == payload.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"user_id": user.id, "role": user.role}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# LOGOUT (stateless JWT)
@router.post("/logout")
def logout():
    return {"message": "Logged out (client should delete token)"}