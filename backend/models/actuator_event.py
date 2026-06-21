from sqlalchemy import Column, BigInteger, String, ForeignKey, Numeric, DateTime

from db.base import Base


class ActuatorEvent(Base):
    __tablename__ = "actuator_events"

    id = Column(BigInteger, primary_key=True)

    actuator_id = Column(
        BigInteger,
        ForeignKey("system_actuators.id", ondelete="CASCADE"),
        nullable=False
    )

    command_id = Column(
        BigInteger,
        ForeignKey("actuator_commands.id", ondelete="SET NULL"),
        nullable=True
    )

    intensity = Column(Numeric(5, 2), nullable=True)
    duration_seconds = Column(BigInteger, nullable=True)

    trigger_type = Column(String(20), nullable=False)

    recorded_at = Column(DateTime(timezone=True), nullable=False)