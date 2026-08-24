from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json

from .errors import ValidationError

SCHEMA = "lfv-epistemic-liquidation-v1"


@dataclass(frozen=True)
class Dependency:
    domain: str
    withdrawal_bps_at_full_shock: int


@dataclass(frozen=True)
class Strategy:
    id: str
    capital_units: int
    liquidity_units: int
    impact_scale_bps: int
    market_exposure_bps: int
    margin_buffer_bps: int
    margin_sensitivity_bps: int
    dependencies: tuple[Dependency, ...]


@dataclass(frozen=True)
class Shock:
    domain: str
    severity_bps: int


@dataclass(frozen=True)
class Correlation:
    left: str
    right: str
    correlation_bps: int


@dataclass(frozen=True)
class Scenario:
    source: Path
    name: str
    low_return_correlation_threshold_bps: int
    market_liquidity_units: int
    market_impact_scale_bps: int
    strategies: tuple[Strategy, ...]
    shocks: tuple[Shock, ...]
    correlations: tuple[Correlation, ...]


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


def _bounded_bps(value: Any, path: str) -> int:
    result = _natural(value, path)
    if result > 10000:
        raise ValidationError(f"{path}: basis points must not exceed 10000")
    return result


def load_scenario(path: Path) -> Scenario:
    raw = _object(load_json(path), "$")
    if raw.get("schema_version") != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")

    strategies: list[Strategy] = []
    for index, item in enumerate(raw.get("strategies", [])):
        obj = _object(item, f"$.strategies[{index}]")
        dependencies: list[Dependency] = []
        for dependency_index, dependency_item in enumerate(
            obj.get("dependencies", [])
        ):
            dependency_obj = _object(
                dependency_item,
                f"$.strategies[{index}].dependencies[{dependency_index}]",
            )
            dependencies.append(
                Dependency(
                    domain=_string(
                        dependency_obj.get("domain"),
                        f"$.strategies[{index}].dependencies[{dependency_index}]"
                        ".domain",
                    ),
                    withdrawal_bps_at_full_shock=_bounded_bps(
                        dependency_obj.get("withdrawal_bps_at_full_shock"),
                        f"$.strategies[{index}].dependencies[{dependency_index}]"
                        ".withdrawal_bps_at_full_shock",
                    ),
                )
            )
        domains = [dependency.domain for dependency in dependencies]
        if len(set(domains)) != len(domains):
            raise ValidationError(
                f"$.strategies[{index}].dependencies: domains must be unique"
            )
        strategies.append(
            Strategy(
                id=_string(obj.get("id"), f"$.strategies[{index}].id"),
                capital_units=_natural(
                    obj.get("capital_units"),
                    f"$.strategies[{index}].capital_units",
                    positive=True,
                ),
                liquidity_units=_natural(
                    obj.get("liquidity_units"),
                    f"$.strategies[{index}].liquidity_units",
                    positive=True,
                ),
                impact_scale_bps=_natural(
                    obj.get("impact_scale_bps"),
                    f"$.strategies[{index}].impact_scale_bps",
                    positive=True,
                ),
                market_exposure_bps=_bounded_bps(
                    obj.get("market_exposure_bps"),
                    f"$.strategies[{index}].market_exposure_bps",
                ),
                margin_buffer_bps=_bounded_bps(
                    obj.get("margin_buffer_bps"),
                    f"$.strategies[{index}].margin_buffer_bps",
                ),
                margin_sensitivity_bps=_bounded_bps(
                    obj.get("margin_sensitivity_bps"),
                    f"$.strategies[{index}].margin_sensitivity_bps",
                ),
                dependencies=tuple(dependencies),
            )
        )
    if len(strategies) < 2 or len({item.id for item in strategies}) != len(
        strategies
    ):
        raise ValidationError(
            "$.strategies: expected at least two unique strategies"
        )
    strategy_ids = {strategy.id for strategy in strategies}

    shocks: list[Shock] = []
    for index, item in enumerate(raw.get("shocks", [])):
        obj = _object(item, f"$.shocks[{index}]")
        shocks.append(
            Shock(
                domain=_string(obj.get("domain"), f"$.shocks[{index}].domain"),
                severity_bps=_bounded_bps(
                    obj.get("severity_bps"),
                    f"$.shocks[{index}].severity_bps",
                ),
            )
        )
    if len({shock.domain for shock in shocks}) != len(shocks):
        raise ValidationError("$.shocks: domains must be unique")

    correlations: list[Correlation] = []
    seen_pairs: set[tuple[str, str]] = set()
    for index, item in enumerate(raw.get("return_correlations", [])):
        obj = _object(item, f"$.return_correlations[{index}]")
        left = _string(obj.get("left"), f"$.return_correlations[{index}].left")
        right = _string(
            obj.get("right"), f"$.return_correlations[{index}].right"
        )
        if left not in strategy_ids or right not in strategy_ids or left == right:
            raise ValidationError(
                f"$.return_correlations[{index}]: unknown or identical strategies"
            )
        pair = tuple(sorted((left, right)))
        if pair in seen_pairs:
            raise ValidationError(
                f"$.return_correlations[{index}]: duplicate pair"
            )
        seen_pairs.add(pair)
        correlation = obj.get("correlation_bps")
        if isinstance(correlation, bool) or not isinstance(correlation, int) or not (
            -10000 <= correlation <= 10000
        ):
            raise ValidationError(
                f"$.return_correlations[{index}].correlation_bps: "
                "expected integer in [-10000, 10000]"
            )
        correlations.append(Correlation(left, right, correlation))

    return Scenario(
        source=path.resolve(),
        name=_string(raw.get("name"), "$.name"),
        low_return_correlation_threshold_bps=_bounded_bps(
            raw.get("low_return_correlation_threshold_bps"),
            "$.low_return_correlation_threshold_bps",
        ),
        market_liquidity_units=_natural(
            raw.get("market_liquidity_units"),
            "$.market_liquidity_units",
            positive=True,
        ),
        market_impact_scale_bps=_natural(
            raw.get("market_impact_scale_bps"),
            "$.market_impact_scale_bps",
            positive=True,
        ),
        strategies=tuple(strategies),
        shocks=tuple(shocks),
        correlations=tuple(correlations),
    )
