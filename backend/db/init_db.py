from backend.db.base import Base
from backend.db.db import engine

#  TODO: importar todos los modelos para que SQLAlchemy los registre
from backend.models.user import User
# luego añadirás:
# from backend.models.system import IrrigationSystem
# from backend.models.sensor import Sensor
# etc.


def init_db():
    Base.metadata.create_all(bind=engine)