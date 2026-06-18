from sqlalchemy import Column, BigInteger, String, Text, DateTime, func
from backend.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)

    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)

    name = Column(String(255))
    role = Column(String(30), default="user", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())