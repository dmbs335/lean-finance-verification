from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes
from tools.robust_pomdp.solver import solve as solve_robust

from .errors import ValidationError
from .model import Plan

REPORT_SCHEMA = "lfv-mcts-spibb-planner-report-v1"


@dataclass
class EdgeStats:
    visits: int = 0
    value_sum: Fraction = Fraction(0, 1)
    branch_visits: dict[str, int] = field(default_factory=dict)

    @property
    def mean(self) -> Fraction:
        return self.value_sum / self.visits if self.visits else Fraction(0, 1)


def _fraction(value: Fraction) -> dict[str, int]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "floor": value.numerator // value.denominator,
    }


def _report_fraction(value: dict[str, int]) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


def _allowed_actions(plan: Plan, belief_id: str) -> tuple[list[str], list[dict[str, Any]]]:
    belief = plan.robust_model.belief_by_id[belief_id]
    baseline = plan.baseline_policy[belief_id]
    safe = set(plan.safe_actions[belief_id])
    allowed: list[str] = []
    excluded: list[dict[str, Any]] = []
    for action in sorted(action.id for action in belief.actions):
        reasons: list[str] = []
        if action not in safe:
            reasons.append("unsafe")
        supported = (
            plan.support_counts[belief_id][action] >= plan.minimum_support
        )
        if not supported and action != baseline:
            reasons.append("insufficientSupport")
        if reasons:
            excluded.append({"action": action, "reasons": reasons})
        else:
            allowed.append(action)
    if baseline not in allowed:
        raise ValidationError(
            f"baseline {baseline} is not an admissible action at {belief_id}"
        )
    return allowed, excluded


def _action_row(
    robust_report: dict[str, Any],
    horizon: int,
    belief_id: str,
    action_id: str,
) -> dict[str, Any]:
    belief = robust_report["layers"][horizon]["beliefs"][belief_id]
    return next(
        action for action in belief["actions"]
        if action["action"] == action_id
    )


def _state_value(
    robust_report: dict[str, Any],
    horizon: int,
    belief_id: str,
) -> Fraction:
    return _report_fraction(
        robust_report["layers"][horizon]["beliefs"][belief_id][
            "robust_value_bps"
        ]
    )


def _choose_action(
    action_ids: list[str],
    stats: dict[str, EdgeStats],
    total_visits: int,
    exploration: float,
) -> str:
    unvisited = [action for action in action_ids if stats[action].visits == 0]
    if unvisited:
        return sorted(unvisited)[0]
    scored: list[tuple[float, str]] = []
    for action in action_ids:
        edge = stats[action]
        score = float(edge.mean) + exploration * math.sqrt(
            math.log(total_visits + 1) / edge.visits
        )
        scored.append((score, action))
    return min(scored, key=lambda item: (-item[0], item[1]))[1]


def _weighted_successor(branches: list[dict[str, Any]], offset: int) -> str:
    total = sum(branch["weight"] for branch in branches)
    cursor = offset % total
    for branch in branches:
        if cursor < branch["weight"]:
            return branch["next_belief"]
        cursor -= branch["weight"]
    raise AssertionError("weighted successor selection exhausted")


def solve(plan: Plan) -> dict[str, Any]:
    robust_report = solve_robust(plan.robust_model)
    root = plan.robust_model.initial_belief
    horizon = plan.robust_model.horizon
    allowed, excluded = _allowed_actions(plan, root)
    belief = plan.robust_model.belief_by_id[root]
    action_by_id = {action.id: action for action in belief.actions}
    stats = {action: EdgeStats() for action in allowed}
    exploration = plan.exploration_milli / 1000.0
    trace: list[dict[str, Any]] = []

    for simulation in range(1, plan.simulations + 1):
        action_id = _choose_action(
            allowed, stats, simulation - 1, exploration
        )
        edge = stats[action_id]
        exact_action = _action_row(
            robust_report, horizon, root, action_id
        )
        worst_model = sorted(exact_action["worst_case_models"])[0]
        model_row = next(
            row for row in exact_action["models"]
            if row["model"] == worst_model
        )
        action = action_by_id[action_id]
        branches = [
            {
                "next_belief": branch.next_belief,
                "weight": branch.weight,
            }
            for branch in action.transitions[worst_model]
        ]
        successor = _weighted_successor(branches, edge.visits)
        leaf = _state_value(robust_report, horizon - 1, successor)
        immediate = Fraction(
            action.reward_bps[worst_model] - action.execution_cost_bps,
            1,
        )
        discount = Fraction(
            plan.robust_model.discount_numerator,
            plan.robust_model.discount_denominator,
        )
        sample_value = immediate + discount * leaf
        edge.visits += 1
        edge.value_sum += sample_value
        edge.branch_visits[successor] = (
            edge.branch_visits.get(successor, 0) + 1
        )
        if simulation <= 8 or simulation > plan.simulations - 4:
            trace.append({
                "simulation": simulation,
                "action": action_id,
                "worst_case_model": worst_model,
                "successor": successor,
                "sample_value_bps": _fraction(sample_value),
            })

    proposal = min(
        allowed,
        key=lambda action: (
            -stats[action].visits,
            -float(stats[action].mean),
            action,
        ),
    )
    baseline = plan.baseline_policy[root]
    proposal_exact = _report_fraction(
        _action_row(robust_report, horizon, root, proposal)[
            "robust_value_bps"
        ]
    )
    baseline_exact = _report_fraction(
        _action_row(robust_report, horizon, root, baseline)[
            "robust_value_bps"
        ]
    )
    required_margin = Fraction(plan.required_root_margin_bps, 1)
    exact_gate_passed = (
        proposal_exact >= baseline_exact + required_margin
    )
    selected = proposal if exact_gate_passed else baseline
    root_rows = [
        {
            "action": action,
            "visits": stats[action].visits,
            "value_sum_bps": _fraction(stats[action].value_sum),
            "mean_value_bps": _fraction(stats[action].mean),
            "branch_visits": {
                successor: count
                for successor, count in sorted(
                    stats[action].branch_visits.items()
                )
            },
            "exact_robust_value_bps": _action_row(
                robust_report, horizon, root, action
            )["robust_value_bps"],
        }
        for action in allowed
    ]

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": plan.name,
        "robust_model": str(
            plan.robust_model_path.relative_to(plan.repository_root)
        ),
        "search": {
            "algorithm": "bounded-root-mcts-spibb",
            "leaf_evaluator": "exact-robust-bellman",
            "simulations": plan.simulations,
            "exploration_milli": plan.exploration_milli,
            "root_belief": root,
            "horizon": horizon,
            "allowed_actions": allowed,
            "excluded_actions": excluded,
            "root_statistics": root_rows,
            "trace_excerpt": trace,
            "proposal": proposal,
        },
        "exact_root_gate": {
            "baseline_action": baseline,
            "proposal_action": proposal,
            "baseline_robust_value_bps": _fraction(baseline_exact),
            "proposal_robust_value_bps": _fraction(proposal_exact),
            "required_margin_bps": plan.required_root_margin_bps,
            "passed": exact_gate_passed,
            "selected_action": selected,
        },
        "support_contract": {
            "minimum_support": plan.minimum_support,
            "baseline_policy": plan.baseline_policy,
            "safe_actions": {
                belief_id: list(actions)
                for belief_id, actions in plan.safe_actions.items()
            },
            "support_counts": plan.support_counts,
        },
        "controlled_claims": {
            "only_safe_supported_or_baseline_actions_expanded": all(
                action in plan.safe_actions[root]
                and (
                    plan.support_counts[root][action]
                    >= plan.minimum_support
                    or action == baseline
                )
                for action in allowed
            ),
            "proposal_is_admissible": proposal in allowed,
            "final_action_is_exactly_gated": (
                selected == (
                    proposal if exact_gate_passed else baseline
                )
            ),
            "search_is_fixed_budget": sum(
                row["visits"] for row in root_rows
            ) == plan.simulations,
        },
        "residual_boundaries": [
            "fixed-budget root search with exact Bellman leaf values",
            "UCT floating-point scores are deterministic implementation details",
            "support counts, safety sets, rewards, and model family are inputs",
            "no MCTS convergence, statistical safety, causality, or return claim",
        ],
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(plan: Plan, report: Any) -> dict[str, Any]:
    expected = solve(plan)
    if report != expected:
        raise ValidationError(
            "MCTS-SPIBB report does not match exact recomputation"
        )
    return expected
