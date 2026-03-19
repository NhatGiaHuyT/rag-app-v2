from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.admin import AccessLog, AuditLog, SystemAlert
from app.models.user import User


def log_audit(
    db: Session,
    actor: Optional[User],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor.id if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )
    )


def log_access(
    db: Session,
    user: Optional[User],
    resource_type: str,
    action: str,
    resource_id: Optional[str] = None,
    success: bool = True,
    failure_reason: Optional[str] = None,
) -> None:
    db.add(
        AccessLog(
            user_id=user.id if user else None,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            success=success,
            failure_reason=failure_reason,
        )
    )


def create_alert(
    db: Session,
    source: str,
    message: str,
    severity: str = "warning",
    metadata_json: Optional[dict[str, Any]] = None,
) -> None:
    existing = (
        db.query(SystemAlert)
        .filter(
            SystemAlert.source == source,
            SystemAlert.message == message,
            SystemAlert.is_resolved.is_(False),
        )
        .first()
    )
    if existing:
        return
    db.add(
        SystemAlert(
            source=source,
            message=message,
            severity=severity,
            metadata_json=metadata_json or {},
        )
    )
