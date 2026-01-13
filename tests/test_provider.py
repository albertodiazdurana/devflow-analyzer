"""Tests for LLM provider factory."""

import os
from unittest.mock import patch, MagicMock

import pytest

from src.llm_provider import (
    Provider,
    ModelConfig,
    AVAILABLE_MODELS,
    get_available_models,
    get_model_config,
    check_provider_available,
    create_llm,
)


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_model_config_creation(self):
        """Test creating a ModelConfig."""
        config = ModelConfig(
            provider=Provider.ANTHROPIC,
            model_id="claude-sonnet-4-20250514",
            display_name="Claude Sonnet 4",
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        )
        assert config.provider == Provider.ANTHROPIC
        assert config.model_id == "claude-sonnet-4-20250514"
        assert config.cost_per_1k_input == 0.003

    def test_model_config_defaults(self):
        """Test default cost values."""
        config = ModelConfig(
            provider=Provider.OLLAMA,
            model_id="llama3",
            display_name="Llama 3",
        )
        assert config.cost_per_1k_input == 0.0
        assert config.cost_per_1k_output == 0.0


class TestAvailableModels:
    """Tests for model registry."""

    def test_available_models_not_empty(self):
        """Test that we have models registered."""
        assert len(AVAILABLE_MODELS) > 0

    def test_get_available_models(self):
        """Test getting list of model keys."""
        models = get_available_models()
        assert isinstance(models, list)
        assert "claude-sonnet" in models
        assert "gpt-4o" in models
        assert "ollama-llama3" in models

    def test_get_model_config_valid(self):
        """Test getting config for valid model."""
        config = get_model_config("claude-sonnet")
        assert config.provider == Provider.ANTHROPIC
        assert "claude" in config.model_id.lower()

    def test_get_model_config_invalid(self):
        """Test getting config for invalid model raises."""
        with pytest.raises(ValueError, match="Unknown model"):
            get_model_config("nonexistent-model")

    def test_all_models_have_required_fields(self):
        """Test all registered models have required fields."""
        for key, config in AVAILABLE_MODELS.items():
            assert config.provider is not None
            assert config.model_id is not None
            assert config.display_name is not None


class TestCheckProviderAvailable:
    """Tests for provider availability checking."""

    def test_anthropic_available_with_key(self):
        """Test Anthropic available when API key set."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
            available, message = check_provider_available(Provider.ANTHROPIC)
            assert available is True
            assert "configured" in message.lower()

    def test_anthropic_unavailable_without_key(self):
        """Test Anthropic unavailable without API key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
            # Need to clear the key
            env = os.environ.copy()
            env.pop("ANTHROPIC_API_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                available, message = check_provider_available(Provider.ANTHROPIC)
                assert available is False

    def test_anthropic_unavailable_with_placeholder(self):
        """Test Anthropic unavailable with placeholder key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "your_anthropic_key_here"}):
            available, message = check_provider_available(Provider.ANTHROPIC)
            assert available is False

    def test_openai_available_with_key(self):
        """Test OpenAI available when API key set."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
            available, message = check_provider_available(Provider.OPENAI)
            assert available is True

    def test_openai_unavailable_without_key(self):
        """Test OpenAI unavailable without API key."""
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            available, message = check_provider_available(Provider.OPENAI)
            assert available is False

    @patch("httpx.get")
    def test_ollama_available_when_running(self, mock_get):
        """Test Ollama available when server responds."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        available, message = check_provider_available(Provider.OLLAMA)
        assert available is True
        assert "running" in message.lower()

    @patch("httpx.get")
    def test_ollama_unavailable_when_not_running(self, mock_get):
        """Test Ollama unavailable when server not reachable."""
        mock_get.side_effect = Exception("Connection refused")

        available, message = check_provider_available(Provider.OLLAMA)
        assert available is False
        assert "not reachable" in message.lower()


class TestCreateLLM:
    """Tests for LLM creation."""

    def test_create_llm_invalid_model(self):
        """Test creating LLM with invalid model raises."""
        with pytest.raises(ValueError, match="Unknown model"):
            create_llm("nonexistent-model")

    @patch("src.llm_provider.check_provider_available")
    def test_create_llm_provider_unavailable(self, mock_check):
        """Test creating LLM when provider unavailable raises."""
        mock_check.return_value = (False, "API key not set")

        with pytest.raises(RuntimeError, match="not available"):
            create_llm("claude-sonnet")

    @patch("src.llm_provider.check_provider_available")
    @patch("src.llm_provider._create_anthropic")
    def test_create_llm_anthropic(self, mock_create, mock_check):
        """Test creating Anthropic LLM."""
        mock_check.return_value = (True, "OK")
        mock_llm = MagicMock()
        mock_create.return_value = mock_llm

        result = create_llm("claude-sonnet", temperature=0.5)

        mock_create.assert_called_once()
        assert result == mock_llm

    @patch("src.llm_provider.check_provider_available")
    @patch("src.llm_provider._create_openai")
    def test_create_llm_openai(self, mock_create, mock_check):
        """Test creating OpenAI LLM."""
        mock_check.return_value = (True, "OK")
        mock_llm = MagicMock()
        mock_create.return_value = mock_llm

        result = create_llm("gpt-4o", temperature=0.3)

        mock_create.assert_called_once()
        assert result == mock_llm

    @patch("src.llm_provider.check_provider_available")
    @patch("src.llm_provider._create_ollama")
    def test_create_llm_ollama(self, mock_create, mock_check):
        """Test creating Ollama LLM."""
        mock_check.return_value = (True, "OK")
        mock_llm = MagicMock()
        mock_create.return_value = mock_llm

        result = create_llm("ollama-llama3", temperature=0.8)

        mock_create.assert_called_once()
        assert result == mock_llm
