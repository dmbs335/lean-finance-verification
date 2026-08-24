from __future__ import annotations

import hashlib
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Scenario, Strategy

REPORT_SCHEMA = "lfv-certifiability-crowding-report-v1"


def _state(strategy: Strategy, confidence_bps: int) -> dict[str, int]:
    allocation = (
        strategy.allocator_capacity_units * confidence_bps
    ) // 10000
    crowding_cost = (
        allocation * strategy.impact_scale_bps
    ) // strategy.strategy_capacity_units
    return {
        "confidence_bps": confidence_bps,
        "allocation_units": allocation,
        "crowding_cost_bps": crowding_cost,
        "deployable_alpha_bps": strategy.economic_alpha_bps - crowding_cost,
    }


def simulate(scenario: Scenario) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for strategy in scenario.strategies:
        before = _state(strategy, strategy.initial_confidence_bps)
        after = _state(strategy, strategy.verified_confidence_bps)
        knowledge_gain = (
            strategy.verified_certifiable_lower_bps
            - strategy.initial_certifiable_lower_bps
        )
        allocation_change = (
            after["allocation_units"] - before["allocation_units"]
        )
        deployable_change = (
            after["deployable_alpha_bps"]
            - before["deployable_alpha_bps"]
        )
        paradox = knowledge_gain > 0 and deployable_change < 0
        law_holds = (
            after["allocation_units"] >= before["allocation_units"]
            and after["deployable_alpha_bps"]
            <= before["deployable_alpha_bps"]
        )
        rows.append({
            "strategy": strategy.id,
            "economic_alpha_bps": strategy.economic_alpha_bps,
            "initial_certifiable_lower_bps": (
                strategy.initial_certifiable_lower_bps
            ),
            "verified_certifiable_lower_bps": (
                strategy.verified_certifiable_lower_bps
            ),
            "knowledge_gain_bps": knowledge_gain,
            "before": before,
            "after": after,
            "allocation_change_units": allocation_change,
            "deployable_alpha_change_bps": deployable_change,
            "certifiability_crowding_paradox": paradox,
            "structural_law_holds": law_holds,
        })

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": scenario.name,
        "strategies": rows,
        "aggregate": {
            "strategy_count": len(rows),
            "paradox_count": sum(
                1 for row in rows
                if row["certifiability_crowding_paradox"]
            ),
            "negative_deployable_alpha_after_verification": sum(
                1 for row in rows
                if row["after"]["deployable_alpha_bps"] < 0
            ),
            "allocation_before_units": sum(
                row["before"]["allocation_units"] for row in rows
            ),
            "allocation_after_units": sum(
                row["after"]["allocation_units"] for row in rows
            ),
            "all_structural_laws_hold": all(
                row["structural_law_holds"] for row in rows
            ),
        },
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(scenario: Scenario, report: Any) -> dict[str, Any]:
    expected = simulate(scenario)
    if report != expected:
        raise ValidationError(
            "certifiability-crowding report does not match exact recomputation"
        )
    return expected
