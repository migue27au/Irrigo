from sqlalchemy import Column, BigInteger, String, Text, DateTime
from sqlalchemy.sql import func

from backend.db.base import Base


class IrrigationSystem(Base):
    __tablename__ = "irrigation_systems"

    id = Column(BigInteger, primary_key=True, index=True)

    api_key_hash = Column(Text, nullable=False)

    alias = Column(String(255), nullable=False)
    description = Column(Text)

    firmware_version = Column(String(50))
    last_seen_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())