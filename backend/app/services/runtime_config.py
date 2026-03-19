from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.admin import SystemConfig


def get_runtime_model_settings(db: Optional[Session] = None) -> dict[str, Any]:
    defaults = {
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
        "ollama_api_base": settings.OLLAMA_API_BASE,
        "openai_api_base": settings.OPENAI_API_BASE,
        "deepseek_api_base": settings.DEEPSEEK_API_BASE,
    }
    if not db:
        return defaults

    row = db.query(SystemConfig).filter(SystemConfig.key == "model_settings").first()
    if not row or not row.value:
        return defaults

    merged = defaults.copy()
    merged.update(row.value)
    return merged
