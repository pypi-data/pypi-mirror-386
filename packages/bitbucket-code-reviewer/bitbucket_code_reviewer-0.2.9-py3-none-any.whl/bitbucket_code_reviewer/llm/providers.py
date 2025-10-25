"""LLM provider abstractions for different LLM services."""

from abc import ABC, abstractmethod

from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI

from ..core.config import get_app_config
from ..core.models import LLMProvider, ReviewConfig


class LLMProviderBase(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: ReviewConfig):
        """Initialize the LLM provider.

        Args:
            config: Review configuration
        """
        self.config = config
        self.app_config = get_app_config()

    @abstractmethod
    def get_language_model(self) -> BaseLanguageModel:
        """Get the LangChain language model instance.

        Returns:
            Configured language model
        """
        pass

    @abstractmethod
    def validate_config(self) -> None:
        """Validate that the provider configuration is correct.

        Raises:
            ValueError: If configuration is invalid
        """
        pass


class OpenAIProvider(LLMProviderBase):
    """OpenAI LLM provider."""

    def validate_config(self) -> None:
        """Validate OpenAI configuration."""
        if not self.app_config.openai_api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable."
            )

        # Validate model name - include GPT-4 and GPT-5 models
        valid_openai_models = [
            # GPT-4 models
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            # GPT-5 base models
            "gpt-5",
            "gpt-5-2025-08-07",
            "gpt-5-chat-latest",
            "gpt-5-codex",
            # GPT-5 mini models
            "gpt-5-mini",
            "gpt-5-mini-2025-08-07",
            # GPT-5 nano models
            "gpt-5-nano",
            "gpt-5-nano-2025-08-07",
            # GPT-5 pro models
            "gpt-5-pro",
            "gpt-5-pro-2025-10-06",
        ]

        if self.config.model_name not in valid_openai_models:
            raise ValueError(
                f"Invalid OpenAI model: {self.config.model_name}. "
                f"Valid models: {', '.join(valid_openai_models)}"
            )

    def get_language_model(self) -> BaseLanguageModel:
        """Get OpenAI language model instance.

        Returns:
            ChatOpenAI instance
        """
        # Enable Responses API for GPT-5 models to access reasoning tokens
        kwargs = {
            "model_name": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "openai_api_key": self.app_config.openai_api_key,
        }
        
        # Enable Responses API for GPT-5 models
        if self.config.model_name.startswith("gpt-5"):
            kwargs["use_responses_api"] = True
            # Only request reasoning summary for non-codex models
            # Codex uses Responses API but doesn't support reasoning summary
            if "codex" not in self.config.model_name:
                kwargs["reasoning"] = {"summary": "auto"}
        
        return ChatOpenAI(**kwargs)


class XAIProvider(LLMProviderBase):
    """xAI LLM provider (formerly Grok)."""

    def validate_config(self) -> None:
        """Validate xAI configuration."""
        if not self.app_config.grok_api_key:
            raise ValueError(
                "xAI API key is required. Set GROK_API_KEY environment variable."
            )

        # Valid xAI models
        valid_grok_models = [
            "grok-4-0709",
            "grok-4-0709-eu",
            "grok-code-fast-1",
        ]

        if self.config.model_name not in valid_grok_models:
            raise ValueError(
                f"Invalid xAI model: {self.config.model_name}. "
                f"Valid models: {', '.join(valid_grok_models)}"
            )

    def get_language_model(self) -> BaseLanguageModel:
        """Get xAI language model instance.

        Returns:
            ChatOpenAI instance (Grok uses OpenAI-compatible API)
        """
        # xAI uses OpenAI-compatible API format
        return ChatOpenAI(
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            openai_api_key=self.app_config.grok_api_key,
            openai_api_base="https://api.x.ai/v1",  # Grok API endpoint
        )


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create_provider(config: ReviewConfig) -> LLMProviderBase:
        """Create an LLM provider instance.

        Args:
            config: Review configuration

        Returns:
            Configured LLM provider instance

        Raises:
            ValueError: If provider is not supported
        """
        if config.llm_provider == LLMProvider.OPENAI:
            provider = OpenAIProvider(config)
        elif config.llm_provider == LLMProvider.XAI:
            provider = XAIProvider(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")

        provider.validate_config()
        return provider


def get_language_model(config: ReviewConfig) -> BaseLanguageModel:
    """Get a configured language model instance.

    Args:
        config: Review configuration

    Returns:
        Configured language model
    """
    provider = LLMProviderFactory.create_provider(config)
    return provider.get_language_model()
