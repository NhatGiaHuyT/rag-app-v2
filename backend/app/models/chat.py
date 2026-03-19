from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text, UniqueConstraint, DateTime
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

# Association table for many-to-many relationship between Chat and KnowledgeBase
chat_knowledge_bases = Table(
    "chat_knowledge_bases",
    Base.metadata,
    Column("chat_id", Integer, ForeignKey("chats.id"), primary_key=True),
    Column("knowledge_base_id", Integer, ForeignKey("knowledge_bases.id"), primary_key=True),
)

class Chat(Base, TimestampMixin):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    user = relationship("User", back_populates="chats")
    knowledge_bases = relationship(
        "KnowledgeBase",
        secondary=chat_knowledge_bases,
        backref="chats"
    )

class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(LONGTEXT, nullable=False)
    role = Column(String(50), nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    feedback_entries = relationship("MessageFeedback", back_populates="message", cascade="all, delete-orphan")
    override = relationship("MessageOverride", back_populates="message", cascade="all, delete-orphan", uselist=False)


class MessageFeedback(Base, TimestampMixin):
    __tablename__ = "message_feedback"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(String(32), nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="submitted")
    expert_assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assignment_note = Column(Text, nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    message = relationship("Message", back_populates="feedback_entries")
    user = relationship("User", foreign_keys=[user_id], back_populates="feedback_entries")
    expert_assignee = relationship("User", foreign_keys=[expert_assignee_id], back_populates="assigned_feedback")

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_message_feedback_user"),
    )


class MessageOverride(Base, TimestampMixin):
    __tablename__ = "message_overrides"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True)
    expert_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(LONGTEXT, nullable=False)
    note = Column(Text, nullable=True)

    message = relationship("Message", back_populates="override")
    expert_user = relationship("User", back_populates="expert_overrides")
