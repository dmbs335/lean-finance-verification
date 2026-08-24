from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json

from .errors import ValidationError

SCHEMA = "lfv-evidence-adjusted-portfolio-v1"
MAX_STRATEGIES = 20


@dataclass(frozen=True)
class Objective:
    raw_risk_penalty: int
    risk_penalty: int
    debt_penalty: int
    robustness_reward: int
    dependency_penalty: int


@dataclass(frozen=True)
class Strategy:
    id: str
    observed_alpha_bps: int
    certifiable_lower_bps: int
    risk_units: int
    evidence_debt: int
    robustness: int
    domains: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    selection_size: int
    objective: Objective
    strategies: tuple[Strategy, ...]


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def _natural(value: Any, path: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    if positive and value == 0:
        raise ValidationError(f"{path}: expected positive integer")
    return value


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path}: expected integer")
    return value


def load_problem(path: Path) -> Problem:
    raw = _object(load_json(path), "$")
    allowed = {
        "schema_version", "name", "selection_size", "objective", "strategies"
    }
    unknown = set(raw) - allowed
    if unknown:
        raise ValidationError(f"$: unknown fields: {sorted(unknown)}")
    if raw.get("schema_version") != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")

    objective_raw = _object(raw.get("objective"), "$.objective")
    objective_fields = {
        "raw_risk_penalty", "risk_penalty", "debt_penalty",
        "robustness_reward", "dependency_penalty",
    }
    if set(objective_raw) != objective_fields:
        raise ValidationError(
            "$.objective: fields must exactly match the objective schema"
        )
    objective = Objective(**{
        field: _natural(objective_raw[field], f"$.objective.{field}")
        for field in objective_fields
    })

    strategies: list[Strategy] = []
    strategies_raw = raw.get("strategies")
    if not isinstance(strategies_raw, list):
        raise ValidationError("$.strategies: expected array")
    for index, item in enumerate(strategies_raw):
        obj = _object(item, f"$.strategies[{index}]")
        strategy_id = _string(obj.get("id"), f"$.strategies[{index}].id")
        observed = _integer(
            obj.get("observed_alpha_bps"),
            f"$.strategies[{index}].observed_alpha_bps",
        )
        certifiable = _integer(
            obj.get("certifiable_lower_bps"),
            f"$.strategies[{index}].certifiable_lower_bps",
        )
        if certifiable > observed:
            raise ValidationError(
                f"$.strategies[{index}]: certifiable lower bound exceeds observed alpha"
            )
        domains_raw = obj.get("domains")
        if not isinstance(domains_raw, list) or not domains_raw or any(
            not isinstance(domain, str) or not domain for domain in domains_raw
        ):
            raise ValidationError(
                f"$.strategies[{index}].domains: expected non-empty string array"
            )
        domains = tuple(domains_raw)
        if len(set(domains)) != len(domains):
            raise ValidationError(
                f"$.strategies[{index}].domains: duplicates are not allowed"
            )
        strategies.append(
            Strategy(
                id=strategy_id,
                observed_alpha_bps=observed,
                certifiable_lower_bps=certifiable,
                risk_units=_natural(
                    obj.get("risk_units"), f"$.strategies[{index}].risk_units"
                ),
                evidence_debt=_natural(
                    obj.get("evidence_debt"),
                    f"$.strategies[{index}].evidence_debt",
                ),
                robustness=_natural(
                    obj.get("robustness"),
                    f"$.strategies[{index}].robustness",
                ),
                domains=domains,
                description=_string(
                    obj.get("description", strategy_id),
                    f"$.strategies[{index}].description",
                ),
            )
        )
    if len(strategies) < 2 or len(strategies) > MAX_STRATEGIES:
        raise ValidationError(
            f"$.strategies: expected between 2 and {MAX_STRATEGIES} strategies"
        )
    if len({strategy.id for strategy in strategies}) != len(strategies):
        raise ValidationError("$.strategies: ids must be unique")

    selection_size = _natural(
        raw.get("selection_size"), "$.selection_size", positive=True
    )
    if selection_size > len(strategies):
        raise ValidationError(
            "$.selection_size must not exceed the strategy count"
        )
    return Problem(
        source=path.resolve(),
        name=_string(raw.get("name"), "$.name"),
        selection_size=selection_size,
        objective=objective,
        strategies=tuple(strategies),
    )
