from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from backend.db.base import Base


class Output(Base):
    __tablename__ = "outputs"

    id = Column(BigInteger, primary_key=True, index=True)

    system_id = Column(BigInteger, ForeignKey("irrigation_systems.id", ondelete="CASCADE"), nullable=False)

    output_key = Column(String(50), nullable=False)

    name = Column(String(255))

    min_value = Column(Integer, default=0, nullable=False)
    max_value = Column(Integer, default=255, nullable=False)

    enabled = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("system_id", "output_key", name="uq_output_key_system"),
    )