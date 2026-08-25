from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-anytime-policy-monitor-v1"
LEVELS = (
    "observe", "shadow", "recommend", "microAutonomy",
    "boundedAutonomy", "fallback", "revoked",
)
MAX_OBSERVATIONS = 10000
MAX_COMPONENTS = 32


@dataclass(frozen=True)
class Component:
    id: str
    bet: Fraction
    mixture_weight: Fraction


@dataclass(frozen=True)
class Observation:
    id: str
    observed_improvement_bps: int


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    null_mean_bps_max: int
    reward_bound_bps: int
    alpha: Fraction
    minimum_observations: int
    current_authority: str
    risk_ucb: int
    risk_budget: int
    model_shift: bool
    operational_breach: bool
    capital_caps: dict[str, int]
    components: tuple[Component, ...]
    observations: tuple[Observation, ...]


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


def _fraction(value: Any, path: str, *, positive: bool = False) -> Fraction:
    obj = _object(value, path)
    if set(obj) != {"numerator", "denominator"}:
        raise ValidationError(f"{path}: fields do not match")
    numerator = _natural(obj["numerator"], f"{path}.numerator")
    denominator = _natural(
        obj["denominator"], f"{path}.denominator", positive=True
    )
    result = Fraction(numerator, denominator)
    if positive and result <= 0:
        raise ValidationError(f"{path}: expected positive fraction")
    return result


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version", "name", "null_mean_bps_max",
        "reward_bound_bps", "alpha", "minimum_observations",
        "current_authority", "risk_ucb", "risk_budget", "model_shift",
        "operational_breach", "capital_caps", "components", "observations",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")
    bound = _natural(raw["reward_bound_bps"], "$.reward_bound_bps", positive=True)
    alpha = _fraction(raw["alpha"], "$.alpha", positive=True)
    if alpha >= 1:
        raise ValidationError("$.alpha: expected value below one")
    components_raw = raw["components"]
    if not isinstance(components_raw, list) or not 1 <= len(components_raw) <= MAX_COMPONENTS:
        raise ValidationError(f"$.components: expected 1..{MAX_COMPONENTS} entries")
    components: list[Component] = []
    for index, item in enumerate(components_raw):
        item_path = f"$.components[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "bet", "mixture_weight"}:
            raise ValidationError(f"{item_path}: fields do not match")
        bet = _fraction(obj["bet"], f"{item_path}.bet")
        if bet > 1:
            raise ValidationError(f"{item_path}.bet: expected value at most one")
        weight = _fraction(
            obj["mixture_weight"], f"{item_path}.mixture_weight", positive=True
        )
        components.append(Component(
            id=_string(obj["id"], f"{item_path}.id"),
            bet=bet,
            mixture_weight=weight,
        ))
    if len({component.id for component in components}) != len(components):
        raise ValidationError("$.components: ids must be unique")
    if sum((component.mixture_weight for component in components), Fraction(0, 1)) != 1:
        raise ValidationError("$.components: mixture weights must sum to one")
    observations_raw = raw["observations"]
    if not isinstance(observations_raw, list) or not 1 <= len(observations_raw) <= MAX_OBSERVATIONS:
        raise ValidationError(
            f"$.observations: expected 1..{MAX_OBSERVATIONS} entries"
        )
    null_mean = _integer(raw["null_mean_bps_max"], "$.null_mean_bps_max")
    observations: list[Observation] = []
    for index, item in enumerate(observations_raw):
        item_path = f"$.observations[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "observed_improvement_bps"}:
            raise ValidationError(f"{item_path}: fields do not match")
        observed = _integer(
            obj["observed_improvement_bps"],
            f"{item_path}.observed_improvement_bps",
        )
        centered = observed - null_mean
        if not -bound <= centered <= bound:
            raise ValidationError(
                f"{item_path}: centered observation exceeds registered bound"
            )
        observations.append(Observation(
            id=_string(obj["id"], f"{item_path}.id"),
            observed_improvement_bps=observed,
        ))
    if len({observation.id for observation in observations}) != len(observations):
        raise ValidationError("$.observations: ids must be unique")
    current = _string(raw["current_authority"], "$.current_authority")
    if current not in LEVELS:
        raise ValidationError("$.current_authority: unsupported level")
    caps_raw = _object(raw["capital_caps"], "$.capital_caps")
    if set(caps_raw) != set(LEVELS):
        raise ValidationError("$.capital_caps: keys must match authority levels")
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        null_mean_bps_max=null_mean,
        reward_bound_bps=bound,
        alpha=alpha,
        minimum_observations=_natural(
            raw["minimum_observations"], "$.minimum_observations", positive=True
        ),
        current_authority=current,
        risk_ucb=_natural(raw["risk_ucb"], "$.risk_ucb"),
        risk_budget=_natural(raw["risk_budget"], "$.risk_budget"),
        model_shift=_boolean(raw["model_shift"], "$.model_shift"),
        operational_breach=_boolean(
            raw["operational_breach"], "$.operational_breach"
        ),
        capital_caps={
            level: _natural(caps_raw[level], f"$.capital_caps.{level}")
            for level in LEVELS
        },
        components=tuple(components),
        observations=tuple(observations),
    )
