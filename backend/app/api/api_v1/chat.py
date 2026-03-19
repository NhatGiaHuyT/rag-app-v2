from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.user import User
from app.models.chat import Chat, Message, MessageFeedback, MessageOverride
from app.models.knowledge import KnowledgeBase
from app.schemas.chat import (
    ChatCreate,
    ChatResponse,
    ChatUpdate,
    MessageCreate,
    MessageResponse
)
from app.api.api_v1.auth import get_current_user
from app.services.chat_service import generate_response
from app.services.access_control import can_access_knowledge_base
from app.services.admin_audit import log_access

router = APIRouter()


def serialize_message(message: Message, current_user: User) -> dict:
    positive = sum(1 for item in message.feedback_entries if item.rating == "up")
    negative = sum(1 for item in message.feedback_entries if item.rating == "down")
    user_feedback = next((item for item in message.feedback_entries if item.user_id == current_user.id), None)
    return {
        "id": message.id,
        "content": message.content,
        "role": message.role,
        "chat_id": message.chat_id,
        "created_at": message.created_at,
        "updated_at": message.updated_at,
        "feedback_summary": {
            "up": positive,
            "down": negative,
            "total": len(message.feedback_entries),
        },
        "user_feedback": None if not user_feedback else {
            "id": user_feedback.id,
            "rating": user_feedback.rating,
            "comment": user_feedback.comment,
            "status": user_feedback.status,
            "expert_assignee_id": user_feedback.expert_assignee_id,
            "assigned_at": user_feedback.assigned_at,
            "resolved_at": user_feedback.resolved_at,
        },
        "expert_override": None if not message.override else {
            "id": message.override.id,
            "content": message.override.content,
            "note": message.override.note,
            "expert_user_id": message.override.expert_user_id,
            "updated_at": message.override.updated_at,
        },
    }


def serialize_chat(chat: Chat, current_user: User) -> dict:
    return {
        "id": chat.id,
        "title": chat.title,
        "user_id": chat.user_id,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "messages": [serialize_message(message, current_user) for message in chat.messages],
        "knowledge_base_ids": [kb.id for kb in chat.knowledge_bases],
    }

@router.post("/", response_model=ChatResponse)
def create_chat(
    *,
    db: Session = Depends(get_db),
    chat_in: ChatCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    # Verify knowledge bases exist and belong to user
    knowledge_bases = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id.in_(chat_in.knowledge_base_ids))
        .all()
    )
    if len(knowledge_bases) != len(chat_in.knowledge_base_ids) or any(
        not can_access_knowledge_base(db, current_user, kb) for kb in knowledge_bases
    ):
        raise HTTPException(
            status_code=400,
            detail="One or more knowledge bases not found"
        )
    
    chat = Chat(
        title=chat_in.title,
        user_id=current_user.id,
    )
    chat.knowledge_bases = knowledge_bases
    
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return serialize_chat(chat, current_user)

@router.get("/", response_model=List[ChatResponse])
def get_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    chats = (
        db.query(Chat)
        .options(
            joinedload(Chat.messages).joinedload(Message.feedback_entries),
            joinedload(Chat.messages).joinedload(Message.override),
            joinedload(Chat.knowledge_bases),
        )
        .filter(Chat.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [serialize_chat(chat, current_user) for chat in chats]

@router.get("/{chat_id}", response_model=ChatResponse)
def get_chat(
    *,
    db: Session = Depends(get_db),
    chat_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    chat = (
        db.query(Chat)
        .options(
            joinedload(Chat.messages).joinedload(Message.feedback_entries),
            joinedload(Chat.messages).joinedload(Message.override),
            joinedload(Chat.knowledge_bases),
        )
        .filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        )
        .first()
    )
    if not chat:
        log_access(db, current_user, "chat", "read", resource_id=str(chat_id), success=False, failure_reason="missing")
        db.commit()
        raise HTTPException(status_code=404, detail="Chat not found")
    log_access(db, current_user, "chat", "read", resource_id=str(chat_id), success=True)
    db.commit()
    return serialize_chat(chat, current_user)

@router.post("/{chat_id}/messages")
async def create_message(
    *,
    db: Session = Depends(get_db),
    chat_id: int,
    messages: dict,
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    chat = (
        db.query(Chat)
        .options(joinedload(Chat.knowledge_bases))
        .filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        )
        .first()
    )
    if not chat:
        log_access(db, current_user, "chat", "message", resource_id=str(chat_id), success=False, failure_reason="missing")
        db.commit()
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get the last user message
    last_message = messages["messages"][-1]
    if last_message["role"] != "user":
        raise HTTPException(status_code=400, detail="Last message must be from user")
    
    # Get knowledge base IDs
    knowledge_base_ids = [kb.id for kb in chat.knowledge_bases]

    async def response_stream():
        async for chunk in generate_response(
            query=last_message["content"],
            messages=messages,
            knowledge_base_ids=knowledge_base_ids,
            chat_id=chat_id,
            db=db
        ):
            yield chunk

    return StreamingResponse(
        response_stream(),
        media_type="text/event-stream",
        headers={
            "x-vercel-ai-data-stream": "v1"
        }
    )

@router.delete("/{chat_id}")
def delete_chat(
    *,
    db: Session = Depends(get_db),
    chat_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    chat = (
        db.query(Chat)
        .filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        )
        .first()
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    db.delete(chat)
    db.commit()
    return {"status": "success"}
