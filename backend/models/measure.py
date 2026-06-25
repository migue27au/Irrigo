from sqlalchemy import Column, BigInteger, Numeric, DateTime, ForeignKey, Index

from db.base import Base


class Measure(Base):
    __tablename__ = "measures"

    id = Column(BigInteger, primary_key=True, index=True)

    sensor_id = Column(BigInteger, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False)

    value = Column(Numeric(12, 4), nullable=False)

    recorded_at = Column(DateTime(timezone=True), nullable=False)


Index("idx_measures_sensor_time", Measure.sensor_id, Measure.recorded_at.desc(), )

Index("idx_measures_time", Measure.recorded_at.desc(),)