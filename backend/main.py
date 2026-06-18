from fastapi import FastAPI

from backend.api.routes.users import router as users_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.irrigation_systems import router as irrigation_systems_router

from backend.db.init_db import init_db

app = FastAPI(title="IoT Irrigation System")

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(irrigation_systems_router)


@app.on_event("startup")
def startup():
    init_db()
    print("Starting IoT Irrigation backend...")