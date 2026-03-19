from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.api.api_v1.auth import get_current_admin, get_current_super_admin
from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.admin import AccessLog, AuditLog, ManualQAEntry, SystemAlert, SystemConfig
from app.models.chat import Chat, Message, MessageFeedback
from app.models.knowledge import Document, KnowledgeBase, ProcessingTask
from app.models.user import User
from app.schemas.admin import (
    AccessLogResponse,
    AdminExpertAssignmentRequest,
    AdminFlaggedAnswerResponse,
    AdminDocumentUpdate,
    AdminKnowledgeBaseUpdate,
    AdminPasswordReset,
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserSuspend,
    AdminUserUpdate,
    AuditLogResponse,
    ManualQAEntryCreate,
    ManualQAEntryResponse,
    SystemAlertResponse,
    SystemConfigResponse,
    SystemConfigUpdate,
)
from app.schemas.analytics import AdminOverviewResponse, AnalyticsPoint
from app.services.admin_audit import create_alert, log_access, log_audit
from app.services.document_processor import reindex_document_from_chunks

router = APIRouter()


DEFAULT_SYSTEM_CONFIG = {
    "response_settings": {
        "max_answer_length": 1024,
        "response_format": "markdown",
        "summarization": True,
        "citations": True,
    },
    "feedback_workflow": {
        "allow_votes": True,
        "route_flagged_answers_to_experts": True,
        "expert_role": "expert",
    },
    "integrations": {
        "slack": False,
        "teams": False,
        "email_notifications": False,
        "internal_portal": False,
    },
    "model_settings": {
        "chat_provider": settings.CHAT_PROVIDER,
        "chat_model": {
            "openai": settings.OPENAI_MODEL,
            "deepseek": settings.DEEPSEEK_MODEL,
            "ollama": settings.OLLAMA_MODEL,
        }.get(settings.CHAT_PROVIDER, settings.OPENAI_MODEL),
        "embeddings_provider": settings.EMBEDDINGS_PROVIDER,
        "embeddings_model": {
            "openai": settings.OPENAI_EMBEDDINGS_MODEL,
            "dashscope": settings.DASH_SCOPE_EMBEDDINGS_MODEL,
            "ollama": settings.OLLAMA_EMBEDDINGS_MODEL,
        }.get(settings.EMBEDDINGS_PROVIDER, settings.OPENAI_EMBEDDINGS_MODEL),
        "openai_api_base": settings.OPENAI_API_BASE,
        "deepseek_api_base": settings.DEEPSEEK_API_BASE,
        "ollama_api_base": settings.OLLAMA_API_BASE,
    },
}


def serialize_user(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        feature_flags=user.feature_flags or {},
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_expert=user.is_expert,
        suspended_until=user.suspended_until,
        suspension_reason=user.suspension_reason,
        knowledge_base_count=len(user.knowledge_bases),
        chat_count=len(user.chats),
    )


def require_super_admin_for_destructive(actor: User) -> None:
    if not (actor.is_superuser or actor.role == "super_admin"):
        raise HTTPException(status_code=403, detail="Only super-admins can perform this action")


def get_or_create_system_config(db: Session) -> dict[str, Any]:
    payload = {}
    for key, default in DEFAULT_SYSTEM_CONFIG.items():
        row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not row:
            row = SystemConfig(key=key, value=default, description=f"Admin setting for {key}")
            db.add(row)
            db.flush()
        payload[key] = row.value or default
    return payload


@router.get("/overview", response_model=AdminOverviewResponse)
def get_admin_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    summary = {
        "users": db.query(User).count(),
        "active_users": db.query(User).filter(User.is_active.is_(True)).count(),
        "experts": db.query(User).filter(User.is_expert.is_(True)).count(),
        "knowledge_bases": db.query(KnowledgeBase).count(),
        "documents": db.query(Document).count(),
        "chats": db.query(Chat).count(),
        "questions": db.query(Message).filter(Message.role == "user").count(),
        "feedback": db.query(MessageFeedback).count(),
        "flagged_answers": db.query(MessageFeedback).filter(MessageFeedback.rating == "down").count(),
    }

    today = datetime.utcnow().date()
    activity = []
    for days_ago in range(6, -1, -1):
        day = today - timedelta(days=days_ago)
        count = (
            db.query(Message)
            .filter(Message.role == "user")
            .filter(Message.created_at >= datetime.combine(day, datetime.min.time()))
            .filter(Message.created_at < datetime.combine(day + timedelta(days=1), datetime.min.time()))
            .count()
        )
        activity.append(AnalyticsPoint(label=day.strftime("%b %d"), value=count))

    top_users = []
    rows = (
        db.query(
            User.id,
            User.username,
            User.full_name,
            func.count(Chat.id).label("chat_count"),
        )
        .outerjoin(Chat, Chat.user_id == User.id)
        .group_by(User.id, User.username, User.full_name)
        .order_by(func.count(Chat.id).desc(), User.username.asc())
        .limit(5)
        .all()
    )
    for row in rows:
        top_users.append({
            "id": row.id,
            "username": row.username,
            "full_name": row.full_name,
            "chat_count": int(row.chat_count),
        })

    topic_counter: Counter[str] = Counter()
    recent_questions = db.query(Message).filter(Message.role == "user").order_by(Message.created_at.desc()).limit(250).all()
    for question in recent_questions:
        words = [word.strip(".,!?").lower() for word in question.content.split()[:8]]
        for word in words:
            if len(word) >= 5:
                topic_counter[word] += 1

    frequent_topics = [
        {"topic": topic, "count": count}
        for topic, count in topic_counter.most_common(8)
    ]

    peak_rows = (
        db.query(extract("hour", Message.created_at).label("hour"), func.count(Message.id).label("count"))
        .filter(Message.role == "user")
        .group_by("hour")
        .order_by(func.count(Message.id).desc())
        .limit(5)
        .all()
    )
    peak_hours = [{"hour": int(row.hour), "count": int(row.count)} for row in peak_rows]

    feedback_summary = {
        "up": db.query(MessageFeedback).filter(MessageFeedback.rating == "up").count(),
        "down": db.query(MessageFeedback).filter(MessageFeedback.rating == "down").count(),
    }

    doc_rows = (
        db.query(Document.id, Document.file_name, Document.query_count, Document.last_queried_at, Document.status)
        .order_by(Document.query_count.desc(), Document.updated_at.desc())
        .limit(10)
        .all()
    )
    document_effectiveness = [
        {
            "id": row.id,
            "file_name": row.file_name,
            "query_count": row.query_count,
            "status": row.status,
            "last_queried_at": row.last_queried_at.isoformat() if row.last_queried_at else None,
        }
        for row in doc_rows
    ]

    if db.query(ProcessingTask).filter(ProcessingTask.status == "failed").count() >= 3:
        create_alert(
            db,
            source="processing_tasks",
            severity="warning",
            message="Repeated document processing failures detected.",
            metadata_json={"failed_tasks": db.query(ProcessingTask).filter(ProcessingTask.status == "failed").count()},
        )

    failed_access_attempts = (
        db.query(AccessLog)
        .filter(AccessLog.success.is_(False), AccessLog.created_at >= datetime.utcnow() - timedelta(hours=24))
        .count()
    )
    if failed_access_attempts >= 5:
        create_alert(
            db,
            source="security",
            severity="warning",
            message="High volume of failed access attempts in the last 24 hours.",
            metadata_json={"failed_access_attempts": failed_access_attempts},
        )

    log_audit(db, current_user, "admin.view_overview", "admin_dashboard", details={"section": "overview"})
    db.commit()

    return {
        "summary": summary,
        "activity": activity,
        "top_users": top_users,
        "frequent_topics": frequent_topics,
        "peak_hours": peak_hours,
        "feedback_summary": feedback_summary,
        "document_effectiveness": document_effectiveness,
    }


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    users = db.query(User).order_by(User.created_at.desc()).all()
    log_audit(db, current_user, "admin.list_users", "user")
    db.commit()
    return {"users": [serialize_user(user) for user in users]}


@router.post("/users", response_model=AdminUserResponse)
def create_user(
    *,
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="A user with this email already exists.")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="A user with this username already exists.")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=security.get_password_hash(payload.password),
        full_name=payload.full_name,
        bio=payload.bio,
        avatar_url=payload.avatar_url,
        role=payload.role,
        feature_flags=payload.feature_flags,
        is_active=payload.is_active,
        is_expert=payload.is_expert or payload.role == "expert",
        is_superuser=payload.role == "super_admin",
    )
    db.add(user)
    log_audit(db, current_user, "admin.create_user", "user", entity_id=str(payload.username), details={"role": payload.role})
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.put("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    *,
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = payload.dict(exclude_unset=True)
    if "password" in updates and updates["password"]:
        user.hashed_password = security.get_password_hash(updates.pop("password"))

    if "role" in updates:
        role = updates["role"]
        user.role = role
        user.is_expert = role == "expert" or updates.get("is_expert", user.is_expert)
        user.is_superuser = role == "super_admin" or updates.get("is_superuser", user.is_superuser)
        updates.pop("role")

    for field, value in updates.items():
        setattr(user, field, value)

    log_audit(db, current_user, "admin.update_user", "user", entity_id=str(user_id), details=updates)
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/users/{user_id}/reset-password", response_model=AdminUserResponse)
def reset_user_password(
    *,
    user_id: int,
    payload: AdminPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = security.get_password_hash(payload.new_password)
    log_audit(db, current_user, "admin.reset_password", "user", entity_id=str(user_id))
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/users/{user_id}/suspend", response_model=AdminUserResponse)
def suspend_user(
    *,
    user_id: int,
    payload: AdminUserSuspend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.suspended_until = payload.suspend_until or (datetime.utcnow() + timedelta(days=7))
    user.suspension_reason = payload.reason
    user.is_active = False
    log_audit(db, current_user, "admin.suspend_user", "user", entity_id=str(user_id), details={"reason": payload.reason})
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/users/{user_id}/unsuspend", response_model=AdminUserResponse)
def unsuspend_user(
    *,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.suspended_until = None
    user.suspension_reason = None
    user.is_active = True
    log_audit(db, current_user, "admin.unsuspend_user", "user", entity_id=str(user_id))
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.delete("/users/{user_id}")
def delete_user(
    *,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    log_audit(db, current_user, "admin.delete_user", "user", entity_id=str(user_id))
    db.delete(user)
    db.commit()
    return {"status": "success"}


@router.get("/knowledge-bases")
def list_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    knowledge_bases = db.query(KnowledgeBase).order_by(KnowledgeBase.updated_at.desc()).all()
    log_audit(db, current_user, "admin.list_knowledge_bases", "knowledge_base")
    db.commit()
    return [
        {
            "id": kb.id,
            "name": kb.name,
            "visibility": kb.visibility,
            "category": kb.category,
            "department": kb.department,
            "sensitivity": kb.sensitivity,
            "document_count": len(kb.documents),
            "preprocessing_config": kb.preprocessing_config or {},
        }
        for kb in knowledge_bases
    ]


@router.put("/knowledge-bases/{kb_id}")
def update_knowledge_base(
    *,
    kb_id: int,
    payload: AdminKnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    updates = payload.dict(exclude_unset=True)
    for field, value in updates.items():
        setattr(kb, field, value)
    log_audit(db, current_user, "admin.update_knowledge_base", "knowledge_base", entity_id=str(kb_id), details=updates)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return {"status": "success", "knowledge_base_id": kb.id}


@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    documents = db.query(Document).order_by(Document.updated_at.desc()).all()
    log_audit(db, current_user, "admin.list_documents", "document")
    db.commit()
    return [
        {
            "id": document.id,
            "file_name": document.file_name,
            "knowledge_base_id": document.knowledge_base_id,
            "category": document.category,
            "department": document.department,
            "sensitivity": document.sensitivity,
            "status": document.status,
            "query_count": document.query_count,
            "last_indexed_at": document.last_indexed_at.isoformat() if document.last_indexed_at else None,
            "last_queried_at": document.last_queried_at.isoformat() if document.last_queried_at else None,
            "access_level": document.access_level,
        }
        for document in documents
    ]


@router.put("/documents/{document_id}")
def update_document(
    *,
    document_id: int,
    payload: AdminDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    updates = payload.dict(exclude_unset=True)
    for field, value in updates.items():
        setattr(document, field, value)
    log_audit(db, current_user, "admin.update_document", "document", entity_id=str(document_id), details=updates)
    db.add(document)
    db.commit()
    db.refresh(document)
    return {"status": "success", "document_id": document.id}


@router.post("/documents/{document_id}/reindex")
def reindex_document(
    *,
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not document.chunks:
        raise HTTPException(status_code=400, detail="Document has no stored chunks to reindex")
    task = ProcessingTask(
        knowledge_base_id=document.knowledge_base_id,
        document_id=document.id,
        status="pending",
    )
    document.last_indexed_at = datetime.utcnow()
    db.add(task)
    db.add(document)
    log_audit(db, current_user, "admin.reindex_document", "document", entity_id=str(document_id))
    db.commit()
    background_tasks.add_task(reindex_document_from_chunks, document.id, task.id)
    return {"status": "queued", "task_id": task.id}


@router.delete("/documents/{document_id}")
def delete_document(
    *,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
) -> Any:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    log_audit(db, current_user, "admin.delete_document", "document", entity_id=str(document_id))
    db.delete(document)
    db.commit()
    return {"status": "success"}


@router.get("/quality/flagged-answers")
def get_flagged_answers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> list[AdminFlaggedAnswerResponse]:
    rows = (
        db.query(MessageFeedback, Message, Chat, User)
        .join(Message, Message.id == MessageFeedback.message_id)
        .join(Chat, Chat.id == Message.chat_id)
        .join(User, User.id == Chat.user_id)
        .filter(MessageFeedback.rating == "down", Message.role == "assistant")
        .order_by(MessageFeedback.updated_at.desc())
        .limit(50)
        .all()
    )
    log_audit(db, current_user, "admin.list_flagged_answers", "message_feedback")
    db.commit()
    results = []
    for feedback, message, chat, requester in rows:
        question_message = (
            db.query(Message)
            .filter(Message.chat_id == chat.id, Message.role == "user", Message.created_at <= message.created_at)
            .order_by(Message.created_at.desc())
            .first()
        )
        assignee_name = None
        if feedback.expert_assignee:
            assignee_name = feedback.expert_assignee.full_name or feedback.expert_assignee.username
        results.append(
            AdminFlaggedAnswerResponse(
                feedback_id=feedback.id,
                message_id=message.id,
                chat_id=chat.id,
                chat_title=chat.title,
                question=question_message.content if question_message else "",
                answer=message.content,
                comment=feedback.comment,
                created_at=feedback.created_at.isoformat(),
                status=feedback.status,
                requester_user_id=requester.id,
                requester_username=requester.username,
                expert_assignee_id=feedback.expert_assignee_id,
                expert_assignee_name=assignee_name,
            )
        )
    return results


@router.post("/quality/flagged-answers/{feedback_id}/assign")
def assign_flagged_answer(
    *,
    feedback_id: int,
    payload: AdminExpertAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    feedback = db.query(MessageFeedback).filter(MessageFeedback.id == feedback_id, MessageFeedback.rating == "down").first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Flagged feedback not found")

    expert = db.query(User).filter(User.id == payload.expert_user_id).first()
    if not expert or not (expert.is_expert or expert.role in {"expert", "admin", "super_admin"}):
        raise HTTPException(status_code=400, detail="Selected user is not eligible for expert review")

    feedback.expert_assignee_id = expert.id
    feedback.assignment_note = payload.assignment_note
    feedback.assigned_at = datetime.utcnow()
    feedback.status = "assigned"
    db.add(feedback)
    log_audit(
        db,
        current_user,
        "admin.assign_flagged_answer",
        "message_feedback",
        entity_id=str(feedback_id),
        details={"expert_user_id": expert.id, "assignment_note": payload.assignment_note},
    )
    db.commit()
    return {"status": "assigned", "feedback_id": feedback.id, "expert_user_id": expert.id}


@router.post("/quality/manual-qa", response_model=ManualQAEntryResponse)
def create_manual_qa_entry(
    *,
    payload: ManualQAEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    entry = ManualQAEntry(
        question=payload.question,
        answer=payload.answer,
        owner_user_id=current_user.id,
        tags=payload.tags,
    )
    db.add(entry)
    log_audit(db, current_user, "admin.create_manual_qa", "manual_qa")
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/quality/manual-qa", response_model=list[ManualQAEntryResponse])
def list_manual_qa_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    entries = db.query(ManualQAEntry).order_by(ManualQAEntry.updated_at.desc()).all()
    log_audit(db, current_user, "admin.list_manual_qa", "manual_qa")
    db.commit()
    return entries


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
    log_audit(db, current_user, "admin.list_audit_logs", "audit_log")
    db.commit()
    return [
        AuditLogResponse(
            id=log.id,
            actor_user_id=log.actor_user_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=log.details or {},
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/access-logs", response_model=list[AccessLogResponse])
def list_access_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    logs = db.query(AccessLog).order_by(AccessLog.created_at.desc()).limit(200).all()
    log_audit(db, current_user, "admin.list_access_logs", "access_log")
    db.commit()
    return [
        AccessLogResponse(
            id=log.id,
            user_id=log.user_id,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            action=log.action,
            success=log.success,
            failure_reason=log.failure_reason,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/alerts", response_model=list[SystemAlertResponse])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    alerts = db.query(SystemAlert).order_by(SystemAlert.created_at.desc()).limit(100).all()
    log_audit(db, current_user, "admin.list_alerts", "system_alert")
    db.commit()
    return [
        SystemAlertResponse(
            id=alert.id,
            severity=alert.severity,
            source=alert.source,
            message=alert.message,
            is_resolved=alert.is_resolved,
            metadata_json=alert.metadata_json or {},
            created_at=alert.created_at,
        )
        for alert in alerts
    ]


@router.get("/system-config", response_model=SystemConfigResponse)
def get_system_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    payload = get_or_create_system_config(db)
    log_audit(db, current_user, "admin.get_system_config", "system_config")
    db.commit()
    return payload


@router.put("/system-config", response_model=SystemConfigResponse)
def update_system_config(
    *,
    payload: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    updates = payload.dict()
    if "model_settings" in updates and updates["model_settings"] and not (
        current_user.is_superuser or current_user.role == "super_admin"
    ):
        raise HTTPException(status_code=403, detail="Only super-admins can change active model settings")
    for key, value in updates.items():
        row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not row:
            row = SystemConfig(key=key, value=value)
        else:
            row.value = value
        db.add(row)
    log_audit(db, current_user, "admin.update_system_config", "system_config", details=updates)
    db.commit()
    return get_or_create_system_config(db)
