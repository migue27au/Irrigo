from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer, Boolean, Numeric, DateTime
from sqlalchemy.sql import func

from db.base import Base

class RuleGroup(Base):
    __tablename__ = "rule_groups"

    id = Column(BigInteger, primary_key=True)
    system_id = Column(BigInteger, ForeignKey("irrigation_systems.id"))

    name = Column(String(255))
    description = Column(String(255))  # 👈 aquí tus comentarios