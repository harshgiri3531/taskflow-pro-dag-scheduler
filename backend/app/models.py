from sqlalchemy import Column, String, Float, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Text
from datetime import datetime
import uuid
from .db import Base


def gen_id():
    return str(uuid.uuid4())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=gen_id)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    duration = Column(Float, nullable=False, default=1.0)
    column = Column(String(50), nullable=False, default="Backlog")
    created_at = Column(DateTime, default=datetime.utcnow)


class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(String, primary_key=True, default=gen_id)
    predecessor_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    successor_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(10), default="manual")  # manual | ai
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("predecessor_id", "successor_id", name="uq_dependency_pair"),
        CheckConstraint("predecessor_id != successor_id", name="ck_no_self_dependency"),
    )


class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(String, primary_key=True, default=gen_id)
    predecessor_id = Column(String, nullable=False)
    successor_id = Column(String, nullable=False)
    reason = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    status = Column(String(10), default="pending")  # pending | accepted | dismissed
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=gen_id)
    task_id = Column(String, nullable=True)
    action = Column(String(50), nullable=False)
    old_value = Column(Text, default="")
    new_value = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
