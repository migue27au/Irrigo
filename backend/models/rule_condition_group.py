from sqlalchemy import Column, BigInteger, Integer, ForeignKey

from db.base import Base


class RuleConditionGroup(Base):
    __tablename__ = "rule_condition_groups"

    id = Column(BigInteger, primary_key=True, index=True)

    rule_id = Column(BigInteger, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)

    group_order = Column(Integer, default=1, nullable=False)