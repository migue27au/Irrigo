from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer, Boolean, Numeric, DateTime
from sqlalchemy.sql import func

from db.base import Base

class ActuatorAction(Base):
    __tablename__ = "actuator_action"

    id = Column(BigInteger, primary_key=True)

    system_id = Column(BigInteger, ForeignKey("irrigation_systems.id"))

    actuator_id = Column(BigInteger, ForeignKey("system_actuators.id"))

    intensity = Column(Numeric(5, 2), nullable=False)  # 0-100

    duration_seconds = Column(BigInteger, nullable=False)

    name = Column(String(255))