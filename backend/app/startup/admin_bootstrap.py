import logging
from dataclasses import dataclass

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class AdminBootstrapConfig:
    email: str
    username: str
    password: str
    full_name: str = "Administrator"
    role: str = "super_admin"
    reset_password: bool = False


def bootstrap_admin_account(config: AdminBootstrapConfig) -> tuple[bool, str]:
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter((User.email == config.email) | (User.username == config.username))
            .first()
        )

        created = False
        if not user:
            user = User(
                email=config.email,
                username=config.username,
                hashed_password=get_password_hash(config.password),
            )
            created = True

        user.email = config.email
        user.username = config.username
        user.full_name = config.full_name
        user.role = config.role
        user.is_active = True
        user.is_superuser = config.role == "super_admin"
        user.is_expert = config.role == "expert"
        user.suspended_until = None
        user.suspension_reason = None
        user.feature_flags = {
            "feedback_enabled": True,
            "history_enabled": True,
            "chat_export_enabled": True,
        }

        if created or config.reset_password:
            user.hashed_password = get_password_hash(config.password)

        db.add(user)
        db.commit()
        db.refresh(user)

        action = "created" if created else "updated"
        message = (
            f"Admin account {action}: username={user.username}, "
            f"email={user.email}, role={user.role}"
        )
        return created, message
    finally:
        db.close()


def bootstrap_admin_from_settings(settings) -> str | None:
    if not getattr(settings, "BOOTSTRAP_ADMIN_ON_STARTUP", False):
        return None

    required_values = {
        "BOOTSTRAP_ADMIN_EMAIL": getattr(settings, "BOOTSTRAP_ADMIN_EMAIL", ""),
        "BOOTSTRAP_ADMIN_USERNAME": getattr(settings, "BOOTSTRAP_ADMIN_USERNAME", ""),
        "BOOTSTRAP_ADMIN_PASSWORD": getattr(settings, "BOOTSTRAP_ADMIN_PASSWORD", ""),
    }
    missing = [key for key, value in required_values.items() if not value]
    if missing:
        logger.warning(
            "Skipping startup admin bootstrap because required env vars are missing: %s",
            ", ".join(missing),
        )
        return None

    _, message = bootstrap_admin_account(
        AdminBootstrapConfig(
            email=settings.BOOTSTRAP_ADMIN_EMAIL,
            username=settings.BOOTSTRAP_ADMIN_USERNAME,
            password=settings.BOOTSTRAP_ADMIN_PASSWORD,
            full_name=settings.BOOTSTRAP_ADMIN_FULL_NAME,
            role=settings.BOOTSTRAP_ADMIN_ROLE,
            reset_password=settings.BOOTSTRAP_ADMIN_RESET_PASSWORD,
        )
    )
    logger.info(message)
    return message
