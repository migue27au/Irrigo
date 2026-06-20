from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer, Boolean, Numeric, DateTime
from sqlalchemy.sql import func

from db.base import Base

class RuleCondition(Base):
    __tablename__ = "rule_conditions"

    id = Column(BigInteger, primary_key=True)

    group_id = Column(BigInteger, ForeignKey("rule_groups.id", ondelete="CASCADE"))

    # sensor-based or time-based
    type = Column(String(20))  
    # sensor | time

    # SENSOR RULE
    sensor_id = Column(BigInteger, ForeignKey("sensors.id"), nullable=True)
    operator = Column(String(5))  # > < >= <= ==
    value = Column(Numeric(12, 4), nullable=True)

    # TIME RULE
    cron = Column(String(100), nullable=True)