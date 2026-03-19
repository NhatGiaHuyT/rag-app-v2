from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.api_v1.auth import get_current_expert, get_current_user
from app.db.session import get_db
from app.models.chat import Chat, Message, MessageFeedback, MessageOverride
from app.models.user import User
from app.schemas.feedback import (
    ExpertFeedbackQueueItem,
    FeedbackCreate,
    FeedbackResponse,
    MessageOverrideResponse,
    MessageOverrideUpsert,
)

router = APIRouter()


def get_owned_message(db: Session, message_id: int, current_user: User) -> Message:
    message = (
        db.query(Message)
        .join(Chat)
        .options(joinedload(Message.override))
        .filter(Message.id == message_id, Chat.user_id == current_user.id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.post("/messages/{message_id}/feedback", response_model=FeedbackResponse)
def upsert_feedback(
    *,
    message_id: int,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    message = get_owned_message(db, message_id, current_user)
    if message.role != "assistant":
        raise HTTPException(status_code=400, detail="Feedback can only be left on assistant messages")

    feedback = (
        db.query(MessageFeedback)
        .filter(MessageFeedback.message_id == message_id, MessageFeedback.user_id == current_user.id)
        .first()
    )
    if not feedback:
        feedback = MessageFeedback(message_id=message_id, user_id=current_user.id, rating=payload.rating)

    feedback.rating = payload.rating
    feedback.comment = payload.comment
    if payload.rating == "down":
        feedback.status = "flagged"
        feedback.resolved_at = None
    elif feedback.status == "resolved":
        feedback.status = "resolved"
    else:
        feedback.status = "submitted"
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.put("/messages/{message_id}/override", response_model=MessageOverrideResponse)
def upsert_message_override(
    *,
    message_id: int,
    payload: MessageOverrideUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_expert)
) -> Any:
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.role != "assistant":
        raise HTTPException(status_code=400, detail="Only assistant messages can be overridden")

    override = db.query(MessageOverride).filter(MessageOverride.message_id == message_id).first()
    if not override:
        override = MessageOverride(message_id=message_id)

    override.content = payload.content
    override.note = payload.note
    override.expert_user_id = current_user.id
    db.add(override)

    related_feedback = (
        db.query(MessageFeedback)
        .filter(MessageFeedback.message_id == message_id, MessageFeedback.rating == "down")
        .all()
    )
    for feedback in related_feedback:
        if feedback.expert_assignee_id and feedback.expert_assignee_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="This flagged answer is assigned to another expert")
        feedback.expert_assignee_id = current_user.id
        feedback.status = "resolved"
        feedback.resolved_at = datetime.utcnow()
        if not feedback.assigned_at:
            feedback.assigned_at = datetime.utcnow()
        db.add(feedback)

    db.commit()
    db.refresh(override)
    return override


@router.get("/expert/assignments", response_model=list[ExpertFeedbackQueueItem])
def get_expert_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_expert)
) -> Any:
    feedback_items = (
        db.query(MessageFeedback)
        .join(Message, Message.id == MessageFeedback.message_id)
        .join(Chat, Chat.id == Message.chat_id)
        .options(joinedload(MessageFeedback.message).joinedload(Message.chat), joinedload(MessageFeedback.user))
        .filter(
            MessageFeedback.rating == "down",
            MessageFeedback.status.in_(["flagged", "assigned"]),
            MessageFeedback.expert_assignee_id == current_user.id,
        )
        .order_by(MessageFeedback.updated_at.desc())
        .all()
    )

    results = []
    for feedback in feedback_items:
        user_question = (
            db.query(Message)
            .filter(Message.chat_id == feedback.message.chat_id, Message.role == "user", Message.created_at <= feedback.message.created_at)
            .order_by(Message.created_at.desc())
            .first()
        )
        results.append(
            ExpertFeedbackQueueItem(
                feedback_id=feedback.id,
                message_id=feedback.message_id,
                chat_id=feedback.message.chat_id,
                chat_title=feedback.message.chat.title,
                question=user_question.content if user_question else "",
                answer=feedback.message.content,
                comment=feedback.comment,
                status=feedback.status,
                assigned_at=feedback.assigned_at,
                requester_user_id=feedback.user_id,
                requester_username=feedback.user.username,
                expert_assignee_id=feedback.expert_assignee_id,
            )
        )
    return results
