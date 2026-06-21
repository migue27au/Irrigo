from sqlalchemy import Column, BigInteger, String, ForeignKey, Boolean, DateTime
from sqlalchemy.sql import func

from db.base import Base


class RuleGroup(Base):
    __tablename__ = "rule_groups"

    id = Column(BigInteger, primary_key=True)

    system_id = Column(
        BigInteger,
        ForeignKey("irrigation_systems.id", ondelete="CASCADE"),
        nullable=False
    )

    name = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)

    enabled = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )