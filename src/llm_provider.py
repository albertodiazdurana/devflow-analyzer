"""Provider-agnostic LLM factory."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Provider(Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"


@dataclass
class ModelConfig:
    """Configuration for an LLM model."""
    provider: Provider
    model_id: str
    display_name: str
    cost_per_1k_input: float = 0.0  # USD
    cost_per_1k_output: float = 0.0  # USD


# Available models registry
AVAILABLE_MODELS: dict[str, ModelConfig] = {
    # Anthropic
    "claude-sonnet": ModelConfig(
        provider=Provider.ANTHROPIC,
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
    ),
    "claude-haiku": ModelConfig(
        provider=Provider.ANTHROPIC,
        model_id="claude-haiku-4-20250514",
        display_name="Claude Haiku 4",
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
    ),
    # OpenAI
    "gpt-4o": ModelConfig(
        provider=Provider.OPENAI,
        model_id="gpt-4o",
        display_name="GPT-4o",
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
    ),
    "gpt-4o-mini": ModelConfig(
        provider=Provider.OPENAI,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
    ),
    # Ollama (local, no cost)
    "ollama-llama3": ModelConfig(
        provider=Provider.OLLAMA,
        model_id="llama3",
        display_name="Llama 3 (Local)",
    ),
    "ollama-mistral": ModelConfig(
        provider=Provider.OLLAMA,
        model_id="mistral",
        display_name="Mistral (Local)",
    ),
}


def get_available_models() -> list[str]:
    """Return list of available model keys."""
    return list(AVAILABLE_MODELS.keys())


def get_model_config(model_key: str) -> ModelConfig:
    """Get configuration for a model."""
    if model_key not in AVAILABLE_MODELS:
        raise ValueError(f"Unknown model: {model_key}. Available: {get_available_models()}")
    return AVAILABLE_MODELS[model_key]


def check_provider_available(provider: Provider) -> tuple[bool, str]:
    """Check if a provider is available (has API key or is running)."""
    if provider == Provider.ANTHROPIC:
        key = os.getenv("ANTHROPIC_API_KEY")
        if key and key != "your_anthropic_key_here":
            return True, "API key configured"
        return False, "ANTHROPIC_API_KEY not set"
    
    elif provider == Provider.OPENAI:
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_key_here":
            return True, "API key configured"
        return False, "OPENAI_API_KEY not set"
    
    elif provider == Provider.OLLAMA:
        # Check if Ollama is running
        try:
            import httpx
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            response = httpx.get(f"{base_url}/api/tags", timeout=2.0)
            if response.status_code == 200:
                return True, "Ollama running"
            return False, f"Ollama returned status {response.status_code}"
        except Exception as e:
            return False, f"Ollama not reachable: {e}"
    
    return False, "Unknown provider"


def create_llm(model_key: str, temperature: float = 0.7):
    """Create an LLM instance for the specified model.
    
    Args:
        model_key: Key from AVAILABLE_MODELS
        temperature: Sampling temperature (0.0 - 1.0)
    
    Returns:
        LangChain BaseChatModel instance
    """
    config = get_model_config(model_key)
    
    available, message = check_provider_available(config.provider)
    if not available:
        raise RuntimeError(f"Provider {config.provider.value} not available: {message}")
    
    if config.provider == Provider.ANTHROPIC:
        return _create_anthropic(config, temperature)
    elif config.provider == Provider.OPENAI:
        return _create_openai(config, temperature)
    elif config.provider == Provider.OLLAMA:
        return _create_ollama(config, temperature)
    else:
        raise ValueError(f"Unsupported provider: {config.provider}")


def _create_anthropic(config: ModelConfig, temperature: float):
    """Create Anthropic Claude model."""
    from langchain_anthropic import ChatAnthropic
    
    return ChatAnthropic(
        model=config.model_id,
        temperature=temperature,
        max_tokens=4096,
    )


def _create_openai(config: ModelConfig, temperature: float):
    """Create OpenAI model."""
    from langchain_openai import ChatOpenAI
    
    return ChatOpenAI(
        model=config.model_id,
        temperature=temperature,
        max_tokens=4096,
    )


def _create_ollama(config: ModelConfig, temperature: float):
    """Create Ollama local model."""
    from langchain_ollama import ChatOllama

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    return ChatOllama(
        model=config.model_id,
        temperature=temperature,
        base_url=base_url,
    )

