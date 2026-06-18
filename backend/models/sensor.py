from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from backend.db.base import Base


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(BigInteger, primary_key=True, index=True)

    system_id = Column(BigInteger, ForeignKey("irrigation_systems.id", ondelete="CASCADE"), nullable=False)

    sensor_key = Column(String(100), nullable=False)

    name = Column(String(255))
    unit = Column(String(20))
    sensor_type = Column(String(50))

    enabled = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("system_id", "sensor_key", name="uq_sensor_key_system"),
    )