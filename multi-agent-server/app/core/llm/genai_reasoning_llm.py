"""
Thread-safe Google GenAI reasoning model management using langchain_google_genai configured for GCP Vertex AI.

This module provides production-ready reasoning LLM model initialization with proper
singleton pattern, validation, error handling, and logging.
"""

import os
import threading
from typing import Optional

from app.configs.logging import get_logger
from app.configs.config_loader import get_config_value
from langchain_google_genai import ChatGoogleGenerativeAI
from app.exceptions.llm_excaptions import LLMConfigurationError, LLMInitializationError

# Configure module logger
logger = get_logger(__name__)


class GenAIReasoningModelManager:
    """
    Thread-safe singleton manager for Google GenAI reasoning models via Vertex AI.

    Manages ChatGoogleGenerativeAI reasoning model instances with thread safety,
    validation, and caching.
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
                self._models = {}
                self._initialized = True
                logger.info("GenAIReasoningModelManager initialized (Vertex AI mode)")

    def _load_config(self) -> dict:
        """
        Load and validate reasoning configuration from config.json.

        Returns:
            dict with keys: api_key, model_name, temperature, max_tokens, vertexai, project, location
        """
        try:
            logger.info("Loading Google GenAI reasoning settings from config for Vertex AI")
            api_key: str = (
                get_config_value("genai", "api_key", default="")
                or os.getenv("VERTEX_API_KEY", "")
                or os.getenv("GOOGLE_API_KEY", "")
            )
            model_name: str = get_config_value(
                "genai_reasoning", "model_name", default="gemini-2.5-pro"
            )
            temperature: float = float(
                get_config_value("genai_reasoning", "temperature", default=0.5)
            )
            max_tokens_raw = get_config_value(
                "genai_reasoning", "max_tokens", default=None
            )
            max_tokens: Optional[int] = (
                int(max_tokens_raw) if max_tokens_raw is not None else None
            )

            project_id: str = (
                get_config_value("vertex_ai", "project", default="lak-chemicals")
                or os.getenv("GCP_PROJECT_ID", "lak-chemicals")
            )
            location: str = (
                get_config_value("vertex_ai", "location", default="asia-south1")
                or os.getenv("GCP_REGION", "asia-south1")
            )
            vertexai: bool = bool(
                get_config_value("vertex_ai", "vertexai", default=True)
            )

            self._validate_config(api_key, model_name, temperature, max_tokens)

            logger.info("Google GenAI reasoning settings loaded and validated for Vertex AI")
            return {
                "api_key": api_key,
                "model_name": model_name,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "project": project_id,
                "location": location,
                "vertexai": vertexai,
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
        """
        if not api_key:
            raise LLMConfigurationError("genai.api_key is not set in config.json or environment")

        if not model_name:
            raise LLMConfigurationError(
                "genai_reasoning.model_name is not set in config.json"
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
            f"Using Google GenAI reasoning model: {model_name} | "
            f"temp={temperature} | max_tokens={max_tokens}"
        )

    def get_model(
        self,
        max_tokens: Optional[int] = None,
        streaming: bool = False,
    ) -> ChatGoogleGenerativeAI:
        """
        Get or create a ChatGoogleGenerativeAI reasoning model instance configured for GCP Vertex AI.
        """
        config = self._load_config()
        temperature: float = config["temperature"]

        resolved_max_tokens: Optional[int] = (
            max_tokens if max_tokens is not None else config["max_tokens"]
        )

        cache_key = (temperature, resolved_max_tokens, streaming)

        if cache_key not in self._models:
            with self._lock:
                if cache_key not in self._models:
                    try:
                        logger.info(
                            f"Creating ChatGoogleGenerativeAI reasoning model for Vertex AI (temp={temperature}, "
                            f"max_tokens={resolved_max_tokens}, streaming={streaming})"
                        )

                        self._models[cache_key] = ChatGoogleGenerativeAI(
                            model=config["model_name"],
                            google_api_key=config["api_key"],
                            temperature=temperature,
                            streaming=streaming,
                            max_output_tokens=resolved_max_tokens,
                            vertexai=config["vertexai"],
                            project=config["project"],
                            location=config["location"],
                        )
                        logger.info(
                            f"ChatGoogleGenerativeAI reasoning model created successfully: {config['model_name']}"
                        )
                    except LLMConfigurationError:
                        raise
                    except Exception as e:
                        logger.error(f"Failed to create Google GenAI reasoning model: {str(e)}")
                        raise LLMInitializationError(
                            f"Failed to create Google GenAI reasoning model: {str(e)}"
                        ) from e

        return self._models[cache_key]

    def reset(self) -> None:
        """
        Reset all cached models.
        """
        with self._lock:
            logger.warning("Resetting all Google GenAI reasoning models")
            self._models.clear()
            logger.info("All Google GenAI reasoning models reset successfully")

    def get_model_info(self) -> dict:
        """
        Get information about cached models.
        """
        with self._lock:
            model_name = get_config_value("genai_reasoning", "model_name", default=None)
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
_reasoning_manager = GenAIReasoningModelManager()


def get_genai_reasoning_model(
    max_tokens: Optional[int] = None,
    streaming: bool = False,
) -> ChatGoogleGenerativeAI:
    """
    Get a Google GenAI reasoning model instance (singleton per configuration).
    """
    return _reasoning_manager.get_model(max_tokens=max_tokens, streaming=streaming)


def reset_genai_reasoning_models() -> None:
    """
    Reset all cached Google GenAI reasoning models.
    """
    _reasoning_manager.reset()


def get_genai_reasoning_model_info() -> dict:
    """
    Get information about cached Google GenAI reasoning models.
    """
    return _reasoning_manager.get_model_info()
