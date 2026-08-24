from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json

from .errors import ValidationError

SCHEMA = "lfv-certifiability-crowding-v1"


@dataclass(frozen=True)
class Strategy:
    id: str
    economic_alpha_bps: int
    initial_certifiable_lower_bps: int
    verified_certifiable_lower_bps: int
    initial_confidence_bps: int
    verified_confidence_bps: int
    allocator_capacity_units: int
    strategy_capacity_units: int
    impact_scale_bps: int
    description: str


@dataclass(frozen=True)
class Scenario:
    source: Path
    name: str
    strategies: tuple[Strategy, ...]


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
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    if positive and value == 0:
        raise ValidationError(f"{path}: expected positive integer")
    return value


def _bps(value: Any, path: str) -> int:
    result = _natural(value, path)
    if result > 10000:
        raise ValidationError(f"{path}: expected basis points in [0, 10000]")
    return result


def load_scenario(path: Path) -> Scenario:
    raw = _object(load_json(path), "$")
    allowed = {"schema_version", "name", "strategies"}
    unknown = set(raw) - allowed
    if unknown:
        raise ValidationError(f"$: unknown fields: {sorted(unknown)}")
    if raw.get("schema_version") != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")

    strategies_raw = raw.get("strategies")
    if not isinstance(strategies_raw, list):
        raise ValidationError("$.strategies: expected array")
    strategies: list[Strategy] = []
    for index, item in enumerate(strategies_raw):
        obj = _object(item, f"$.strategies[{index}]")
        economic = _integer(
            obj.get("economic_alpha_bps"),
            f"$.strategies[{index}].economic_alpha_bps",
        )
        initial_lower = _integer(
            obj.get("initial_certifiable_lower_bps"),
            f"$.strategies[{index}].initial_certifiable_lower_bps",
        )
        verified_lower = _integer(
            obj.get("verified_certifiable_lower_bps"),
            f"$.strategies[{index}].verified_certifiable_lower_bps",
        )
        if initial_lower > verified_lower or verified_lower > economic:
            raise ValidationError(
                f"$.strategies[{index}]: certifiable lower bounds must increase "
                "without exceeding economic alpha"
            )
        initial_confidence = _bps(
            obj.get("initial_confidence_bps"),
            f"$.strategies[{index}].initial_confidence_bps",
        )
        verified_confidence = _bps(
            obj.get("verified_confidence_bps"),
            f"$.strategies[{index}].verified_confidence_bps",
        )
        if initial_confidence > verified_confidence:
            raise ValidationError(
                f"$.strategies[{index}]: verified confidence must not decline"
            )
        strategies.append(
            Strategy(
                id=_string(obj.get("id"), f"$.strategies[{index}].id"),
                economic_alpha_bps=economic,
                initial_certifiable_lower_bps=initial_lower,
                verified_certifiable_lower_bps=verified_lower,
                initial_confidence_bps=initial_confidence,
                verified_confidence_bps=verified_confidence,
                allocator_capacity_units=_natural(
                    obj.get("allocator_capacity_units"),
                    f"$.strategies[{index}].allocator_capacity_units",
                    positive=True,
                ),
                strategy_capacity_units=_natural(
                    obj.get("strategy_capacity_units"),
                    f"$.strategies[{index}].strategy_capacity_units",
                    positive=True,
                ),
                impact_scale_bps=_natural(
                    obj.get("impact_scale_bps"),
                    f"$.strategies[{index}].impact_scale_bps",
                ),
                description=_string(
                    obj.get("description", obj.get("id")),
                    f"$.strategies[{index}].description",
                ),
            )
        )
    if len(strategies) < 2:
        raise ValidationError("$.strategies: expected at least two strategies")
    if len({strategy.id for strategy in strategies}) != len(strategies):
        raise ValidationError("$.strategies: ids must be unique")
    return Scenario(
        source=path.resolve(),
        name=_string(raw.get("name"), "$.name"),
        strategies=tuple(strategies),
    )
