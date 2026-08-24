from __future__ import annotations

import hashlib
from typing import Any

from tools.certifiable_alpha_interval.model import load_problem as load_alpha_interval
from tools.certifiable_alpha_interval.solver import solve as solve_alpha_interval
from tools.certifiability_crowding.model import load_scenario as load_crowding
from tools.certifiability_crowding.simulator import simulate as simulate_crowding
from tools.epistemic_liquidation.model import load_scenario as load_liquidation
from tools.epistemic_liquidation.simulator import simulate as simulate_liquidation
from tools.evidence_portfolio.model import load_problem as load_portfolio
from tools.evidence_portfolio.solver import solve as solve_portfolio
from tools.evidence_synth.canonical import canonical_bytes
from tools.fake_alpha_benchmark.model import load_benchmark
from tools.fake_alpha_benchmark.solver import solve as solve_fake_alpha

from .errors import ValidationError
from .model import Plan

REPORT_SCHEMA = "lfv-proof-carrying-research-agent-report-v2"
STAGES = [
    "registered", "alphaAudited", "alphaBounded", "portfolioSelected",
    "crowdingStressed", "liquidationStressed", "certified",
]


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def run(plan: Plan) -> dict[str, Any]:
    fake_alpha = solve_fake_alpha(
        load_benchmark(plan.analyses.fake_alpha_benchmark)
    )
    alpha_interval = solve_alpha_interval(
        load_alpha_interval(plan.analyses.certifiable_alpha_interval)
    )
    portfolio = solve_portfolio(
        load_portfolio(plan.analyses.evidence_portfolio)
    )
    crowding = simulate_crowding(
        load_crowding(plan.analyses.certifiability_crowding)
    )
    liquidation = simulate_liquidation(
        load_liquidation(plan.analyses.epistemic_liquidation)
    )

    selected_alpha = fake_alpha["synthesis"]["selected"]
    exact_recovery = bool(selected_alpha["verifies"]) and all(
        evaluation["exact_recovery"]
        for evaluation in selected_alpha["evaluations"]
    )
    alpha_gate = exact_recovery if plan.gates.require_exact_alpha_recovery else True

    selected_interval = alpha_interval["selected"]
    interval_lower, interval_upper = selected_interval["interval_bps"]
    interval_width = selected_interval["interval_width_bps"]
    positive_lower = interval_lower > 0
    alpha_interval_gate = (
        interval_width <= plan.gates.maximum_certifiable_interval_width_bps
        and (
            positive_lower
            or not plan.gates.require_positive_certifiable_lower_bound
        )
    )

    portfolio_gain = portfolio["adjusted_optimum_score_gain"]
    portfolio_gate = (
        portfolio_gain >= plan.gates.minimum_adjusted_portfolio_gain
    )
    crowding_laws = crowding["aggregate"]["all_structural_laws_hold"]
    crowding_gate = (
        (crowding_laws or not plan.gates.require_all_crowding_laws)
        and crowding["aggregate"]["paradox_count"]
        >= plan.gates.minimum_crowding_paradox_count
    )
    hidden_pairs = liquidation["aggregate"]["hidden_common_risk_pairs"]
    liquidation_gate = (
        hidden_pairs >= plan.gates.minimum_hidden_common_risk_pairs
    )

    gates = {
        "alpha_audit": {
            "passed": alpha_gate,
            "exact_recovery": exact_recovery,
            "selected_channels": selected_alpha["channels"],
            "selected_cost": selected_alpha["cost"],
        },
        "alpha_interval": {
            "passed": alpha_interval_gate,
            "selected_channels": selected_interval["channels"],
            "selected_cost": selected_interval["cost"],
            "interval_bps": [interval_lower, interval_upper],
            "interval_width_bps": interval_width,
            "maximum_width_bps": (
                plan.gates.maximum_certifiable_interval_width_bps
            ),
            "positive_lower_bound": positive_lower,
            "positive_lower_bound_required": (
                plan.gates.require_positive_certifiable_lower_bound
            ),
        },
        "portfolio": {
            "passed": portfolio_gate,
            "adjusted_score_gain": portfolio_gain,
            "raw_selection": portfolio["raw_optimum"]["strategies"],
            "adjusted_selection": portfolio[
                "evidence_adjusted_optimum"
            ]["strategies"],
        },
        "crowding": {
            "passed": crowding_gate,
            "all_structural_laws_hold": crowding_laws,
            "paradox_count": crowding["aggregate"]["paradox_count"],
        },
        "liquidation": {
            "passed": liquidation_gate,
            "hidden_common_risk_pairs": hidden_pairs,
            "final_market_impact_bps": liquidation[
                "final_market_impact_bps"
            ],
        },
    }
    all_pass = all(gate["passed"] for gate in gates.values())
    artifact_digests = {
        "fake_alpha": _digest(fake_alpha),
        "alpha_interval": _digest(alpha_interval),
        "portfolio": _digest(portfolio),
        "crowding": _digest(crowding),
        "liquidation": _digest(liquidation),
    }
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "research_id": plan.research_id,
        "hypothesis": plan.hypothesis,
        "plan_sha256": plan.digest,
        "status": "certified-bounded" if all_pass else "rejected",
        "completed_stages": STAGES if all_pass else STAGES[:-1],
        "artifact_sha256": artifact_digests,
        "gates": gates,
        "certificate": (
            {
                "plan_sha256": plan.digest,
                "artifact_sha256": artifact_digests,
                "completed_stages": STAGES,
                "residual_boundaries": [
                    "finite declared distortions, models, and strategies",
                    "declared statistical/model alpha envelopes",
                    "declared deployment-cost and portfolio-governance inputs",
                    "controlled allocation, capacity, and impact equations",
                    "no claim of real-market causal calibration",
                ],
            }
            if all_pass
            else None
        ),
    }
    report["report_sha256"] = _digest(report)
    return report


def verify(plan: Plan, report: Any) -> dict[str, Any]:
    expected = run(plan)
    if report != expected:
        raise ValidationError(
            "research-agent report does not match exact recomputation"
        )
    return expected
