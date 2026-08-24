from __future__ import annotations

import hashlib
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Scenario, Strategy

REPORT_SCHEMA = "lfv-certifiability-crowding-report-v2"


def _state(strategy: Strategy, confidence_bps: int) -> dict[str, int | bool]:
    allocation = (
        strategy.allocator_capacity_units * confidence_bps
    ) // 10000
    crowding_cost = (
        allocation * strategy.impact_scale_bps
    ) // strategy.strategy_capacity_units
    deployable = strategy.economic_alpha_bps - crowding_cost
    return {
        "confidence_bps": confidence_bps,
        "allocation_units": allocation,
        "crowding_cost_bps": crowding_cost,
        "deployable_alpha_bps": deployable,
        "investable": deployable > 0,
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
            int(after["allocation_units"]) - int(before["allocation_units"])
        )
        deployable_change = (
            int(after["deployable_alpha_bps"])
            - int(before["deployable_alpha_bps"])
        )
        paradox = knowledge_gain > 0 and deployable_change < 0
        law_holds = (
            int(after["allocation_units"])
            >= int(before["allocation_units"])
            and int(after["deployable_alpha_bps"])
            <= int(before["deployable_alpha_bps"])
        )
        epistemic_death = strategy.verified_certifiable_lower_bps <= 0
        capacity_death = (
            strategy.economic_alpha_bps > 0
            and int(after["deployable_alpha_bps"]) <= 0
        )
        death_modes: list[str] = []
        if epistemic_death:
            death_modes.append("epistemic")
        if capacity_death:
            death_modes.append("capacity")
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
            "epistemic_death_after_verification": epistemic_death,
            "capacity_death_after_verification": capacity_death,
            "alpha_death_modes_after_verification": death_modes,
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
                if int(row["after"]["deployable_alpha_bps"]) < 0
            ),
            "epistemic_death_count": sum(
                1 for row in rows
                if row["epistemic_death_after_verification"]
            ),
            "capacity_death_count": sum(
                1 for row in rows
                if row["capacity_death_after_verification"]
            ),
            "allocation_before_units": sum(
                int(row["before"]["allocation_units"]) for row in rows
            ),
            "allocation_after_units": sum(
                int(row["after"]["allocation_units"]) for row in rows
            ),
            "all_structural_laws_hold": all(
                row["structural_law_holds"] for row in rows
            ),
        },
        "interpretation": {
            "epistemic_death": (
                "the evidence-supported lower bound is nonpositive"
            ),
            "capacity_death": (
                "gross economic alpha is positive but modeled impact consumes "
                "the deployable edge"
            ),
            "ecological_decay": (
                "not simulated here; it requires the gross economic edge itself "
                "to change after market adaptation"
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
