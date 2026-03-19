from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    rating: str
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    rating: str
    comment: Optional[str] = None
    status: str
    expert_assignee_id: Optional[int] = None
    assignment_note: Optional[str] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageOverrideUpsert(BaseModel):
    content: str
    note: Optional[str] = None


class MessageOverrideResponse(BaseModel):
    id: int
    message_id: int
    expert_user_id: Optional[int] = None
    content: str
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpertAssignmentUpdate(BaseModel):
    expert_user_id: int
    assignment_note: Optional[str] = None


class ExpertFeedbackQueueItem(BaseModel):
    feedback_id: int
    message_id: int
    chat_id: int
    chat_title: str
    question: str
    answer: str
    comment: Optional[str] = None
    status: str
    assigned_at: Optional[datetime] = None
    requester_user_id: int
    requester_username: str
    expert_assignee_id: Optional[int] = None
