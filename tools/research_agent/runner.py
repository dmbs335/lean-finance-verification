from __future__ import annotations

import hashlib
from typing import Any

from tools.certifiable_alpha_interval.model import load_problem as load_alpha_interval
from tools.certifiable_alpha_interval.solver import solve as solve_alpha_interval
from tools.certificate_composition.model import load_problem as load_composition
from tools.certificate_composition.solver import solve as solve_composition
from tools.certifiability_crowding.model import load_scenario as load_crowding
from tools.certifiability_crowding.simulator import simulate as simulate_crowding
from tools.epistemic_event_study.analyzer import analyze as analyze_event_study
from tools.epistemic_event_study.model import load_plan as load_event_study
from tools.epistemic_liquidation.model import load_scenario as load_liquidation
from tools.epistemic_liquidation.simulator import simulate as simulate_liquidation
from tools.evidence_portfolio.model import load_problem as load_portfolio
from tools.evidence_portfolio.solver import solve as solve_portfolio
from tools.evidence_synth.canonical import canonical_bytes
from tools.fake_alpha_benchmark.model import load_benchmark
from tools.fake_alpha_benchmark.solver import solve as solve_fake_alpha

from .errors import ValidationError
from .model import Plan

REPORT_SCHEMA = "lfv-proof-carrying-research-agent-report-v4"
STAGES = [
    "registered", "alphaAudited", "alphaBounded", "portfolioSelected",
    "crowdingStressed", "liquidationStressed", "eventStudied",
    "pipelineComposed", "certified",
]
GATE_STAGE_ORDER = [
    ("alpha_audit", "alphaAudited"),
    ("alpha_interval", "alphaBounded"),
    ("portfolio", "portfolioSelected"),
    ("crowding", "crowdingStressed"),
    ("liquidation", "liquidationStressed"),
    ("event_study", "eventStudied"),
    ("composition", "pipelineComposed"),
]


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _completed_stages(gates: dict[str, dict[str, Any]]) -> list[str]:
    completed = ["registered"]
    for gate_id, stage in GATE_STAGE_ORDER:
        if not gates[gate_id]["passed"]:
            return completed
        completed.append(stage)
    completed.append("certified")
    return completed


def run(plan: Plan) -> dict[str, Any]:
    fake_alpha = solve_fake_alpha(load_benchmark(plan.analyses.fake_alpha_benchmark))
    alpha_interval = solve_alpha_interval(
        load_alpha_interval(plan.analyses.certifiable_alpha_interval)
    )
    portfolio = solve_portfolio(load_portfolio(plan.analyses.evidence_portfolio))
    crowding = simulate_crowding(
        load_crowding(plan.analyses.certifiability_crowding)
    )
    liquidation = simulate_liquidation(
        load_liquidation(plan.analyses.epistemic_liquidation)
    )
    event_study = analyze_event_study(
        load_event_study(plan.analyses.epistemic_event_study)
    )
    composition = solve_composition(
        load_composition(plan.analyses.certificate_composition)
    )

    selected_alpha = fake_alpha["synthesis"]["selected"]
    exact_recovery = bool(selected_alpha["verifies"]) and all(
        evaluation["exact_recovery"]
        for evaluation in selected_alpha["evaluations"]
    )
    alpha_gate = (
        exact_recovery
        if plan.gates.require_exact_alpha_recovery
        else True
    )

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

    event_effect = event_study["gates"]["event_effect"]
    event_accepted = event_study["status"] == "accepted-controlled"
    event_average = event_effect["average_did_bps_floor"]
    event_study_gate = (
        (event_accepted or not plan.gates.require_event_study_acceptance)
        and event_average >= plan.gates.minimum_event_study_average_did_bps
    )

    selected_composition = composition["synthesis"]["selected"]
    composition_verifies = bool(selected_composition["verifies"])
    composition_cost = selected_composition["cost"]
    composition_gate = (
        composition_verifies
        and composition_cost <= plan.gates.maximum_composition_evidence_cost
        if plan.gates.require_composition_verification
        else True
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
        "event_study": {
            "passed": event_study_gate,
            "accepted_controlled": event_accepted,
            "average_event_did_bps": event_average,
            "minimum_average_event_did_bps": (
                plan.gates.minimum_event_study_average_did_bps
            ),
            "pair_count": event_effect["did_denominator"],
        },
        "composition": {
            "passed": composition_gate,
            "verifies_global_claim": composition_verifies,
            "selected_channels": selected_composition["channels"],
            "selected_cost": composition_cost,
            "maximum_cost": plan.gates.maximum_composition_evidence_cost,
            "verification_required": (
                plan.gates.require_composition_verification
            ),
            "local_certificates_all_valid": composition[
                "local_certificates_all_valid_across_worlds"
            ],
            "local_summary_verifies": composition[
                "local_summary_only"
            ]["verifies"],
            "global_bundle_cost": composition[
                "global_bundle_only"
            ]["cost"],
        },
    }
    completed_stages = _completed_stages(gates)
    all_pass = completed_stages == STAGES
    artifact_digests = {
        "fake_alpha": _digest(fake_alpha),
        "alpha_interval": _digest(alpha_interval),
        "portfolio": _digest(portfolio),
        "crowding": _digest(crowding),
        "liquidation": _digest(liquidation),
        "event_study": _digest(event_study),
        "certificate_composition": _digest(composition),
    }
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "research_id": plan.research_id,
        "hypothesis": plan.hypothesis,
        "plan_sha256": plan.digest,
        "status": "certified-bounded" if all_pass else "rejected",
        "completed_stages": completed_stages,
        "artifact_sha256": artifact_digests,
        "gates": gates,
        "certificate": ({
            "plan_sha256": plan.digest,
            "artifact_sha256": artifact_digests,
            "completed_stages": STAGES,
            "residual_boundaries": [
                "finite declared distortions, models, strategies, and event pairs",
                "declared alpha envelopes, matching dimensions, and thresholds",
                "controlled allocation, capacity, impact, and withdrawal equations",
                "declared local certificate semantics and cross-boundary bindings",
                "no claim of real-market causal calibration",
            ],
        } if all_pass else None),
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
