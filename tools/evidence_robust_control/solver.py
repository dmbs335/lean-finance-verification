from __future__ import annotations

import hashlib
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Action, Problem

REPORT_SCHEMA = "lfv-evidence-robust-control-report-v1"


def _robust_value(action: Action, models: tuple[str, ...]) -> int:
    return min(action.model_values_bps[model] for model in models) - action.execution_cost_bps


def _best_action(problem: Problem, models: tuple[str, ...]) -> dict[str, Any]:
    rows = [
        {"action": action.id, "robust_net_value_bps": _robust_value(action, models)}
        for action in problem.actions
    ]
    selected = min(rows, key=lambda row: (-row["robust_net_value_bps"], row["action"]))
    return {"models": list(models), "actions": rows, "selected": selected}


def solve(problem: Problem) -> dict[str, Any]:
    immediate = _best_action(problem, problem.current_models)
    current_value = immediate["selected"]["robust_net_value_bps"]
    query_rows: list[dict[str, Any]] = []
    for query in problem.queries:
        outcomes: list[dict[str, Any]] = []
        for observation, remaining in sorted(query.observations.items()):
            analysis = _best_action(problem, remaining)
            outcomes.append({"observation": observation, **analysis})
        guarantee = min(
            outcome["selected"]["robust_net_value_bps"]
            for outcome in outcomes
        )
        net = guarantee - query.cost_bps
        query_rows.append({
            "query": query.id,
            "cost_bps": query.cost_bps,
            "outcomes": outcomes,
            "post_query_guarantee_bps": guarantee,
            "net_post_query_value_bps": net,
            "robust_value_of_information_bps": net - current_value,
        })
    selected_query = min(
        query_rows,
        key=lambda row: (-row["net_post_query_value_bps"], row["query"]),
    )
    acquire_evidence = (
        selected_query["net_post_query_value_bps"] > current_value
    )
    capital = problem.capital_rule
    robust_gain = (
        capital.robust_value_after_bps - capital.robust_value_before_bps
    )
    crowding_increase = (
        capital.crowding_cost_after_bps - capital.crowding_cost_before_bps
    )
    capital_allowed = crowding_increase < robust_gain
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "current_ambiguity_set": list(problem.current_models),
        "immediate_control": immediate,
        "queries": query_rows,
        "decision": {
            "kind": "acquireEvidence" if acquire_evidence else "actNow",
            "selected_query": selected_query["query"] if acquire_evidence else None,
            "immediate_action": immediate["selected"]["action"],
            "current_robust_value_bps": current_value,
            "selected_net_value_bps": (
                selected_query["net_post_query_value_bps"]
                if acquire_evidence else current_value
            ),
        },
        "capital_rule": {
            "robust_value_before_bps": capital.robust_value_before_bps,
            "robust_value_after_bps": capital.robust_value_after_bps,
            "robust_gain_bps": robust_gain,
            "crowding_cost_before_bps": capital.crowding_cost_before_bps,
            "crowding_cost_after_bps": capital.crowding_cost_after_bps,
            "crowding_cost_increase_bps": crowding_increase,
            "capital_increase_allowed": capital_allowed,
        },
        "controlled_claims": {
            "query_selected_only_for_positive_robust_voi": (
                not acquire_evidence
                or selected_query["robust_value_of_information_bps"] > 0
            ),
            "capital_requires_gain_above_crowding": (
                capital_allowed == (crowding_increase < robust_gain)
            ),
        },
        "residual_boundaries": [
            "finite declared model family and action values",
            "observation branches and evidence costs are controlled inputs",
            "no observation probabilities or calibrated market dynamics",
            "capital rule is not an investment recommendation",
        ],
    }
    report["report_sha256"] = hashlib.sha256(canonical_bytes(report)).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "evidence-robust-control report does not match exact recomputation"
        )
    return expected
