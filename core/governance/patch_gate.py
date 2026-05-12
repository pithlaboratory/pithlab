"""PatchGate — шлюз безопасности для патчей."""
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Literal

DecisionType = Literal["allow", "canary_only", "stop"]

@dataclass
class GateDecision:
    decision: DecisionType
    reason: str
    rollout_ring: str = "owner"
    traffic_share: float = 0.0

class PatchGate:
    def __init__(self, config_path: Path = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "autonomy.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.mode = self.config.get("mode", "suggest_only")
        self.thresholds = self.config.get("thresholds", {})
        self.safe_targets = self.config.get("safe_autopatch_targets", {})
        self.blocked_targets = self.config.get("blocked_targets", {})

    def evaluate(self, patch_candidate: dict) -> GateDecision:
        component = patch_candidate.get("component", "unknown")
        confidence = patch_candidate.get("confidence", 0.0)
        patch_type = patch_candidate.get("patch_type", "code")
        blocked_components = self.blocked_targets.get("components", [])
        if component in blocked_components:
            return GateDecision("stop", f"Component '{component}' is in blocked_targets")
        if self.mode == "manual_only":
            return GateDecision("stop", "System is in manual_only mode")
        min_conf = self.thresholds.get("min_confidence", 0.85)
        if confidence < min_conf:
            return GateDecision("stop", f"Confidence {confidence} < {min_conf}")
        safe_components = self.safe_targets.get("components", [])
        tools_allowed = self.safe_targets.get("tools_allowed", False)
        if component in safe_components:
            if patch_type == "tool" and not tools_allowed:
                return GateDecision("canary_only", "Tool changes require canary", "canary", 0.05)
            if self.mode == "safe_autopatch":
                return GateDecision("allow", "Safe autopatch approved", "owner", 0.0)
            else:
                return GateDecision("canary_only", "Suggested canary rollout", "canary", 0.05)
        if self.mode == "suggest_only":
            return GateDecision("canary_only", "Requires canary observation", "canary", 0.05)
        else:
            return GateDecision("stop", "Component not in safe_autopatch_targets")

patch_gate = PatchGate()
