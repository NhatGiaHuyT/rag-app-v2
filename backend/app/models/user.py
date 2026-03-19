from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(1024), nullable=True)
    role = Column(String(32), nullable=False, default="user")
    feature_flags = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_expert = Column(Boolean, default=False)
    suspended_until = Column(DateTime, nullable=True)
    suspension_reason = Column(Text, nullable=True)

    # Relationships
    knowledge_bases = relationship("KnowledgeBase", back_populates="user")
    chats = relationship("Chat", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    knowledge_base_permissions = relationship("KnowledgeBasePermission", back_populates="user", cascade="all, delete-orphan")
    document_permissions = relationship("DocumentPermission", back_populates="user", cascade="all, delete-orphan")
    feedback_entries = relationship(
        "MessageFeedback",
        foreign_keys="MessageFeedback.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    assigned_feedback = relationship("MessageFeedback", foreign_keys="MessageFeedback.expert_assignee_id", back_populates="expert_assignee")
    expert_overrides = relationship("MessageOverride", back_populates="expert_user")
    audit_logs = relationship("AuditLog", back_populates="actor")
    access_logs = relationship("AccessLog", back_populates="user")
    manual_qa_entries = relationship("ManualQAEntry", back_populates="owner")
