from __future__ import annotations

import hashlib
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import AUTHORITY_LEVELS, Action, Problem, State

REPORT_SCHEMA = "lfv-autonomous-control-foundation-report-v1"


def _safe_actions(
    state: State,
    viable_successors: set[str],
) -> list[Action]:
    return [
        action for action in state.actions
        if set(action.next_states).issubset(viable_successors)
    ]


def _viability_layers(problem: Problem) -> list[set[str]]:
    layers = [{state.id for state in problem.states if state.safe}]
    for _ in range(problem.horizon):
        previous = layers[-1]
        current = {
            state.id for state in problem.states
            if state.safe and _safe_actions(state, previous)
        }
        layers.append(current)
    return layers


def _next_authority(current: str) -> str:
    order = [
        "observe", "shadow", "recommend", "microAutonomy",
        "boundedAutonomy",
    ]
    if current in {"fallback", "revoked", "boundedAutonomy"}:
        return current
    return order[order.index(current) + 1]


def _authority(problem: Problem, improvement_passed: bool) -> dict[str, Any]:
    evidence = problem.authority
    eligible = (
        improvement_passed
        and evidence.improvement_lcb > 0
        and evidence.effective_sample_size
        >= evidence.minimum_effective_sample_size
        and evidence.risk_ucb <= evidence.risk_budget
    )
    if evidence.model_shift or evidence.operational_breach:
        decision = "revoked"
        reason = "model shift or operational breach"
    elif eligible:
        decision = _next_authority(evidence.current)
        reason = "registered improvement, support, and risk gates passed"
    else:
        decision = evidence.current
        reason = "authority held at current level"
    return {
        "current": evidence.current,
        "decision": decision,
        "capital_cap": evidence.capital_caps[decision],
        "eligible": eligible,
        "improvement_lcb": evidence.improvement_lcb,
        "effective_sample_size": evidence.effective_sample_size,
        "minimum_effective_sample_size": (
            evidence.minimum_effective_sample_size
        ),
        "risk_ucb": evidence.risk_ucb,
        "risk_budget": evidence.risk_budget,
        "model_shift": evidence.model_shift,
        "operational_breach": evidence.operational_breach,
        "reason": reason,
    }


def solve(problem: Problem) -> dict[str, Any]:
    layers = _viability_layers(problem)
    successor_kernel = layers[problem.horizon - 1]
    state_rows: list[dict[str, Any]] = []
    baseline_score = 0
    candidate_score = 0
    candidate_policy: dict[str, str] = {}
    baseline_policy: dict[str, str] = {}
    all_baselines_safe = True
    all_candidates_safe = True
    respects_baseline = True

    for state in problem.states:
        safe_actions = _safe_actions(state, successor_kernel)
        safe_ids = [action.id for action in safe_actions]
        baseline = state.action_by_id[state.baseline_action]
        baseline_safe = baseline.id in safe_ids
        all_baselines_safe = all_baselines_safe and (
            baseline_safe or not state.safe
        )
        proposed_safe = state.proposed_action in safe_ids
        shielded = state.proposed_action if proposed_safe else state.baseline_action

        supported_safe = [
            action for action in safe_actions
            if action.count >= problem.minimum_support
        ]
        if supported_safe:
            candidate = min(
                supported_safe,
                key=lambda action: (-action.reward_lcb, action.id),
            )
        else:
            candidate = baseline
        candidate_safe = candidate.id in safe_ids
        all_candidates_safe = all_candidates_safe and (
            candidate_safe or not state.safe
        )
        if candidate.count < problem.minimum_support:
            respects_baseline = (
                respects_baseline and candidate.id == baseline.id
            )

        if state.id in problem.evaluation_states:
            baseline_score += baseline.reward_lcb
            candidate_score += candidate.reward_lcb
        baseline_policy[state.id] = baseline.id
        candidate_policy[state.id] = candidate.id
        state_rows.append({
            "state": state.id,
            "safe": state.safe,
            "viable_at_horizon": state.id in layers[-1],
            "safe_actions": safe_ids,
            "baseline_action": baseline.id,
            "baseline_safe": baseline_safe,
            "proposed_action": state.proposed_action,
            "proposed_safe": proposed_safe,
            "shielded_action": shielded,
            "candidate_action": candidate.id,
            "candidate_count": candidate.count,
            "candidate_supported": (
                candidate.count >= problem.minimum_support
            ),
            "candidate_safe": candidate_safe,
            "candidate_reward_lcb": candidate.reward_lcb,
        })

    if not all_baselines_safe:
        raise ValidationError(
            "baseline policy is not total and safe on every declared safe state"
        )
    improvement = candidate_score - baseline_score
    improvement_passed = improvement >= problem.required_improvement
    authority = _authority(problem, improvement_passed)
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "horizon": problem.horizon,
        "minimum_support": problem.minimum_support,
        "required_improvement": problem.required_improvement,
        "viability_layers": [sorted(layer) for layer in layers],
        "states": state_rows,
        "baseline_policy": baseline_policy,
        "candidate_policy": candidate_policy,
        "policy_certificate": {
            "baseline_score_lcb": baseline_score,
            "candidate_score_lcb": candidate_score,
            "improvement_lcb": improvement,
            "improvement_passed": improvement_passed,
            "respects_baseline_outside_support": respects_baseline,
            "all_candidate_actions_safe": all_candidates_safe,
        },
        "authority": authority,
        "controlled_claims": {
            "shield_never_emits_known_unsafe_action": all(
                (not row["safe"])
                or row["shielded_action"] in row["safe_actions"]
                for row in state_rows
            ),
            "candidate_is_baseline_constrained": respects_baseline,
            "candidate_clears_registered_margin": improvement_passed,
            "authority_advances_at_most_one_level": (
                authority["decision"]
                in {problem.authority.current,
                    _next_authority(problem.authority.current),
                    "revoked"}
            ),
        },
        "residual_boundaries": [
            "finite declared states, actions, and successor supports",
            "reward lower bounds and support counts are controlled inputs",
            "no claim of calibrated transition probabilities or market returns",
            "authority capital caps are governance inputs",
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
            "autonomous-control report does not match exact recomputation"
        )
    return expected
