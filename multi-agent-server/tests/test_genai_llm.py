"""
Unit tests for app.core.llm.genai_llm
Covers: _validate_config, get_model (caching), get_model_info, generate_genai_response
Uses: pytest fixtures + pytest-mock (mocker)
"""

import pytest
from app.exceptions.llm_excaptions import LLMConfigurationError, LLMInitializationError


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def manager(mocker):
    """
    Return a fresh GenAIModelManager instance for every test.
    The singleton is destroyed before each test so tests don't share state.
    """
    import app.core.llm.genai_llm as llm_module

    # Reset singleton
    llm_module.GenAIModelManager._instance = None

    manager = llm_module.GenAIModelManager()
    yield manager

    # Cleanup
    llm_module.GenAIModelManager._instance = None


@pytest.fixture()
def valid_config():
    """A valid config dict that _load_config would normally return."""
    return {
        "api_key": "AIzaSyA5ZanWx6O8u4woYUWKdEnrxG11pADEp0A",
        "model_name": "gemini-2.5-flash",
        "temperature": 0.0,
        "max_tokens": None,
    }


@pytest.fixture()
def mock_load_config(mocker, valid_config):
    """Patch _load_config so tests never hit the real config file."""
    return mocker.patch(
        "app.core.llm.genai_llm.GenAIModelManager._load_config",
        return_value=valid_config,
    )


@pytest.fixture()
def mock_chat(mocker):
    """Patch ChatGoogleGenerativeAI so tests never make real API calls."""
    return mocker.patch("app.core.llm.genai_llm.ChatGoogleGenerativeAI")


# ─────────────────────────────────────────────────────────────────────────────
# _validate_config
# ─────────────────────────────────────────────────────────────────────────────


class TestValidateConfig:

    def test_valid_config_does_not_raise(self, manager):
        """A full, correct config should pass validation silently."""
        manager._validate_config(
            api_key="AIzaSyA5ZanWx6O8u4woYUWKdEnrxG11pADEp0A",
            model_name="gemini-2.5-flash",
            temperature=0.0,
            max_tokens=None,
        )

    def test_empty_api_key_raises(self, manager):
        """Empty api_key must raise LLMConfigurationError."""
        with pytest.raises(LLMConfigurationError, match="api_key is not set"):
            manager._validate_config(
                api_key="",
                model_name="gemini-2.5-flash",
                temperature=0.0,
                max_tokens=None,
            )

    def test_empty_model_name_raises(self, manager):
        """Empty model_name must raise LLMConfigurationError."""
        with pytest.raises(LLMConfigurationError, match="model_name is not set"):
            manager._validate_config(
                api_key="AIzaSyA5ZanWx6O8u4woYUWKdEnrxG11pADEp0A",
                model_name="",
                temperature=0.0,
                max_tokens=None,
            )

    @pytest.mark.parametrize("bad_temp", [-0.1, 2.1, -10.0, 99.9])
    def test_out_of_range_temperature_raises(self, manager, bad_temp):
        """Temperature outside [0.0, 2.0] must raise LLMConfigurationError."""
        with pytest.raises(LLMConfigurationError, match="Temperature must be between"):
            manager._validate_config(
                api_key="AIzaSyA5ZanWx6O8u4woYUWKdEnrxG11pADEp0A",
                model_name="gemini-2.5-flash",
                temperature=bad_temp,
                max_tokens=None,
            )

    @pytest.mark.parametrize("valid_temp", [0.0, 0.5, 1.0, 2.0])
    def test_boundary_temperatures_pass(self, manager, valid_temp):
        """Temperatures at the boundaries 0.0 and 2.0 must be accepted."""
        manager._validate_config(
            api_key="AIzaSyA5ZanWx6O8u4woYUWKdEnrxG11pADEp0A",
            model_name="gemini-2.5-flash",
            temperature=valid_temp,
            max_tokens=None,
        )

    @pytest.mark.parametrize("bad_tokens", [0, -1, -100])
    def test_non_positive_max_tokens_raises(self, manager, bad_tokens):
        """max_tokens <= 0 must raise LLMConfigurationError."""
        with pytest.raises(
            LLMConfigurationError, match="max_tokens must be a positive"
        ):
            manager._validate_config(
                api_key="AIzaSyA5ZanWx6O8u4woYUWKdEnrxG11pADEp0A",
                model_name="gemini-2.5-flash",
                temperature=0.0,
                max_tokens=bad_tokens,
            )

    def test_positive_max_tokens_passes(self, manager):
        """A positive max_tokens must not raise."""
        manager._validate_config(
            api_key="AIzaSyA5ZanWx6O8u4woYUWKdEnrxG11pADEp0A",
            model_name="gemini-2.5-flash",
            temperature=0.0,
            max_tokens=512,
        )


# ─────────────────────────────────────────────────────────────────────────────
# get_model
# ─────────────────────────────────────────────────────────────────────────────


class TestGetModel:

    def test_returns_chat_instance(self, manager, mock_load_config, mock_chat):
        """get_model() should return the object created by ChatGoogleGenerativeAI."""
        fake_model = mock_chat.return_value  # the instance returned by the constructor

        result = manager.get_model()

        assert result is fake_model

    def test_same_args_returns_cached_model(self, manager, mock_load_config, mock_chat):
        """Calling get_model() twice with identical args must NOT create a second model."""
        first = manager.get_model()
        second = manager.get_model()

        assert first is second
        mock_chat.assert_called_once()  # constructor called only once

    def test_different_max_tokens_creates_new_model(
        self, manager, mock_load_config, mock_chat
    ):
        """Different max_tokens values must each get their own cached model."""
        mock_chat.side_effect = [
            pytest.importorskip("unittest.mock").MagicMock(),
            pytest.importorskip("unittest.mock").MagicMock(),
        ]

        m1 = manager.get_model(max_tokens=None)
        m2 = manager.get_model(max_tokens=256)

        assert m1 is not m2
        assert mock_chat.call_count == 2

    def test_different_streaming_creates_new_model(
        self, manager, mock_load_config, mock_chat
    ):
        """streaming=True vs streaming=False must produce separate cache entries."""
        from unittest.mock import MagicMock

        mock_chat.side_effect = [MagicMock(), MagicMock()]

        m1 = manager.get_model(streaming=False)
        m2 = manager.get_model(streaming=True)

        assert m1 is not m2
        assert mock_chat.call_count == 2

    def test_max_output_tokens_passed_when_set(
        self, manager, mock_load_config, mock_chat
    ):
        """When max_tokens is provided it must be forwarded to ChatGoogleGenerativeAI."""
        manager.get_model(max_tokens=512)

        _, kwargs = mock_chat.call_args
        assert kwargs.get("max_output_tokens") == 512

    def test_max_output_tokens_omitted_when_none(
        self, manager, mock_load_config, mock_chat
    ):
        """When max_tokens is None the key must NOT appear in kwargs."""
        manager.get_model(max_tokens=None)

        _, kwargs = mock_chat.call_args
        assert "max_output_tokens" not in kwargs

    def test_load_config_error_propagates(self, manager, mocker):
        """If _load_config raises, get_model must re-raise the exception."""
        mocker.patch(
            "app.core.llm.genai_llm.GenAIModelManager._load_config",
            side_effect=LLMConfigurationError("bad config"),
        )

        with pytest.raises(LLMConfigurationError, match="bad config"):
            manager.get_model()

    def test_chat_init_error_raises_initialization_error(
        self, manager, mock_load_config, mock_chat
    ):
        """If ChatGoogleGenerativeAI() raises, get_model must raise LLMInitializationError."""
        mock_chat.side_effect = Exception("network error")

        with pytest.raises(
            LLMInitializationError, match="Failed to create Google GenAI model"
        ):
            manager.get_model()


# ─────────────────────────────────────────────────────────────────────────────
# reset
# ─────────────────────────────────────────────────────────────────────────────


class TestReset:

    def test_reset_clears_cache(self, manager, mock_load_config, mock_chat):
        """After reset() a subsequent get_model() must build a brand-new model."""
        from unittest.mock import MagicMock

        mock_chat.side_effect = [MagicMock(), MagicMock()]

        first = manager.get_model()
        manager.reset()
        second = manager.get_model()

        assert first is not second
        assert mock_chat.call_count == 2


# ─────────────────────────────────────────────────────────────────────────────
# get_model_info
# ─────────────────────────────────────────────────────────────────────────────


class TestGetModelInfo:

    def test_empty_cache_returns_zero(self, manager, mocker):
        """Before any model is created, cached_models must be 0."""
        mocker.patch(
            "app.core.llm.genai_llm.get_config_value", return_value="gemini-2.5-flash"
        )

        info = manager.get_model_info()

        assert info["cached_models"] == 0
        assert info["configurations"] == []

    def test_info_counts_cached_models(
        self, manager, mock_load_config, mock_chat, mocker
    ):
        """get_model_info must reflect every distinct cached configuration."""
        from unittest.mock import MagicMock

        mock_chat.side_effect = [MagicMock(), MagicMock()]
        mocker.patch(
            "app.core.llm.genai_llm.get_config_value", return_value="gemini-2.5-flash"
        )

        manager.get_model(streaming=False)
        manager.get_model(streaming=True)

        info = manager.get_model_info()

        assert info["cached_models"] == 2
        assert len(info["configurations"]) == 2
        assert info["model_name"] == "gemini-2.5-flash"

    def test_info_configuration_keys(
        self, manager, mock_load_config, mock_chat, mocker
    ):
        """Each configuration entry must contain temperature, max_tokens, streaming."""
        mocker.patch(
            "app.core.llm.genai_llm.get_config_value", return_value="gemini-2.5-flash"
        )

        manager.get_model()

        info = manager.get_model_info()
        config_entry = info["configurations"][0]

        assert "temperature" in config_entry
        assert "max_tokens" in config_entry
        assert "streaming" in config_entry


# ─────────────────────────────────────────────────────────────────────────────
# generate_genai_response
# ─────────────────────────────────────────────────────────────────────────────


class TestGenerateGenaiResponse:

    def test_returns_response_content(
        self, manager, mock_load_config, mock_chat, mocker
    ):
        """generate_genai_response() should return response.content as a string."""
        from unittest.mock import MagicMock
        from app.core.llm.genai_llm import generate_genai_response

        fake_response = MagicMock()
        fake_response.content = "Hello there!"
        mock_model = MagicMock()
        mock_model.invoke.return_value = fake_response
        mock_chat.return_value = mock_model

        result = generate_genai_response("Say hi")

        assert result == "Hello there!"
        mock_model.invoke.assert_called_once_with("Say hi")

    def test_falls_back_to_str_when_no_content(
        self, manager, mock_load_config, mock_chat
    ):
        """If the response has no .content attribute, str() should be used instead."""
        from unittest.mock import MagicMock
        from app.core.llm.genai_llm import generate_genai_response

        mock_model = MagicMock()
        mock_model.invoke.return_value = "plain text"  # no .content
        mock_chat.return_value = mock_model

        result = generate_genai_response("Test")

        assert result == "plain text"

    def test_propagates_model_exception(self, manager, mock_load_config, mock_chat):
        """Exceptions raised during model.invoke() must bubble up unchanged."""
        from unittest.mock import MagicMock
        from app.core.llm.genai_llm import generate_genai_response

        mock_model = MagicMock()
        mock_model.invoke.side_effect = RuntimeError("API timeout")
        mock_chat.return_value = mock_model

        with pytest.raises(RuntimeError, match="API timeout"):
            generate_genai_response("This will fail")


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────


class TestSingleton:

    def test_same_instance_every_time(self, manager):
        """Two calls to GenAIModelManager() must return the exact same object."""
        from app.core.llm.genai_llm import GenAIModelManager

        a = GenAIModelManager()
        b = GenAIModelManager()

        assert a is b
