from app.core.config import settings
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from sqlalchemy.orm import Session
from typing import Optional

from app.services.runtime_config import get_runtime_model_settings
# If you plan on adding other embeddings, import them here
# from some_other_module import AnotherEmbeddingClass


class EmbeddingsFactory:
    @staticmethod
    def create(provider: Optional[str] = None, model: Optional[str] = None, db: Optional[Session] = None):
        """
        Factory method to create an embeddings instance based on .env config.
        """
        runtime_settings = get_runtime_model_settings(db)
        embeddings_provider = (provider or runtime_settings.get("embeddings_provider") or settings.EMBEDDINGS_PROVIDER).lower()
        model = model or runtime_settings.get("embeddings_model")

        if embeddings_provider == "openai":
            return OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                openai_api_base=runtime_settings.get("openai_api_base", settings.OPENAI_API_BASE),
                model=model or settings.OPENAI_EMBEDDINGS_MODEL
            )
        elif embeddings_provider == "dashscope":
            return DashScopeEmbeddings(
                model=model or settings.DASH_SCOPE_EMBEDDINGS_MODEL,
                dashscope_api_key=settings.DASH_SCOPE_API_KEY
            )
        elif embeddings_provider == "ollama":
            return OllamaEmbeddings(
                model=model or settings.OLLAMA_EMBEDDINGS_MODEL,
                base_url=runtime_settings.get("ollama_api_base", settings.OLLAMA_API_BASE)
            )

        # Extend with other providers:
        # elif embeddings_provider == "another_provider":
        #     return AnotherEmbeddingClass(...)
        else:
            raise ValueError(f"Unsupported embeddings provider: {embeddings_provider}")
