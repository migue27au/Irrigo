from fastapi import FastAPI

from app.api.routes.users import router as users_router
from app.api.routes.auth import router as auth_router

from app.db.init_db import init_db
from app.db.seed import create_admin_user
from app.db.db import SessionLocal

app = FastAPI(title="IoT Irrigation System")

app.include_router(users_router)
app.include_router(auth_router)

@app.on_event("startup")
async def startup():
    # crear tablas
    await init_db()

    # crear admin
    async with SessionLocal() as db:
        await create_admin_user(db)

