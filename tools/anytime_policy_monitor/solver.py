from __future__ import annotations

import hashlib
from fractions import Fraction
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .model import Problem

REPORT_SCHEMA = "lfv-anytime-policy-monitor-report-v1"


def _fraction(value: Fraction) -> dict[str, int]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "floor": value.numerator // value.denominator,
    }


def _next_level(current: str) -> str:
    order = [
        "observe", "shadow", "recommend", "microAutonomy",
        "boundedAutonomy",
    ]
    if current in {"boundedAutonomy", "fallback", "revoked"}:
        return current
    return order[order.index(current) + 1]


def solve(problem: Problem) -> dict[str, Any]:
    threshold = Fraction(problem.alpha.denominator, problem.alpha.numerator)
    wealth = {component.id: Fraction(1, 1) for component in problem.components}
    maximum_mixture = Fraction(1, 1)
    first_crossing: int | None = None
    rows: list[dict[str, Any]] = []
    for index, observation in enumerate(problem.observations, start=1):
        centered = observation.observed_improvement_bps - problem.null_mean_bps_max
        components: list[dict[str, Any]] = []
        for component in problem.components:
            factor = Fraction(1, 1) + (
                component.bet * Fraction(centered, problem.reward_bound_bps)
            )
            if factor < 0:
                raise AssertionError("validated betting factor became negative")
            wealth[component.id] *= factor
            components.append({
                "id": component.id,
                "bet": _fraction(component.bet),
                "mixture_weight": _fraction(component.mixture_weight),
                "factor": _fraction(factor),
                "wealth": _fraction(wealth[component.id]),
            })
        mixture = sum(
            (component.mixture_weight * wealth[component.id]
             for component in problem.components),
            Fraction(0, 1),
        )
        maximum_mixture = max(maximum_mixture, mixture)
        crossed = mixture >= threshold
        if crossed and first_crossing is None:
            first_crossing = index
        rows.append({
            "index": index,
            "id": observation.id,
            "observed_improvement_bps": observation.observed_improvement_bps,
            "centered_improvement_bps": centered,
            "components": components,
            "mixture_e_value": _fraction(mixture),
            "crossed_threshold": crossed,
        })
    current_mixture = Fraction(
        rows[-1]["mixture_e_value"]["numerator"],
        rows[-1]["mixture_e_value"]["denominator"],
    )
    evidence_passed = maximum_mixture >= threshold
    sample_passed = len(rows) >= problem.minimum_observations
    risk_passed = problem.risk_ucb <= problem.risk_budget
    eligible = (
        evidence_passed
        and sample_passed
        and risk_passed
        and not problem.model_shift
        and not problem.operational_breach
    )
    if problem.model_shift or problem.operational_breach:
        authority = "revoked"
        reason = "model shift or operational breach"
    elif eligible:
        authority = _next_level(problem.current_authority)
        reason = "anytime e-value, sample, and risk gates passed"
    else:
        authority = problem.current_authority
        reason = "authority held pending stronger anytime evidence"
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "null": {
            "conditional_mean_bps_at_most": problem.null_mean_bps_max,
            "centered_reward_bound_bps": problem.reward_bound_bps,
        },
        "alpha": _fraction(problem.alpha),
        "e_value_threshold": _fraction(threshold),
        "components": [
            {
                "id": component.id,
                "bet": _fraction(component.bet),
                "mixture_weight": _fraction(component.mixture_weight),
            }
            for component in problem.components
        ],
        "observations": rows,
        "anytime_evidence": {
            "current_e_value": _fraction(current_mixture),
            "maximum_e_value": _fraction(maximum_mixture),
            "first_crossing_observation": first_crossing,
            "crossed_threshold": evidence_passed,
            "all_prefixes_checked": True,
        },
        "gates": {
            "minimum_observations": problem.minimum_observations,
            "minimum_observations_passed": sample_passed,
            "e_value_passed": evidence_passed,
            "risk_ucb": problem.risk_ucb,
            "risk_budget": problem.risk_budget,
            "risk_passed": risk_passed,
            "model_shift": problem.model_shift,
            "operational_breach": problem.operational_breach,
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
            "bounded_observations_checked": True,
            "mixture_weights_sum_to_one": True,
            "nonnegative_betting_factors_checked": True,
            "conditional_null_mean_assumed": True,
            "optional_stopping_claim_conditional_on_e_validity": True,
            "measure_theoretic_ville_proof_not_formalized_in_lean": True,
        },
        "residual_boundaries": [
            "conditional null-mean and predictability assumptions are external",
            "reward clipping or bounding may introduce economic bias",
            "the Lean layer checks rational evidence and promotion gates",
            "no future-profitability or live-authority claim",
        ],
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        from .errors import ValidationError
        raise ValidationError(
            "anytime policy-monitor report does not match exact recomputation"
        )
    return expected
