from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from db.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(BigInteger, primary_key=True, index=True)

    system_id = Column(BigInteger, ForeignKey("irrigation_systems.id", ondelete="CASCADE"), nullable=False)

    event_type = Column(String(100), nullable=False)

    message = Column(Text)

    metadata = Column(JSONB)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)