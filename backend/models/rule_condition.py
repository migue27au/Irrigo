from sqlalchemy import Column, BigInteger, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from db.base import Base


class RuleCondition(Base):
    __tablename__ = "rule_conditions"

    id = Column(BigInteger, primary_key=True)

    group_id = Column(
        BigInteger,
        ForeignKey("rule_groups.id", ondelete="CASCADE"),
        nullable=False
    )

    sensor_id = Column(BigInteger, ForeignKey("sensors.id"), nullable=True)

    type = Column(String(20), nullable=False)   # sensor | time
    operator = Column(String(5), nullable=True) # > < >= <= == !=
    value = Column(Numeric(12, 4), nullable=True)
    cron = Column(String(100), nullable=True)

    group = relationship("RuleGroup", back_populates="conditions")