"""
Thread-safe Google GenAI model management with comprehensive error handling and validation.

This module provides production-ready LLM model initialization with proper
singleton pattern, validation, error handling, and logging.
"""

import threading
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI

from app.configs.logging import get_logger
from app.configs.config_loader import get_config_value
from app.exceptions.llm_excaptions import LLMConfigurationError, LLMInitializationError

# Configure module logger
logger = get_logger(__name__)


class GenAIModelManager:
    """
    Thread-safe singleton manager for Google GenAI models.

    This class manages Google GenAI model instances with proper thread safety,
    validation, and error handling. Supports multiple models with different
    temperatures through a cache.
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._lock:
            if not self._initialized:
                self._models = {}  # Cache for models with different temperatures
                self._initialized = True
                logger.info("GenAIModelManager initialized")

    def _load_config(self) -> dict:
        """
        Load and validate Google GenAI configuration from config.json.

        Returns:
            dict with keys: api_key, model_name, temperature, max_tokens

        Raises:
            LLMConfigurationError: If required settings are missing or invalid
        """
        try:
            logger.info("Loading Google GenAI settings from config")
            api_key: str = get_config_value("genai", "api_key", default="")
            model_name: str = get_config_value(
                "genai_normal", "model_name", default="gemini-2.0-flash"
            )
            temperature: float = float(
                get_config_value("genai_normal", "temperature", default=0.0)
            )
            max_tokens_raw = get_config_value(
                "genai_normal", "max_tokens", default=None
            )
            max_tokens: Optional[int] = (
                int(max_tokens_raw) if max_tokens_raw is not None else None
            )

            self._validate_config(api_key, model_name, temperature, max_tokens)

            logger.info("Google GenAI settings loaded and validated")
            return {
                "api_key": api_key,
                "model_name": model_name,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        except LLMConfigurationError:
            raise
        except Exception as e:
            logger.error(f"Failed to load settings: {str(e)}")
            raise LLMConfigurationError(f"Failed to load settings: {str(e)}") from e

    def _validate_config(
        self,
        api_key: str,
        model_name: str,
        temperature: float,
        max_tokens: Optional[int],
    ) -> None:
        """
        Validate Google GenAI configuration values.

        Raises:
            LLMConfigurationError: If required settings are missing or invalid
        """
        if not api_key:
            raise LLMConfigurationError("genai.api_key is not set in config.json")

        if not model_name:
            raise LLMConfigurationError(
                "genai_normal.model_name is not set in config.json"
            )

        if len(api_key) < 10:
            logger.warning("genai.api_key seems too short – may be invalid")

        if not 0.0 <= temperature <= 2.0:
            raise LLMConfigurationError(
                f"Temperature must be between 0.0 and 2.0, got {temperature}"
            )

        if max_tokens is not None and max_tokens <= 0:
            raise LLMConfigurationError(
                f"max_tokens must be a positive integer, got {max_tokens}"
            )

        logger.debug(
            f"Using Google GenAI model: {model_name} | "
            f"temp={temperature} | max_tokens={max_tokens}"
        )

    def get_model(
        self,
        max_tokens: Optional[int] = None,
        streaming: bool = False,
    ) -> ChatGoogleGenerativeAI:
        """
        Get or create a Google GenAI model instance.

        Models are cached by their configuration (temperature, max_tokens, streaming).
        This ensures consistent behaviour and avoids creating duplicate instances.

        Args:
            max_tokens: Override max output tokens (None = use config value or model default)
            streaming: Whether to enable streaming responses

        Returns:
            Configured ChatGoogleGenerativeAI instance

        Raises:
            LLMConfigurationError: If configuration is invalid
            LLMInitializationError: If model creation fails
        """
        config = self._load_config()
        temperature: float = config["temperature"]

        # Caller-supplied max_tokens takes priority; fall back to config value
        resolved_max_tokens: Optional[int] = (
            max_tokens if max_tokens is not None else config["max_tokens"]
        )

        # Create cache key based on full resolved configuration
        cache_key = (temperature, resolved_max_tokens, streaming)

        if cache_key not in self._models:
            with self._lock:
                if cache_key not in self._models:
                    try:
                        logger.info(
                            f"Creating Google GenAI model (temp={temperature}, "
                            f"max_tokens={resolved_max_tokens}, streaming={streaming})"
                        )

                        model_kwargs = {
                            "model": config["model_name"],
                            "google_api_key": config["api_key"],
                            "temperature": temperature,
                            "streaming": streaming,
                        }

                        if resolved_max_tokens is not None:
                            model_kwargs["max_output_tokens"] = resolved_max_tokens

                        self._models[cache_key] = ChatGoogleGenerativeAI(**model_kwargs)
                        logger.info(
                            f"Google GenAI model created successfully: {config['model_name']}"
                        )
                    except LLMConfigurationError:
                        raise
                    except Exception as e:
                        logger.error(f"Failed to create Google GenAI model: {str(e)}")
                        raise LLMInitializationError(
                            f"Failed to create Google GenAI model: {str(e)}"
                        ) from e

        return self._models[cache_key]

    def reset(self) -> None:
        """
        Reset all cached models. Useful for testing or configuration changes.
        """
        with self._lock:
            logger.warning("Resetting all Google GenAI models")
            self._models.clear()
            logger.info("All Google GenAI models reset successfully")

    def get_model_info(self) -> dict:
        """
        Get information about cached models.

        Returns:
            Dictionary with model statistics
        """
        with self._lock:
            model_name = get_config_value("genai_normal", "model_name", default=None)
            return {
                "cached_models": len(self._models),
                "configurations": [
                    {
                        "temperature": temp,
                        "max_tokens": max_tok,
                        "streaming": stream,
                    }
                    for temp, max_tok, stream in self._models.keys()
                ],
                "model_name": model_name,
            }


# Global manager instance
_manager = GenAIModelManager()


# Public API - Backward compatible
def get_genai_model(
    max_tokens: Optional[int] = None,
    streaming: bool = True,
) -> ChatGoogleGenerativeAI:
    """
    Get a Google GenAI model instance (singleton per configuration).

    This is the main public API for getting Google GenAI models. Models are cached
    based on their configuration to ensure consistent behaviour.

    Args:
        max_tokens: Maximum tokens in response (None = model default)
        streaming: Whether to enable streaming responses

    Returns:
        Configured ChatGoogleGenerativeAI instance

    Raises:
        LLMConfigurationError: If configuration is invalid
        LLMInitializationError: If model creation fails

    Example:
        >>> model = get_genai_model()
        >>> response = model.invoke("Hello, how are you?")
    """
    return _manager.get_model(max_tokens=max_tokens, streaming=streaming)


def reset_genai_models() -> None:
    """
    Reset all cached Google GenAI models.

    Useful for testing or when configuration has changed.
    """
    _manager.reset()


def get_genai_model_info() -> dict:
    """
    Get information about cached Google GenAI models.

    Returns:
        Dictionary containing model statistics and configuration info
    """
    return _manager.get_model_info()


# Convenience function for generating responses
def generate_genai_response(
    prompt: str,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Generate a response using Google GenAI model.

    This is a convenience function that handles model retrieval and invocation.

    Args:
        prompt: The input prompt
        max_tokens: Maximum tokens in response

    Returns:
        Generated response text

    Raises:
        LLMConfigurationError: If configuration is invalid
        LLMInitializationError: If model creation fails
    """
    try:
        model = get_genai_model(max_tokens=max_tokens)
        logger.debug(f"Generating response for prompt: {prompt[:50]}...")
        response = model.invoke(prompt)
        logger.debug("Response generated successfully")
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        logger.error(f"Failed to generate response: {str(e)}")
        raise
