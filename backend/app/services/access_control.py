from typing import Iterable, List

from sqlalchemy.orm import Session

from app.models.chat import Chat
from app.models.knowledge import (
    Document,
    DocumentPermission,
    KnowledgeBase,
    KnowledgeBasePermission,
)
from app.models.user import User


EDITOR_LEVELS = {"editor"}


def can_access_knowledge_base(db: Session, user: User, knowledge_base: KnowledgeBase) -> bool:
    if user.is_superuser or knowledge_base.user_id == user.id:
        return True
    if knowledge_base.visibility == "public":
        return True
    permission = (
        db.query(KnowledgeBasePermission)
        .filter(
            KnowledgeBasePermission.knowledge_base_id == knowledge_base.id,
            KnowledgeBasePermission.user_id == user.id,
        )
        .first()
    )
    return permission is not None


def can_edit_knowledge_base(db: Session, user: User, knowledge_base: KnowledgeBase) -> bool:
    if user.is_superuser or knowledge_base.user_id == user.id:
        return True
    permission = (
        db.query(KnowledgeBasePermission)
        .filter(
            KnowledgeBasePermission.knowledge_base_id == knowledge_base.id,
            KnowledgeBasePermission.user_id == user.id,
            KnowledgeBasePermission.permission_level.in_(tuple(EDITOR_LEVELS)),
        )
        .first()
    )
    return permission is not None


def can_access_document(db: Session, user: User, document: Document) -> bool:
    if user.is_superuser or document.knowledge_base.user_id == user.id:
        return True
    if document.access_level == "public":
        return True
    if document.access_level == "inherit":
        return can_access_knowledge_base(db, user, document.knowledge_base)
    permission = (
        db.query(DocumentPermission)
        .filter(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == user.id,
        )
        .first()
    )
    return permission is not None


def can_edit_document(db: Session, user: User, document: Document) -> bool:
    if user.is_superuser or document.knowledge_base.user_id == user.id:
        return True
    permission = (
        db.query(DocumentPermission)
        .filter(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == user.id,
            DocumentPermission.permission_level.in_(tuple(EDITOR_LEVELS)),
        )
        .first()
    )
    return permission is not None or can_edit_knowledge_base(db, user, document.knowledge_base)


def filter_accessible_knowledge_bases(db: Session, user: User, knowledge_bases: Iterable[KnowledgeBase]) -> List[KnowledgeBase]:
    return [kb for kb in knowledge_bases if can_access_knowledge_base(db, user, kb)]


def filter_accessible_documents(db: Session, user: User, documents: Iterable[Document]) -> List[Document]:
    return [doc for doc in documents if can_access_document(db, user, doc)]


def can_access_chat(user: User, chat: Chat) -> bool:
    return user.is_superuser or chat.user_id == user.id
