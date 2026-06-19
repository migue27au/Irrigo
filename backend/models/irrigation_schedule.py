from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from db.base import Base


class IrrigationSchedule(Base):
    __tablename__ = "irrigation_schedules"

    id = Column(BigInteger, primary_key=True, index=True)

    system_id = Column(BigInteger, ForeignKey("irrigation_systems.id", ondelete="CASCADE"), nullable=False)
    output_id = Column(BigInteger, ForeignKey("outputs.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)

    enabled = Column(Boolean, default=True, nullable=False)

    cron_expression = Column(String(100), nullable=False)

    value = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)