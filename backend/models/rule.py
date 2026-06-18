from sqlalchemy import Column, BigInteger, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.db.base import Base


class Rule(Base):
    __tablename__ = "rules"

    id = Column(BigInteger, primary_key=True, index=True)

    system_id = Column(BigInteger, ForeignKey("irrigation_systems.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)

    enabled = Column(Boolean, default=True, nullable=False)

    action_output_id = Column(BigInteger, ForeignKey("outputs.id", ondelete="CASCADE"), nullable=False)
    action_value = Column(Integer, nullable=False)

    cooldown_seconds = Column(Integer, default=0, nullable=False)

    last_executed_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)