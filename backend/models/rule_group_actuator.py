from sqlalchemy import Column, BigInteger, ForeignKey

from db.base import Base


class RuleGroupActuator(Base):
    __tablename__ = "rule_group_actuator"

    id = Column(BigInteger, primary_key=True)

    group_id = Column(
        BigInteger,
        ForeignKey("rule_groups.id", ondelete="CASCADE"),
        nullable=False
    )

    command_id = Column(
        BigInteger,
        ForeignKey("actuator_commands.id", ondelete="CASCADE"),
        nullable=False
    )