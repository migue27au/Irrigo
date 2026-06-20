from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer, Boolean, Numeric, DateTime
from sqlalchemy.sql import func

from db.base import Base

class RuleGroupAction(Base):
    __tablename__ = "rule_group_actions"

    id = Column(BigInteger, primary_key=True)

    group_id = Column(BigInteger, ForeignKey("rule_groups.id", ondelete="CASCADE"))

    action_id = Column(BigInteger, ForeignKey("automation_actions.id", ondelete="CASCADE"))