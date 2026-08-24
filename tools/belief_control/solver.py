from __future__ import annotations

import hashlib
from fractions import Fraction
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Problem

REPORT_SCHEMA = "lfv-belief-state-robust-control-report-v1"


def _best_action(
    problem: Problem,
    support: tuple[str, ...],
) -> dict[str, Any]:
    rows = []
    for action in problem.actions:
        robust = min(action.hidden_values_bps[hidden] for hidden in support)
        robust -= action.execution_cost_bps
        rows.append({"action": action.id, "robust_net_value_bps": robust})
    selected = min(
        rows,
        key=lambda row: (-row["robust_net_value_bps"], row["action"]),
    )
    return {"support": list(support), "actions": rows, "selected": selected}


def _fraction(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def solve(problem: Problem) -> dict[str, Any]:
    prior_support = tuple(
        hidden for hidden, weight in problem.prior_weights.items() if weight > 0
    )
    prior_control = _best_action(problem, prior_support)
    prior_value = prior_control["selected"]["robust_net_value_bps"]
    observations: list[dict[str, Any]] = []
    for observation in problem.observations:
        unnormalized = {
            hidden: problem.prior_weights[hidden]
            * observation.likelihood_weights[hidden]
            for hidden in problem.prior_weights
        }
        total = sum(unnormalized.values())
        posterior = {
            hidden: _fraction(Fraction(weight, total))
            for hidden, weight in unnormalized.items()
        }
        support = tuple(
            hidden for hidden, weight in unnormalized.items() if weight > 0
        )
        control = _best_action(problem, support)
        observations.append({
            "observation": observation.id,
            "likelihood_weights": observation.likelihood_weights,
            "posterior_unnormalized": unnormalized,
            "posterior_probability": posterior,
            "posterior_support": list(support),
            "control": control,
        })
    guarantee = min(
        item["control"]["selected"]["robust_net_value_bps"]
        for item in observations
    )
    net_query_value = guarantee - problem.query_cost_bps
    robust_voi = net_query_value - prior_value
    decision = "acquireEvidence" if robust_voi > 0 else "actNow"
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "prior": {
            "weights": problem.prior_weights,
            "support": list(prior_support),
            "control": prior_control,
        },
        "observations": observations,
        "query": {
            "cost_bps": problem.query_cost_bps,
            "worst_post_observation_value_bps": guarantee,
            "net_post_query_value_bps": net_query_value,
            "robust_value_of_information_bps": robust_voi,
            "decision": decision,
        },
        "controlled_claims": {
            "posterior_weights_are_exact": True,
            "zero_likelihood_removes_support": all(
                all(
                    observation["posterior_unnormalized"][hidden] == 0
                    for hidden, likelihood in
                    observation["likelihood_weights"].items()
                    if likelihood == 0
                )
                for observation in observations
            ),
            "query_requires_positive_robust_voi": (
                decision != "acquireEvidence" or robust_voi > 0
            ),
        },
        "residual_boundaries": [
            "finite hidden states, values, and likelihood weights",
            "no transition dynamics or observation calibration",
            "query uses worst-case observations rather than probabilities",
            "no future-return or autonomous-trading claim",
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
            "belief-control report does not match exact recomputation"
        )
    return expected
