from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

SCHEMA = "lfv-certifiability-crowding-v1"
REPORT_SCHEMA = "lfv-certifiability-crowding-report-v1"


class CertifiabilityCrowdingValidationError(ValueError):
    """Raised when a lifecycle scenario or report is malformed."""


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CertifiabilityCrowdingValidationError(f"{path}: expected object")
    return value


def _identifier(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise CertifiabilityCrowdingValidationError(
            f"{path}: expected non-empty string"
        )
    return value


def _natural(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CertifiabilityCrowdingValidationError(
            f"{path}: expected non-negative integer"
        )
    return value


@dataclass(frozen=True)
class Strategy:
    id: str
    economic_alpha_bps: int
    initial_certifiability_bps: int
    evidence_upgrade_bps: int
    initial_capital: int
    allocator_sensitivity_bps: int
    capacity: int
    impact_scale_bps: int


@dataclass(frozen=True)
class Scenario:
    source: Path
    name: str
    strategies: tuple[Strategy, ...]


def load_scenario(path: Path) -> Scenario:
    raw = _object(load_json(path), "$")
    if set(raw) != {"schema_version", "name", "strategies"}:
        raise CertifiabilityCrowdingValidationError(
            "$: fields do not match schema"
        )
    if raw["schema_version"] != SCHEMA:
        raise CertifiabilityCrowdingValidationError("$: unsupported schema")
    strategies: list[Strategy] = []
    for index, item in enumerate(raw["strategies"]):
        obj = _object(item, f"$.strategies[{index}]")
        strategies.append(
            Strategy(
                id=_identifier(obj.get("id"), f"$.strategies[{index}].id"),
                economic_alpha_bps=_natural(
                    obj.get("economic_alpha_bps"),
                    f"$.strategies[{index}].economic_alpha_bps",
                ),
                initial_certifiability_bps=_natural(
                    obj.get("initial_certifiability_bps"),
                    f"$.strategies[{index}].initial_certifiability_bps",
                ),
                evidence_upgrade_bps=_natural(
                    obj.get("evidence_upgrade_bps"),
                    f"$.strategies[{index}].evidence_upgrade_bps",
                ),
                initial_capital=_natural(
                    obj.get("initial_capital"),
                    f"$.strategies[{index}].initial_capital",
                ),
                allocator_sensitivity_bps=_natural(
                    obj.get("allocator_sensitivity_bps"),
                    f"$.strategies[{index}].allocator_sensitivity_bps",
                ),
                capacity=_natural(
                    obj.get("capacity"),
                    f"$.strategies[{index}].capacity",
                ),
                impact_scale_bps=_natural(
                    obj.get("impact_scale_bps"),
                    f"$.strategies[{index}].impact_scale_bps",
                ),
            )
        )
    if not strategies or len({item.id for item in strategies}) != len(strategies):
        raise CertifiabilityCrowdingValidationError(
            "$.strategies: expected unique non-empty strategies"
        )
    if any(strategy.capacity == 0 for strategy in strategies):
        raise CertifiabilityCrowdingValidationError(
            "$.strategies: capacity must be positive"
        )
    return Scenario(
        source=path.resolve(),
        name=_identifier(raw["name"], "$.name"),
        strategies=tuple(strategies),
    )


def _impact_bps(strategy: Strategy, capital: int) -> int:
    return capital * strategy.impact_scale_bps // strategy.capacity


def _evaluate_strategy(strategy: Strategy) -> dict[str, Any]:
    before_certifiability = strategy.initial_certifiability_bps
    after_certifiability = min(
        10_000,
        before_certifiability + strategy.evidence_upgrade_bps,
    )
    capital_inflow = (
        strategy.evidence_upgrade_bps
        * strategy.allocator_sensitivity_bps
        * strategy.initial_capital
        // 100_000_000
    )
    before_capital = strategy.initial_capital
    after_capital = before_capital + capital_inflow
    before_impact = _impact_bps(strategy, before_capital)
    after_impact = _impact_bps(strategy, after_capital)
    before_deployable = strategy.economic_alpha_bps - before_impact
    after_deployable = strategy.economic_alpha_bps - after_impact

    if strategy.evidence_upgrade_bps > 0 and after_certifiability <= before_certifiability:
        raise CertifiabilityCrowdingValidationError(
            f"strategy {strategy.id}: capped certifiability prevents strict upgrade"
        )

    return {
        "id": strategy.id,
        "economic_alpha_bps": strategy.economic_alpha_bps,
        "before": {
            "certifiability_bps": before_certifiability,
            "capital": before_capital,
            "impact_bps": before_impact,
            "deployable_alpha_bps": before_deployable,
            "investable": before_deployable > 0,
        },
        "after": {
            "certifiability_bps": after_certifiability,
            "capital": after_capital,
            "impact_bps": after_impact,
            "deployable_alpha_bps": after_deployable,
            "investable": after_deployable > 0,
        },
        "capital_inflow": capital_inflow,
        "certifiability_increased": after_certifiability > before_certifiability,
        "capital_increased": after_capital > before_capital,
        "impact_increased": after_impact > before_impact,
        "deployable_alpha_decreased": after_deployable < before_deployable,
        "capacity_death": (
            strategy.economic_alpha_bps > 0 and after_deployable <= 0
        ),
        "certifiability_crowding_chain": (
            after_certifiability > before_certifiability
            and after_capital > before_capital
            and after_impact > before_impact
            and after_deployable < before_deployable
        ),
    }


def simulate(scenario: Scenario) -> dict[str, Any]:
    strategies = [_evaluate_strategy(strategy) for strategy in scenario.strategies]
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": scenario.name,
        "strategy_count": len(strategies),
        "capacity_death_count": sum(
            strategy["capacity_death"] for strategy in strategies
        ),
        "certifiability_crowding_count": sum(
            strategy["certifiability_crowding_chain"]
            for strategy in strategies
        ),
        "strategies": strategies,
        "interpretation": (
            "conditional lifecycle simulation; not an empirical market law"
        ),
    }
    report["report_sha256"] = hashlib.sha256(canonical_bytes(report)).hexdigest()
    return report


def verify(scenario: Scenario, report: Any) -> dict[str, Any]:
    expected = simulate(scenario)
    if report != expected:
        raise CertifiabilityCrowdingValidationError(
            "certifiability-crowding report does not match exact recomputation"
        )
    return expected
