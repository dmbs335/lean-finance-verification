from __future__ import annotations

import hashlib
from fractions import Fraction
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Action, Problem, State

REPORT_SCHEMA = "lfv-safe-tree-policy-search-report-v1"


def _fraction(value: Fraction) -> dict[str, int]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "floor": value.numerator // value.denominator,
    }


def _admissible(
    problem: Problem,
    state: State,
    action: Action,
) -> tuple[bool, str | None]:
    if not action.safe:
        return False, "unsafe"
    supported = action.support_count >= problem.minimum_support
    baseline = action.id == state.baseline_action
    if not supported and not baseline:
        return False, "insufficient-support"
    return True, None


def solve(problem: Problem) -> dict[str, Any]:
    discount = Fraction(
        problem.discount_numerator,
        problem.discount_denominator,
    )
    previous = {
        state.id: Fraction(state.terminal_value_lcb, 1)
        for state in problem.states
    }
    layers: list[dict[str, Any]] = [{
        "remaining_horizon": 0,
        "state_values": {
            state_id: _fraction(value)
            for state_id, value in sorted(previous.items())
        },
        "states": [],
    }]
    selected_policy_by_horizon: list[dict[str, str]] = []

    for remaining_horizon in range(1, problem.horizon + 1):
        current: dict[str, Fraction] = {}
        state_rows: list[dict[str, Any]] = []
        policy: dict[str, str] = {}
        for state in problem.states:
            action_rows: list[dict[str, Any]] = []
            admissible_rows: list[tuple[Action, Fraction]] = []
            for action in state.actions:
                accepted, exclusion = _admissible(problem, state, action)
                worst_successor = min(
                    previous[next_state]
                    for next_state in action.next_states
                )
                lower_value = Fraction(action.reward_lcb, 1) + (
                    discount * worst_successor
                )
                action_rows.append({
                    "action": action.id,
                    "safe": action.safe,
                    "support_count": action.support_count,
                    "minimum_support": problem.minimum_support,
                    "baseline": action.id == state.baseline_action,
                    "supported": (
                        action.support_count >= problem.minimum_support
                    ),
                    "admissible": accepted,
                    "excluded_reason": exclusion,
                    "immediate_reward_lcb": action.reward_lcb,
                    "successors": list(action.next_states),
                    "worst_successor_value": _fraction(worst_successor),
                    "pessimistic_lower_value": _fraction(lower_value),
                })
                if accepted:
                    admissible_rows.append((action, lower_value))
            if not admissible_rows:
                raise ValidationError(
                    f"state {state.id}: no admissible action at horizon "
                    f"{remaining_horizon}"
                )
            selected_action, selected_value = min(
                admissible_rows,
                key=lambda pair: (-pair[1], pair[0].id),
            )
            current[state.id] = selected_value
            policy[state.id] = selected_action.id
            state_rows.append({
                "state": state.id,
                "baseline_action": state.baseline_action,
                "selected_action": selected_action.id,
                "selected_is_baseline": (
                    selected_action.id == state.baseline_action
                ),
                "selected_value": _fraction(selected_value),
                "actions": action_rows,
            })
        layers.append({
            "remaining_horizon": remaining_horizon,
            "state_values": {
                state_id: _fraction(value)
                for state_id, value in sorted(current.items())
            },
            "states": state_rows,
        })
        selected_policy_by_horizon.append(policy)
        previous = current

    final_layer = layers[-1]
    final_rows = {
        row["state"]: row for row in final_layer["states"]
    }
    root_row = final_rows[problem.root_state]
    every_baseline_available = all(
        any(
            action["action"] == row["baseline_action"]
            and action["admissible"]
            for action in row["actions"]
        )
        for layer in layers[1:]
        for row in layer["states"]
    )
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "root_state": problem.root_state,
        "horizon": problem.horizon,
        "minimum_support": problem.minimum_support,
        "discount": {
            "numerator": problem.discount_numerator,
            "denominator": problem.discount_denominator,
        },
        "layers": layers,
        "policy_by_horizon": selected_policy_by_horizon,
        "root_decision": {
            "action": root_row["selected_action"],
            "pessimistic_lower_value": root_row["selected_value"],
            "is_baseline": root_row["selected_is_baseline"],
        },
        "controlled_claims": {
            "unsafe_actions_never_selected": all(
                next(
                    action for action in row["actions"]
                    if action["action"] == row["selected_action"]
                )["safe"]
                for layer in layers[1:]
                for row in layer["states"]
            ),
            "unsupported_nonbaseline_actions_never_selected": all(
                (
                    selected["supported"]
                    or selected["baseline"]
                )
                for layer in layers[1:]
                for row in layer["states"]
                for selected in [next(
                    action for action in row["actions"]
                    if action["action"] == row["selected_action"]
                )]
            ),
            "baseline_is_total": every_baseline_available,
            "selection_uses_worst_successor": True,
            "finite_horizon_exact": True,
        },
        "residual_boundaries": [
            "finite declared states, actions, and successor supports",
            "reward lower bounds and transition supports are controlled inputs",
            "no calibrated transition probabilities or statistical coverage",
            "exact dynamic programming is a foundation, not stochastic MCTS",
            "no autonomous-trading or future-profitability claim",
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
            "safe-tree-search report does not match exact recomputation"
        )
    return expected
