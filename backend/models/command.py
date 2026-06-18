from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from backend.db.base import Base


class Command(Base):
    __tablename__ = "commands"

    id = Column(BigInteger, primary_key=True, index=True)

    system_id = Column(BigInteger, ForeignKey("irrigation_systems.id", ondelete="CASCADE"), nullable=False)
    output_id = Column(BigInteger, ForeignKey("outputs.id", ondelete="CASCADE"), nullable=False)

    value = Column(Integer, nullable=False)

    status = Column(String(20), default="pending", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sent_at = Column(DateTime(timezone=True))
    executed_at = Column(DateTime(timezone=True))

    response_message = Column(Text)


Index("idx_commands_pending", Command.system_id, Command.status)