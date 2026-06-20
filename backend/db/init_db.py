import time, traceback
from sqlalchemy import text

from db.base import Base
from db.db import engine

from models.user import User
from models.irrigation_system import IrrigationSystem
from models.system_user import SystemUser
from models.system_sensor import Sensor
from models.sensor_reading import SensorReading


def wait_for_db():
    for i in range(30):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("Database ready")
                return

        except Exception as e:
            print(f"Waiting for database... ({i+1}/30)")
            print(traceback.format_exc())
            time.sleep(2)

    raise Exception("Database not available")


def init_db():
    wait_for_db()
    Base.metadata.create_all(bind=engine)