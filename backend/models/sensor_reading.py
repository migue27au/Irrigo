from sqlalchemy import Column, BigInteger, Numeric, DateTime, ForeignKey, Index

from backend.db.base import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(BigInteger, primary_key=True, index=True)

    sensor_id = Column(BigInteger, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False)

    value = Column(Numeric(12, 4), nullable=False)

    recorded_at = Column(DateTime(timezone=True), nullable=False)


Index(
    "idx_sensor_readings_sensor_time",
    SensorReading.sensor_id,
    SensorReading.recorded_at.desc(),
)

Index(
    "idx_sensor_readings_time",
    SensorReading.recorded_at.desc(),
)