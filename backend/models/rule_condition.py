from sqlalchemy import Column, BigInteger, String, ForeignKey, Numeric

from db.base import Base


class RuleCondition(Base):
    __tablename__ = "rule_conditions"

    id = Column(BigInteger, primary_key=True)

    group_id = Column(
        BigInteger,
        ForeignKey("rule_groups.id", ondelete="CASCADE"),
        nullable=False
    )

    type = Column(String(20), nullable=False)
    # sensor | time

    sensor_id = Column(
        BigInteger,
        ForeignKey("sensors.id"),
        nullable=True
    )

    operator = Column(String(5), nullable=True)
    # > < >= <= == !=

    value = Column(Numeric(12, 4), nullable=True)

    cron = Column(String(100), nullable=True)