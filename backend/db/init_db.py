from backend.db.base import Base
from backend.db.db import engine

#  TODO: importar todos los modelos para que SQLAlchemy los registre
from backend.models.user import User
# luego añadirás:
# from backend.models.system import IrrigationSystem
# from backend.models.sensor import Sensor
# etc.


async def init_db():
    """
    Creates all database tables based on SQLAlchemy models.
    Only use in development or initial setup (NOT production).
    """

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)