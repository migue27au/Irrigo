from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.users import router as users_router
from api.routes.auth import router as auth_router
from api.routes.irrigation_systems import router as irrigation_systems_router
from api.routes.sensors import router as sensors_router
from api.routes.actuators import router as actuators_router
from api.routes.rules import router as rules_router


from db.init_db import init_db

app = FastAPI(title="IoT Irrigation System")

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(irrigation_systems_router)
app.include_router(sensors_router)
app.include_router(actuators_router)
app.include_router(rules_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    print("Starting IoT Irrigation ..")