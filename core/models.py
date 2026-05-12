from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Единая конфигурация модели для Pith."""
    name: str
    provider: str
    model: str
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    temperature: float = 0.2


MODELS: dict[str, ModelConfig] = {
    "primary": ModelConfig(
        name="primary",
        provider="openrouter",
        model="qwen/qwen3-235b-a22b",
        max_input_tokens=131_072,
        max_output_tokens=4_096,
        temperature=0.2,
    ),
    "fast": ModelConfig(
        name="fast",
        provider="openrouter",
        model="mistralai/mistral-nemo",
        max_input_tokens=131_072,
        max_output_tokens=4_096,
        temperature=0.2,
    ),
    "coder": ModelConfig(
        name="coder",
        provider="openrouter",
        model="qwen/qwen3-coder",
        max_input_tokens=131_072,
        max_output_tokens=4_096,
        temperature=0.15,
    ),
    "thinking": ModelConfig(
        name="thinking",
        provider="openrouter",
        model="qwen/qwen3-235b-a22b-thinking-2507",
        max_input_tokens=131_072,
        max_output_tokens=4_096,
        temperature=0.1,
    ),
} 