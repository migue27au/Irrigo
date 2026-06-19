from sqlalchemy import Column, BigInteger, String, Numeric, ForeignKey

from db.base import Base


class RuleCondition(Base):
    __tablename__ = "rule_conditions"

    id = Column(BigInteger, primary_key=True, index=True)

    group_id = Column(BigInteger, ForeignKey("rule_condition_groups.id", ondelete="CASCADE"), nullable=False)
    sensor_id = Column(BigInteger, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False)

    operator = Column(String(10), nullable=False)
    compare_value = Column(Numeric(12, 4), nullable=False)