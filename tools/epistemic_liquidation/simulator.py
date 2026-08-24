from __future__ import annotations

import hashlib
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Scenario, Strategy

REPORT_SCHEMA = "lfv-epistemic-liquidation-report-v2"


def _shock_map(scenario: Scenario) -> dict[str, int]:
    return {shock.domain: shock.severity_bps for shock in scenario.shocks}


def _evidence_withdrawal_bps(
    strategy: Strategy,
    shocks: dict[str, int],
) -> tuple[int, list[str]]:
    failed_domains: list[str] = []
    withdrawal_bps = 0
    for dependency in strategy.dependencies:
        severity = shocks.get(dependency.domain, 0)
        if severity > 0:
            failed_domains.append(dependency.domain)
            withdrawal_bps += (
                dependency.withdrawal_bps_at_full_shock * severity
            ) // 10000
    return min(10000, withdrawal_bps), sorted(failed_domains)


def _market_pressure(withdrawal: int, exposure_bps: int) -> int:
    return (withdrawal * exposure_bps) // 10000


def _market_impact(
    scenario: Scenario,
    pressure_units: int,
) -> int:
    return (
        pressure_units * scenario.market_impact_scale_bps
    ) // scenario.market_liquidity_units


def _dependency_domains(strategy: Strategy) -> set[str]:
    return {dependency.domain for dependency in strategy.dependencies}


def _dependency_overlap_bps(left: Strategy, right: Strategy) -> int:
    left_domains = _dependency_domains(left)
    right_domains = _dependency_domains(right)
    union = left_domains | right_domains
    if not union:
        return 0
    return (len(left_domains & right_domains) * 10000) // len(union)


def simulate(scenario: Scenario) -> dict[str, Any]:
    shocks = _shock_map(scenario)
    first_round: list[dict[str, Any]] = []
    initial_pressure = 0
    for strategy in scenario.strategies:
        withdrawal_bps, failed_domains = _evidence_withdrawal_bps(
            strategy, shocks
        )
        evidence_withdrawal = (
            strategy.capital_units * withdrawal_bps
        ) // 10000
        idiosyncratic_impact = (
            evidence_withdrawal * strategy.impact_scale_bps
        ) // strategy.liquidity_units
        initial_pressure += _market_pressure(
            evidence_withdrawal, strategy.market_exposure_bps
        )
        first_round.append(
            {
                "strategy": strategy.id,
                "dependency_domains": sorted(_dependency_domains(strategy)),
                "failed_domains": failed_domains,
                "evidence_withdrawal_bps": withdrawal_bps,
                "evidence_withdrawal_units": evidence_withdrawal,
                "idiosyncratic_impact_bps": idiosyncratic_impact,
            }
        )

    initial_market_impact = _market_impact(scenario, initial_pressure)
    strategy_by_id = {strategy.id: strategy for strategy in scenario.strategies}
    final_rows: list[dict[str, Any]] = []
    final_pressure = 0
    for row in first_round:
        strategy = strategy_by_id[row["strategy"]]
        mark_loss_bps = (
            initial_market_impact * strategy.market_exposure_bps
        ) // 10000
        excess_loss_bps = max(
            0, mark_loss_bps - strategy.margin_buffer_bps
        )
        margin_withdrawal = (
            strategy.capital_units
            * excess_loss_bps
            * strategy.margin_sensitivity_bps
        ) // 100_000_000
        total_withdrawal = min(
            strategy.capital_units,
            row["evidence_withdrawal_units"] + margin_withdrawal,
        )
        final_pressure += _market_pressure(
            total_withdrawal, strategy.market_exposure_bps
        )
        final_rows.append(
            {
                **row,
                "mark_loss_bps": mark_loss_bps,
                "margin_excess_bps": excess_loss_bps,
                "margin_withdrawal_units": margin_withdrawal,
                "total_withdrawal_units": total_withdrawal,
                "remaining_capital_units": (
                    strategy.capital_units - total_withdrawal
                ),
            }
        )

    final_market_impact = _market_impact(scenario, final_pressure)
    correlation_by_pair = {
        tuple(sorted((item.left, item.right))): item.correlation_bps
        for item in scenario.correlations
    }
    pairs: list[dict[str, Any]] = []
    for left_index, left in enumerate(final_rows):
        for right in final_rows[left_index + 1 :]:
            pair_key = tuple(sorted((left["strategy"], right["strategy"])))
            correlation = correlation_by_pair.get(pair_key)
            if correlation is None:
                continue
            left_strategy = strategy_by_id[left["strategy"]]
            right_strategy = strategy_by_id[right["strategy"]]
            shared_dependencies = sorted(
                _dependency_domains(left_strategy)
                & _dependency_domains(right_strategy)
            )
            overlap_bps = _dependency_overlap_bps(
                left_strategy, right_strategy
            )
            shared_failed = sorted(
                set(left["failed_domains"]) & set(right["failed_domains"])
            )
            synchronized = (
                left["evidence_withdrawal_units"] > 0
                and right["evidence_withdrawal_units"] > 0
                and bool(shared_failed)
            )
            low_return_correlation = (
                abs(correlation)
                <= scenario.low_return_correlation_threshold_bps
            )
            hidden_crowding = low_return_correlation and bool(shared_dependencies)
            pairs.append(
                {
                    "left": left["strategy"],
                    "right": right["strategy"],
                    "return_correlation_bps": correlation,
                    "low_return_correlation": low_return_correlation,
                    "shared_dependency_domains": shared_dependencies,
                    "dependency_overlap_bps": overlap_bps,
                    "hidden_epistemic_crowding": hidden_crowding,
                    "shared_failed_domains": shared_failed,
                    "synchronized_evidence_liquidation": synchronized,
                    "hidden_common_risk": (
                        synchronized and hidden_crowding
                    ),
                }
            )

    evidence_withdrawal_total = sum(
        row["evidence_withdrawal_units"] for row in final_rows
    )
    margin_withdrawal_total = sum(
        row["margin_withdrawal_units"] for row in final_rows
    )
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": scenario.name,
        "shocks": [
            {"domain": shock.domain, "severity_bps": shock.severity_bps}
            for shock in scenario.shocks
        ],
        "initial_market_impact_bps": initial_market_impact,
        "final_market_impact_bps": final_market_impact,
        "strategies": final_rows,
        "pairs": pairs,
        "aggregate": {
            "evidence_withdrawal_units": evidence_withdrawal_total,
            "margin_withdrawal_units": margin_withdrawal_total,
            "total_withdrawal_units": (
                evidence_withdrawal_total + margin_withdrawal_total
            ),
            "feedback_amplification_units": margin_withdrawal_total,
            "hidden_epistemic_crowding_pairs": sum(
                1 for pair in pairs
                if pair["hidden_epistemic_crowding"]
            ),
            "hidden_common_risk_pairs": sum(
                1 for pair in pairs if pair["hidden_common_risk"]
            ),
        },
        "interpretation": {
            "dependency_overlap": (
                "shared data, model, execution, or evidence domains; it is "
                "distinct from return correlation"
            ),
            "hidden_common_risk": (
                "low return correlation, shared dependency exposure, and "
                "synchronized first-round evidence withdrawal"
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
            "epistemic-liquidation report does not match exact recomputation"
        )
    return expected
