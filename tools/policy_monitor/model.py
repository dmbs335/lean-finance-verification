from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-policy-monitor-v1"
LEVELS = (
    "observe", "shadow", "recommend", "microAutonomy",
    "boundedAutonomy", "fallback", "revoked",
)


@dataclass(frozen=True)
class Record:
    id: str
    behavior_probability_ppm: int
    target_probability_ppm: int
    reward_bps: int
    logged_action_model_bps: int
    target_policy_model_bps: int


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    baseline_value_bps: int
    confidence_radius_bps: int
    required_improvement_bps: int
    minimum_effective_sample_size: int
    risk_ucb: int
    risk_budget: int
    current_authority: str
    model_shift: bool
    operational_breach: bool
    capital_caps: dict[str, int]
    records: tuple[Record, ...]


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path}: expected integer")
    return value


def _natural(value: Any, path: str, *, positive: bool = False) -> int:
    result = _integer(value, path)
    if result < 0 or (positive and result == 0):
        qualifier = "positive" if positive else "non-negative"
        raise ValidationError(f"{path}: expected {qualifier} integer")
    return result


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path}: expected boolean")
    return value


def _probability(value: Any, path: str) -> int:
    result = _natural(value, path, positive=True)
    if result > 1_000_000:
        raise ValidationError(f"{path}: probability exceeds one million ppm")
    return result


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version", "name", "baseline_value_bps",
        "confidence_radius_bps", "required_improvement_bps",
        "minimum_effective_sample_size", "risk_ucb", "risk_budget",
        "current_authority", "model_shift", "operational_breach",
        "capital_caps", "records",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")
    records_raw = raw["records"]
    if not isinstance(records_raw, list) or not records_raw:
        raise ValidationError("$.records: expected non-empty array")
    records: list[Record] = []
    for index, item in enumerate(records_raw):
        item_path = f"$.records[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {
            "id", "behavior_probability_ppm", "target_probability_ppm",
            "reward_bps", "logged_action_model_bps",
            "target_policy_model_bps",
        }:
            raise ValidationError(f"{item_path}: fields do not match")
        records.append(Record(
            id=_string(obj["id"], f"{item_path}.id"),
            behavior_probability_ppm=_probability(
                obj["behavior_probability_ppm"],
                f"{item_path}.behavior_probability_ppm",
            ),
            target_probability_ppm=_probability(
                obj["target_probability_ppm"],
                f"{item_path}.target_probability_ppm",
            ),
            reward_bps=_integer(obj["reward_bps"], f"{item_path}.reward_bps"),
            logged_action_model_bps=_integer(
                obj["logged_action_model_bps"],
                f"{item_path}.logged_action_model_bps",
            ),
            target_policy_model_bps=_integer(
                obj["target_policy_model_bps"],
                f"{item_path}.target_policy_model_bps",
            ),
        ))
    if len({record.id for record in records}) != len(records):
        raise ValidationError("$.records: ids must be unique")
    current = _string(raw["current_authority"], "$.current_authority")
    if current not in LEVELS:
        raise ValidationError("$.current_authority: unsupported level")
    caps_raw = _object(raw["capital_caps"], "$.capital_caps")
    if set(caps_raw) != set(LEVELS):
        raise ValidationError("$.capital_caps: keys must match authority levels")
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        baseline_value_bps=_integer(
            raw["baseline_value_bps"], "$.baseline_value_bps"
        ),
        confidence_radius_bps=_natural(
            raw["confidence_radius_bps"], "$.confidence_radius_bps"
        ),
        required_improvement_bps=_integer(
            raw["required_improvement_bps"], "$.required_improvement_bps"
        ),
        minimum_effective_sample_size=_natural(
            raw["minimum_effective_sample_size"],
            "$.minimum_effective_sample_size",
            positive=True,
        ),
        risk_ucb=_natural(raw["risk_ucb"], "$.risk_ucb"),
        risk_budget=_natural(raw["risk_budget"], "$.risk_budget"),
        current_authority=current,
        model_shift=_boolean(raw["model_shift"], "$.model_shift"),
        operational_breach=_boolean(
            raw["operational_breach"], "$.operational_breach"
        ),
        capital_caps={
            level: _natural(caps_raw[level], f"$.capital_caps.{level}")
            for level in LEVELS
        },
        records=tuple(records),
    )
