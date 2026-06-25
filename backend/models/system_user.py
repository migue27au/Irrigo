from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from db.base import Base


class SystemUser(Base):
    __tablename__ = "system_users"

    id = Column(BigInteger, primary_key=True, index=True)

    system_id = Column(BigInteger, ForeignKey("systems.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    role = Column(String(30), nullable=False, default="viewer")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("system_id", "user_id", name="uq_system_user"),
    )