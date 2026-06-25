from sqlalchemy import Column, BigInteger, String, ForeignKey, Boolean, Numeric, DateTime
from sqlalchemy.sql import func

from db.base import Base


class ActuatorCommand(Base):
    __tablename__ = "actuator_commands"

    id = Column(BigInteger, primary_key=True)

    system_id = Column(BigInteger, ForeignKey("systems.id", ondelete="CASCADE"), index=True, nullable=False)

    actuator_id = Column(BigInteger, ForeignKey("systems.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=True)

    trigger_type = Column(String(20), nullable=False)
    # manual | automatic

    intensity = Column(Numeric(5, 2), nullable=True)
    duration_seconds = Column(BigInteger, nullable=True)

    enabled = Column(Boolean, default=True)
    disabled_reason = Column(String(50), nullable=True)

    executed_count = Column(BigInteger, default=0, nullable=False)
    last_executed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)