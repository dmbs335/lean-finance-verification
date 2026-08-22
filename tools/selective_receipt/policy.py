from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

from .errors import ValidationError

POLICY_SCHEMA = "lfv-selective-execution-policy-v1"


@dataclass(frozen=True)
class Policy:
    source: Path
    policy_id: str
    runner_id: str
    trust_domain: str
    action_universe: tuple[str, ...]
    forbidden_actions: tuple[str, ...]

    @property
    def universe_digest(self) -> str:
        return __import__("hashlib").sha256(
            canonical_bytes(list(self.action_universe))
        ).hexdigest()

    @property
    def policy_digest(self) -> str:
        payload = {
            "schema_version": POLICY_SCHEMA,
            "policy_id": self.policy_id,
            "runner_id": self.runner_id,
            "trust_domain": self.trust_domain,
            "action_universe": list(self.action_universe),
            "forbidden_actions": list(self.forbidden_actions),
        }
        return __import__("hashlib").sha256(canonical_bytes(payload)).hexdigest()


def _identifier(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def load_policy(path: Path) -> Policy:
    raw = load_json(path)
    if not isinstance(raw, dict):
        raise ValidationError("policy must be an object")
    if raw.get("schema_version") != POLICY_SCHEMA:
        raise ValidationError(f"unsupported policy schema")
    universe = tuple(raw.get("action_universe", []))
    forbidden = tuple(raw.get("forbidden_actions", []))
    if not universe or len(universe) & (len(universe) - 1):
        raise ValidationError("action universe must have power-of-two size")
    if any(not isinstance(item, str) or not item for item in universe):
        raise ValidationError("action universe entries must be non-empty strings")
    if len(set(universe)) != len(universe):
        raise ValidationError("action universe contains duplicates")
    if any(item not in set(universe) for item in forbidden):
        raise ValidationError("forbidden action is outside declared universe")
    if len(set(forbidden)) != len(forbidden) or not forbidden:
        raise ValidationError("forbidden actions must be unique and non-empty")
    return Policy(
        source=path.resolve(),
        policy_id=_identifier(raw.get("policy_id"), "$.policy_id"),
        runner_id=_identifier(raw.get("runner_id"), "$.runner_id"),
        trust_domain=_identifier(raw.get("trust_domain"), "$.trust_domain"),
        action_universe=universe,
        forbidden_actions=forbidden,
    )
