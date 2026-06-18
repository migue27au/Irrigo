from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.user import User
from backend.schemas.auth import LoginRequest, TokenResponse
from backend.core.security import verify_password, create_access_token
from backend.api.deps import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


# LOGIN
@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

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
async def logout():
    return {"message": "Logged out (client should delete token)"}