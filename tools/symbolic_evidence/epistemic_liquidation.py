from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

SCHEMA = "lfv-epistemic-liquidation-v1"
REPORT_SCHEMA = "lfv-epistemic-liquidation-report-v1"


class LiquidationValidationError(ValueError):
    """Raised when a liquidation scenario is malformed or a report is altered."""


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LiquidationValidationError(f"{path}: expected object")
    return value


def _identifier(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise LiquidationValidationError(f"{path}: expected non-empty string")
    return value


def _natural(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LiquidationValidationError(f"{path}: expected non-negative integer")
    return value


def _signed(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LiquidationValidationError(f"{path}: expected integer")
    return value


@dataclass(frozen=True)
class Strategy:
    id: str
    capital: int
    dependencies: tuple[str, ...]
    evidence_sensitivity_bps: int
    positions: dict[str, int]


@dataclass(frozen=True)
class Shock:
    id: str
    failed_domains: tuple[str, ...]
    severity_bps: int


@dataclass(frozen=True)
class PairCorrelation:
    left: str
    right: str
    return_correlation_bps: int


@dataclass(frozen=True)
class Scenario:
    source: Path
    name: str
    strategies: tuple[Strategy, ...]
    shocks: tuple[Shock, ...]
    correlations: tuple[PairCorrelation, ...]
    asset_liquidity: dict[str, int]


def load_scenario(path: Path) -> Scenario:
    raw = _object(load_json(path), "$")
    expected = {
        "schema_version",
        "name",
        "strategies",
        "shocks",
        "pair_correlations",
        "asset_liquidity",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise LiquidationValidationError("$: fields or schema do not match")

    liquidity_raw = _object(raw["asset_liquidity"], "$.asset_liquidity")
    liquidity = {
        _identifier(asset, "$.asset_liquidity key"): _natural(
            value, f"$.asset_liquidity.{asset}"
        )
        for asset, value in liquidity_raw.items()
    }
    if not liquidity or any(value == 0 for value in liquidity.values()):
        raise LiquidationValidationError(
            "$.asset_liquidity: expected positive capacities"
        )

    strategies: list[Strategy] = []
    for index, item in enumerate(raw["strategies"]):
        obj = _object(item, f"$.strategies[{index}]")
        dependencies = tuple(obj.get("dependencies", []))
        if not dependencies or any(
            not isinstance(value, str) or not value for value in dependencies
        ):
            raise LiquidationValidationError(
                f"$.strategies[{index}].dependencies: expected strings"
            )
        if len(set(dependencies)) != len(dependencies):
            raise LiquidationValidationError(
                f"$.strategies[{index}].dependencies: duplicates"
            )
        positions_raw = _object(
            obj.get("positions"), f"$.strategies[{index}].positions"
        )
        positions = {
            asset: _natural(value, f"$.strategies[{index}].positions.{asset}")
            for asset, value in positions_raw.items()
        }
        if not positions or any(asset not in liquidity for asset in positions):
            raise LiquidationValidationError(
                f"$.strategies[{index}].positions: unknown or empty asset set"
            )
        if sum(positions.values()) == 0:
            raise LiquidationValidationError(
                f"$.strategies[{index}].positions: zero gross position"
            )
        strategies.append(
            Strategy(
                id=_identifier(obj.get("id"), f"$.strategies[{index}].id"),
                capital=_natural(
                    obj.get("capital"), f"$.strategies[{index}].capital"
                ),
                dependencies=dependencies,
                evidence_sensitivity_bps=_natural(
                    obj.get("evidence_sensitivity_bps"),
                    f"$.strategies[{index}].evidence_sensitivity_bps",
                ),
                positions=positions,
            )
        )
    strategy_ids = {strategy.id for strategy in strategies}
    if not strategies or len(strategy_ids) != len(strategies):
        raise LiquidationValidationError(
            "$.strategies: expected unique non-empty strategies"
        )

    shocks: list[Shock] = []
    for index, item in enumerate(raw["shocks"]):
        obj = _object(item, f"$.shocks[{index}]")
        failed = tuple(obj.get("failed_domains", []))
        if not failed or any(not isinstance(value, str) or not value for value in failed):
            raise LiquidationValidationError(
                f"$.shocks[{index}].failed_domains: expected strings"
            )
        shocks.append(
            Shock(
                id=_identifier(obj.get("id"), f"$.shocks[{index}].id"),
                failed_domains=failed,
                severity_bps=_natural(
                    obj.get("severity_bps"),
                    f"$.shocks[{index}].severity_bps",
                ),
            )
        )
    if not shocks or len({shock.id for shock in shocks}) != len(shocks):
        raise LiquidationValidationError("$.shocks: expected unique non-empty shocks")

    correlations: list[PairCorrelation] = []
    seen_pairs: set[tuple[str, str]] = set()
    for index, item in enumerate(raw["pair_correlations"]):
        obj = _object(item, f"$.pair_correlations[{index}]")
        left = _identifier(obj.get("left"), f"$.pair_correlations[{index}].left")
        right = _identifier(obj.get("right"), f"$.pair_correlations[{index}].right")
        if left not in strategy_ids or right not in strategy_ids or left == right:
            raise LiquidationValidationError(
                f"$.pair_correlations[{index}]: invalid strategy pair"
            )
        pair = tuple(sorted((left, right)))
        if pair in seen_pairs:
            raise LiquidationValidationError(
                f"$.pair_correlations[{index}]: duplicate pair"
            )
        seen_pairs.add(pair)
        correlations.append(
            PairCorrelation(
                left=left,
                right=right,
                return_correlation_bps=_signed(
                    obj.get("return_correlation_bps"),
                    f"$.pair_correlations[{index}].return_correlation_bps",
                ),
            )
        )

    return Scenario(
        source=path.resolve(),
        name=_identifier(raw["name"], "$.name"),
        strategies=tuple(strategies),
        shocks=tuple(shocks),
        correlations=tuple(correlations),
        asset_liquidity=liquidity,
    )


def _jaccard_bps(left: tuple[str, ...], right: tuple[str, ...]) -> int:
    left_set = set(left)
    right_set = set(right)
    union = left_set | right_set
    if not union:
        return 0
    return (len(left_set & right_set) * 10_000) // len(union)


def _strategy_response(strategy: Strategy, shock: Shock) -> dict[str, Any]:
    failed = set(shock.failed_domains)
    affected = sorted(set(strategy.dependencies) & failed)
    dependency_share_bps = (
        len(affected) * 10_000 // len(strategy.dependencies)
        if affected
        else 0
    )
    confidence_loss_bps = (
        shock.severity_bps
        * dependency_share_bps
        * strategy.evidence_sensitivity_bps
        // 100_000_000
    )
    liquidation = strategy.capital * confidence_loss_bps // 10_000
    gross = sum(strategy.positions.values())
    sales = {
        asset: liquidation * weight // gross
        for asset, weight in strategy.positions.items()
    }
    allocated = sum(sales.values())
    remainder = liquidation - allocated
    if remainder and sales:
        first_asset = sorted(sales)[0]
        sales[first_asset] += remainder
    return {
        "strategy": strategy.id,
        "affected_domains": affected,
        "dependency_share_bps": dependency_share_bps,
        "confidence_loss_bps": confidence_loss_bps,
        "capital_before": strategy.capital,
        "capital_after": strategy.capital - liquidation,
        "liquidation": liquidation,
        "asset_sales": sales,
    }


def simulate(scenario: Scenario) -> dict[str, Any]:
    strategy_by_id = {strategy.id: strategy for strategy in scenario.strategies}
    pairs = []
    for correlation in scenario.correlations:
        left = strategy_by_id[correlation.left]
        right = strategy_by_id[correlation.right]
        overlap = _jaccard_bps(left.dependencies, right.dependencies)
        pairs.append(
            {
                "left": correlation.left,
                "right": correlation.right,
                "return_correlation_bps": correlation.return_correlation_bps,
                "evidence_overlap_bps": overlap,
                "hidden_epistemic_crowding": (
                    abs(correlation.return_correlation_bps) <= 1_000
                    and overlap > 0
                ),
            }
        )

    shocks = []
    for shock in scenario.shocks:
        responses = [
            _strategy_response(strategy, shock)
            for strategy in scenario.strategies
        ]
        asset_sales = {asset: 0 for asset in scenario.asset_liquidity}
        for response in responses:
            for asset, sale in response["asset_sales"].items():
                asset_sales[asset] += sale
        price_impact_bps = {
            asset: -(sale * 10_000 // scenario.asset_liquidity[asset])
            for asset, sale in asset_sales.items()
        }
        liquidating = {
            response["strategy"]
            for response in responses
            if response["liquidation"] > 0
        }
        synchronized_hidden_pairs = [
            {
                "left": pair["left"],
                "right": pair["right"],
            }
            for pair in pairs
            if pair["hidden_epistemic_crowding"]
            and pair["left"] in liquidating
            and pair["right"] in liquidating
        ]
        shocks.append(
            {
                "id": shock.id,
                "failed_domains": list(shock.failed_domains),
                "severity_bps": shock.severity_bps,
                "strategy_responses": responses,
                "total_liquidation": sum(
                    response["liquidation"] for response in responses
                ),
                "asset_sales": asset_sales,
                "price_impact_bps": price_impact_bps,
                "synchronized_hidden_pairs": synchronized_hidden_pairs,
            }
        )

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": scenario.name,
        "strategy_count": len(scenario.strategies),
        "pair_profiles": pairs,
        "shocks": shocks,
    }
    report["report_sha256"] = hashlib.sha256(canonical_bytes(report)).hexdigest()
    return report


def verify(scenario: Scenario, report: Any) -> dict[str, Any]:
    expected = simulate(scenario)
    if report != expected:
        raise LiquidationValidationError(
            "epistemic liquidation report does not match exact recomputation"
        )
    return expected
