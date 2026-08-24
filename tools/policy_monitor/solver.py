from __future__ import annotations

import hashlib
from fractions import Fraction
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Problem

REPORT_SCHEMA = "lfv-policy-monitor-report-v1"


def _fraction(value: Fraction) -> dict[str, int]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "floor": value.numerator // value.denominator,
    }


def _ceil(value: Fraction) -> int:
    return -((-value.numerator) // value.denominator)


def _next_level(current: str) -> str:
    order = [
        "observe", "shadow", "recommend", "microAutonomy",
        "boundedAutonomy",
    ]
    if current in {"boundedAutonomy", "fallback", "revoked"}:
        return current
    return order[order.index(current) + 1]


def solve(problem: Problem) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    weights: list[Fraction] = []
    contributions: list[Fraction] = []
    for record in problem.records:
        weight = Fraction(
            record.target_probability_ppm,
            record.behavior_probability_ppm,
        )
        residual = record.reward_bps - record.logged_action_model_bps
        contribution = Fraction(record.target_policy_model_bps, 1) + (
            weight * residual
        )
        weights.append(weight)
        contributions.append(contribution)
        rows.append({
            "id": record.id,
            "importance_weight": _fraction(weight),
            "reward_bps": record.reward_bps,
            "model_residual_bps": residual,
            "doubly_robust_contribution_bps": _fraction(contribution),
        })

    estimate = sum(contributions, Fraction(0, 1)) / len(contributions)
    improvement = estimate - problem.baseline_value_bps
    lower_exact = improvement - problem.confidence_radius_bps
    upper_exact = improvement + problem.confidence_radius_bps
    lower = lower_exact.numerator // lower_exact.denominator
    upper = _ceil(upper_exact)
    weight_sum = sum(weights, Fraction(0, 1))
    weight_square_sum = sum(
        (weight * weight for weight in weights), Fraction(0, 1)
    )
    if weight_square_sum <= 0:
        raise ValidationError("effective sample size denominator is zero")
    ess = weight_sum * weight_sum / weight_square_sum
    ess_passed = ess >= problem.minimum_effective_sample_size
    improvement_passed = lower >= problem.required_improvement_bps
    risk_passed = problem.risk_ucb <= problem.risk_budget
    eligible = (
        improvement_passed
        and ess_passed
        and risk_passed
        and not problem.model_shift
        and not problem.operational_breach
    )
    if problem.model_shift or problem.operational_breach:
        authority = "revoked"
        reason = "model shift or operational breach"
    elif eligible:
        authority = _next_level(problem.current_authority)
        reason = "off-policy lower bound, ESS, and risk gates passed"
    else:
        authority = problem.current_authority
        reason = "authority held pending stronger evidence"

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "record_count": len(rows),
        "records": rows,
        "off_policy": {
            "doubly_robust_value_bps": _fraction(estimate),
            "baseline_value_bps": problem.baseline_value_bps,
            "improvement_bps": _fraction(improvement),
            "confidence_radius_bps": problem.confidence_radius_bps,
            "improvement_interval_bps": [lower, upper],
            "required_improvement_bps": problem.required_improvement_bps,
            "improvement_passed": improvement_passed,
            "effective_sample_size": _fraction(ess),
            "minimum_effective_sample_size": (
                problem.minimum_effective_sample_size
            ),
            "effective_sample_size_passed": ess_passed,
        },
        "risk": {
            "risk_ucb": problem.risk_ucb,
            "risk_budget": problem.risk_budget,
            "passed": risk_passed,
        },
        "authority": {
            "current": problem.current_authority,
            "decision": authority,
            "capital_cap": problem.capital_caps[authority],
            "eligible": eligible,
            "reason": reason,
        },
        "assurance": {
            "arithmetic_exact": True,
            "confidence_sequence_coverage_assumed": True,
            "behavior_probabilities_required": True,
            "optional_stopping_validity_not_proved_in_lean": True,
        },
        "residual_boundaries": [
            "logged behavior and target probabilities are declared inputs",
            "confidence radius and risk upper bound are externally calibrated",
            "the exact checker does not prove statistical coverage",
            "no future-profitability or causal claim",
        ],
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "policy-monitor report does not match exact recomputation"
        )
    return expected
