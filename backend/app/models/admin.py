from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(128), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(128), nullable=True)
    details = Column(JSON, nullable=True)

    actor = relationship("User", back_populates="audit_logs")


class AccessLog(Base, TimestampMixin):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=True)
    action = Column(String(64), nullable=False)
    success = Column(Boolean, nullable=False, default=True)
    failure_reason = Column(Text, nullable=True)

    user = relationship("User", back_populates="access_logs")


class SystemAlert(Base, TimestampMixin):
    __tablename__ = "system_alerts"

    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String(32), nullable=False, default="info")
    source = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, nullable=False, default=False)
    metadata_json = Column(JSON, nullable=True)


class SystemConfig(Base, TimestampMixin):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(128), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)


class ManualQAEntry(Base, TimestampMixin):
    __tablename__ = "manual_qa_entries"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    tags = Column(JSON, nullable=True)

    owner = relationship("User", back_populates="manual_qa_entries")
