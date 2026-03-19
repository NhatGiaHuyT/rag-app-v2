from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import OllamaLLM
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.runtime_config import get_runtime_model_settings

class LLMFactory:
    @staticmethod
    def create(
        provider: Optional[str] = None,
        temperature: float = 0,
        streaming: bool = True,
        model: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> BaseChatModel:
        """
        Create a LLM instance based on the provider
        """
        runtime_settings = get_runtime_model_settings(db)
        provider = (provider or runtime_settings.get("chat_provider") or settings.CHAT_PROVIDER).lower()
        model = model or runtime_settings.get("chat_model")

        if provider == "openai":
            return ChatOpenAI(
                temperature=temperature,
                streaming=streaming,
                model=model or settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                openai_api_base=runtime_settings.get("openai_api_base", settings.OPENAI_API_BASE)
            )
        elif provider == "deepseek":
            return ChatDeepSeek(
                temperature=temperature,
                streaming=streaming,
                model=model or settings.DEEPSEEK_MODEL,
                api_key=settings.DEEPSEEK_API_KEY,
                api_base=runtime_settings.get("deepseek_api_base", settings.DEEPSEEK_API_BASE)
            )
        elif provider == "ollama":
            # Initialize Ollama model
            return OllamaLLM(
                model=model or settings.OLLAMA_MODEL,
                base_url=runtime_settings.get("ollama_api_base", settings.OLLAMA_API_BASE),
                temperature=temperature,
                streaming=streaming
            )
        # Add more providers here as needed
        # elif provider.lower() == "anthropic":
        #     return ChatAnthropic(...)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
