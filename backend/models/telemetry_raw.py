from sqlalchemy import Column, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from backend.db.base import Base


class TelemetryRaw(Base):
    __tablename__ = "telemetry_raw"

    id = Column(BigInteger, primary_key=True, index=True)

    system_id = Column(BigInteger, ForeignKey("irrigation_systems.id", ondelete="CASCADE"), nullable=False)

    payload = Column(JSONB, nullable=False)

    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)