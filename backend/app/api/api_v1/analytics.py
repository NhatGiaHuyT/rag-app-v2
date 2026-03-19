from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.api_v1.auth import get_current_user
from app.db.session import get_db
from app.models.chat import Chat, Message, MessageFeedback
from app.models.knowledge import Document, KnowledgeBase
from app.models.user import User
from app.schemas.analytics import AnalyticsPoint, UserAnalyticsResponse

router = APIRouter()


@router.get("/me", response_model=UserAnalyticsResponse)
def get_my_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    knowledge_bases = db.query(KnowledgeBase).filter(KnowledgeBase.user_id == current_user.id).count()
    chats = db.query(Chat).filter(Chat.user_id == current_user.id).count()
    messages = (
        db.query(Message)
        .join(Chat)
        .filter(Chat.user_id == current_user.id)
        .count()
    )
    documents = (
        db.query(Document)
        .join(KnowledgeBase)
        .filter(KnowledgeBase.user_id == current_user.id)
        .count()
    )
    feedback = (
        db.query(MessageFeedback)
        .filter(MessageFeedback.user_id == current_user.id)
        .count()
    )

    today = datetime.utcnow().date()
    points = []
    for days_ago in range(6, -1, -1):
        day = today - timedelta(days=days_ago)
        count = (
            db.query(Message)
            .join(Chat)
            .filter(Chat.user_id == current_user.id)
            .filter(Message.created_at >= datetime.combine(day, datetime.min.time()))
            .filter(Message.created_at < datetime.combine(day + timedelta(days=1), datetime.min.time()))
            .count()
        )
        points.append(AnalyticsPoint(label=day.strftime("%b %d"), value=count))

    recent_feedback = []
    feedback_rows = (
        db.query(MessageFeedback)
        .filter(MessageFeedback.user_id == current_user.id)
        .order_by(MessageFeedback.updated_at.desc())
        .limit(5)
        .all()
    )
    for row in feedback_rows:
        recent_feedback.append({
            "id": row.id,
            "rating": row.rating,
            "comment": row.comment,
            "updated_at": row.updated_at.isoformat(),
            "message_id": row.message_id,
        })

    return {
        "summary": {
            "knowledge_bases": knowledge_bases,
            "documents": documents,
            "chats": chats,
            "messages": messages,
            "feedback": feedback,
        },
        "activity": points,
        "recent_feedback": recent_feedback,
    }
