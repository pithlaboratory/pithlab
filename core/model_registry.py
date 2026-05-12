"""Model Registry for Pith v5 — loads and serves model definitions from JSON."""
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path(__file__).with_name("model_registry.json")


@dataclass
class Pricing:
    input_usd: float
    output_usd: float
    cache_read_usd: float | None = None


@dataclass
class ModelRegistryEntry:
    key: str
    provider: str
    model_id: str
    role_tags: list[str]
    context_tokens: int | None = None
    max_output_tokens: int | None = None
    pricing: Pricing | None = None
    routing_priority: int | None = None
    enabled: bool = True


class ModelRegistry:
    """Registry for model definitions, loaded from JSON config."""

    def __init__(self, data: Dict[str, Any]):
        self.raw = data
        self.models: Dict[str, ModelRegistryEntry] = {}

        for key, cfg in data["models"].items():
            pricing_cfg = cfg.get("pricing_per_million")
            pricing = None
            if pricing_cfg:
                pricing = Pricing(
                    input_usd=pricing_cfg.get("input_usd", 0.0),
                    output_usd=pricing_cfg.get("output_usd", 0.0),
                    cache_read_usd=pricing_cfg.get("cache_read_usd"),
                )

            self.models[key] = ModelRegistryEntry(
                key=key,
                provider=cfg["provider"],
                model_id=cfg["model_id"],
                role_tags=cfg.get("role_tags", []),
                context_tokens=cfg.get("context_tokens"),
                max_output_tokens=cfg.get("max_output_tokens"),
                pricing=pricing,
                routing_priority=cfg.get("routing_priority"),
                enabled=cfg.get("enabled", True),
            )

    @classmethod
    def load(cls, path: Path = REGISTRY_PATH) -> "ModelRegistry":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        routing = data.get("routing", {})
        lanes = routing.get("lanes", {})

        logger.debug(f"[registry] loaded from: {path}")
        logger.debug(f"[registry] top-level keys: {sorted(data.keys())}")
        logger.debug(f"[registry] routing keys: {sorted(routing.keys()) if isinstance(routing, dict) else routing}")
        logger.debug(f"[registry] lanes keys: {sorted(lanes.keys()) if isinstance(lanes, dict) else lanes}")

        return cls(data)

    def get_model(self, key: str) -> ModelRegistryEntry:
        return self.models[key]

    def get_default(self, role: str) -> ModelRegistryEntry:
        key = self.raw["defaults"][role]
        return self.get_model(key)

    def get_lane_model(self, lane: str) -> ModelRegistryEntry:
        """
        Return model for a logical lane (chat_fast, code_paid, reasoner_free, etc.).
        Provides detailed diagnostics if lane or model key is missing.
        """
        routing = self.raw.get("routing", {})
        lanes = routing.get("lanes", {})

        # ✅ Проверка 1: есть ли lane вообще
        if lane not in lanes:
            available = ", ".join(sorted(lanes.keys())) if lanes else "<none>"
            raise KeyError(f"Unknown model lane: {lane!r}. Available lanes: {available}")

        key = lanes[lane]

        # ✅ Проверка 2: указывает ли lane на существующую модель
        if key not in self.models:
            available_models = ", ".join(sorted(self.models.keys()))
            raise KeyError(
                f"Lane {lane!r} points to unknown model key {key!r}. "
                f"Available models: {available_models}"
            )

        return self.get_model(key)

    def get_task_route(self, task_type: str) -> list[ModelRegistryEntry]:
        routing = self.raw.get("routing", {})
        task_routes = routing.get("task_routes", {})
        keys: List[str] = task_routes.get(task_type, [])
        if not keys:
            available = ", ".join(sorted(task_routes.keys())) if task_routes else "<none>"
            raise KeyError(f"Unknown task route: {task_type!r}. Available routes: {available}")
        return [self.get_model(k) for k in keys]