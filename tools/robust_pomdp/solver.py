from __future__ import annotations

import hashlib
from fractions import Fraction
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Action, Problem

REPORT_SCHEMA = "lfv-robust-pomdp-bellman-report-v1"


def _fraction(value: Fraction) -> dict[str, int]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "floor": value.numerator // value.denominator,
    }


def _action_value(
    problem: Problem,
    action: Action,
    previous: dict[str, Fraction],
) -> dict[str, Any]:
    discount = Fraction(
        problem.discount_numerator,
        problem.discount_denominator,
    )
    model_values: dict[str, Fraction] = {}
    model_rows: list[dict[str, Any]] = []
    for model in problem.models:
        branches = action.transitions[model]
        total_weight = sum(branch.weight for branch in branches)
        continuation = sum(
            (
                branch.weight * previous[branch.next_belief]
                for branch in branches
            ),
            Fraction(0, 1),
        ) / total_weight
        immediate = Fraction(
            action.reward_bps[model] - action.execution_cost_bps,
            1,
        )
        q_value = immediate + discount * continuation
        model_values[model] = q_value
        model_rows.append({
            "model": model,
            "immediate_net_bps": _fraction(immediate),
            "continuation_bps": _fraction(continuation),
            "q_value_bps": _fraction(q_value),
            "branches": [
                {
                    "next_belief": branch.next_belief,
                    "weight": branch.weight,
                    "previous_value_bps": _fraction(
                        previous[branch.next_belief]
                    ),
                }
                for branch in branches
            ],
        })
    robust_value = min(model_values.values())
    worst_models = sorted(
        model for model, value in model_values.items()
        if value == robust_value
    )
    return {
        "action": action.id,
        "execution_cost_bps": action.execution_cost_bps,
        "models": model_rows,
        "robust_value_bps": _fraction(robust_value),
        "worst_case_models": worst_models,
    }


def solve(problem: Problem) -> dict[str, Any]:
    previous = {belief.id: Fraction(0, 1) for belief in problem.beliefs}
    layers: list[dict[str, Any]] = [{
        "horizon": 0,
        "beliefs": {
            belief.id: {
                "selected_action": None,
                "robust_value_bps": _fraction(Fraction(0, 1)),
                "actions": [],
            }
            for belief in problem.beliefs
        },
    }]
    for horizon in range(1, problem.horizon + 1):
        current: dict[str, Fraction] = {}
        belief_rows: dict[str, Any] = {}
        for belief in problem.beliefs:
            action_rows = [
                _action_value(problem, action, previous)
                for action in belief.actions
            ]
            selected = min(
                action_rows,
                key=lambda row: (
                    -Fraction(
                        row["robust_value_bps"]["numerator"],
                        row["robust_value_bps"]["denominator"],
                    ),
                    row["action"],
                ),
            )
            value = Fraction(
                selected["robust_value_bps"]["numerator"],
                selected["robust_value_bps"]["denominator"],
            )
            current[belief.id] = value
            belief_rows[belief.id] = {
                "selected_action": selected["action"],
                "robust_value_bps": _fraction(value),
                "actions": action_rows,
            }
        layers.append({"horizon": horizon, "beliefs": belief_rows})
        previous = current

    initial = layers[-1]["beliefs"][problem.initial_belief]
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "horizon": problem.horizon,
        "discount": {
            "numerator": problem.discount_numerator,
            "denominator": problem.discount_denominator,
        },
        "models": list(problem.models),
        "initial_belief": problem.initial_belief,
        "layers": layers,
        "initial_decision": {
            "action": initial["selected_action"],
            "robust_value_bps": initial["robust_value_bps"],
        },
        "controlled_claims": {
            "backward_induction_exact": True,
            "model_values_use_exact_rationals": True,
            "actions_use_worst_case_model_value": all(
                row["robust_value_bps"]["numerator"]
                * model_row["q_value_bps"]["denominator"]
                <= model_row["q_value_bps"]["numerator"]
                * row["robust_value_bps"]["denominator"]
                for layer in layers[1:]
                for belief in layer["beliefs"].values()
                for row in belief["actions"]
                for model_row in row["models"]
            ),
            "initial_query_selected": (
                initial["selected_action"] == "query"
            ),
        },
        "residual_boundaries": [
            "finite declared belief graph, models, rewards, and branch weights",
            "branch weights are model inputs rather than calibrated probabilities",
            "belief nodes are discretized and supplied rather than derived online",
            "no convergence, causal, future-return, or autonomous-trading claim",
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
            "robust-POMDP report does not match exact recomputation"
        )
    return expected
