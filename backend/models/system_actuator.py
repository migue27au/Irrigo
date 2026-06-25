from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer, Boolean, Numeric, DateTime
from sqlalchemy.sql import func

from db.base import Base


class SystemActuator(Base):
    __tablename__ = "system_actuators"

    id = Column(BigInteger, primary_key=True)

    system_id = Column(BigInteger, ForeignKey("systems.id", ondelete="CASCADE"), nullable=False, index=True)

    # Canal donde esta conectado (0-3)
    channel = Column(Integer, nullable=False)

    # Configuración lógica
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    # Estado actual
    enabled = Column(Boolean, default=False, nullable=False)

    intensity = Column(Numeric(5, 2), nullable=True)  # PWM 0-255

    # Auditoría mínima
    last_changed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    last_changed_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)