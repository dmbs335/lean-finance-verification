from __future__ import annotations

import hashlib
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .model import DIGEST_FIELDS, Problem, _time
from .errors import ValidationError

REPORT_SCHEMA = "lfv-prospective-backtest-admission-report-v1"


def solve(problem: Problem) -> dict[str, Any]:
    plan = problem.plan
    execution = problem.execution
    preregistered = (
        _time(plan.registered_at) < _time(plan.first_decision_at)
        <= _time(plan.outcome_start_at) < _time(plan.outcome_end_at)
    )
    contracts = {
        field: plan.digests[field] == execution.digests[field]
        for field in DIGEST_FIELDS
    }
    trial_set_exact = (
        set(execution.executed_trial_ids)
        == set(plan.registered_trial_ids)
        and len(execution.executed_trial_ids)
        == len(plan.registered_trial_ids)
    )
    primary_selected = execution.selected_trial_id == plan.primary_trial_id
    structural_ready = (
        preregistered
        and all(contracts.values())
        and trial_set_exact
        and primary_selected
        and problem.all_executed_trials_disclosed
    )

    outcome_present = problem.outcome is not None
    outcome_row: dict[str, Any] | None = None
    outcome_mature = False
    outcome_pass = False
    if problem.outcome is not None:
        outcome = problem.outcome
        window_exact = (
            outcome.window_start_at == plan.outcome_start_at
            and outcome.window_end_at == plan.outcome_end_at
        )
        outcome_mature = (
            window_exact
            and _time(plan.outcome_end_at) <= _time(outcome.available_at)
        )
        lower_pass = (
            plan.minimum_result_lcb_bps <= outcome.result_lcb_bps
        )
        outcome_pass = (
            outcome_mature
            and outcome.strict_pit_verified
            and lower_pass
        )
        outcome_row = {
            "window_start_at": outcome.window_start_at,
            "window_end_at": outcome.window_end_at,
            "available_at": outcome.available_at,
            "window_exact": window_exact,
            "mature": outcome_mature,
            "strict_pit_verified": outcome.strict_pit_verified,
            "data_lineage_sha256": outcome.data_lineage_sha256,
            "result_lcb_bps": outcome.result_lcb_bps,
            "minimum_result_lcb_bps": plan.minimum_result_lcb_bps,
            "lower_bound_passed": lower_pass,
        }

    if not structural_ready:
        status = "rejected"
        reason = "prospective registration, contract, or trial-ledger gate failed"
    elif not outcome_present:
        status = "pending"
        reason = "registered plan is waiting for its untouched outcome"
    elif not outcome_mature:
        status = "rejected"
        reason = "presented outcome is premature or uses the wrong window"
    elif outcome_pass:
        status = "admitted-controlled"
        reason = "all prospective admission gates passed"
    else:
        status = "rejected"
        reason = "mature outcome failed strict-PIT or lower-bound gate"

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "plan": {
            "plan_id": plan.plan_id,
            "registered_at": plan.registered_at,
            "first_decision_at": plan.first_decision_at,
            "outcome_start_at": plan.outcome_start_at,
            "outcome_end_at": plan.outcome_end_at,
            "primary_trial_id": plan.primary_trial_id,
            "registered_trial_ids": list(plan.registered_trial_ids),
            "minimum_result_lcb_bps": plan.minimum_result_lcb_bps,
            "digests": plan.digests,
        },
        "execution": {
            "selected_trial_id": execution.selected_trial_id,
            "executed_trial_ids": list(execution.executed_trial_ids),
            "digests": execution.digests,
        },
        "outcome": outcome_row,
        "gates": {
            "preregistered_before_first_decision": preregistered,
            "contracts_unchanged": contracts,
            "all_contracts_unchanged": all(contracts.values()),
            "trial_ledger_exact": trial_set_exact,
            "primary_trial_selected": primary_selected,
            "all_executed_trials_disclosed": (
                problem.all_executed_trials_disclosed
            ),
            "structural_ready": structural_ready,
            "outcome_present": outcome_present,
            "outcome_mature": outcome_mature,
            "outcome_pass": outcome_pass,
        },
        "status": status,
        "reason": reason,
        "certificate": ({
            "plan_id": plan.plan_id,
            "primary_trial_id": plan.primary_trial_id,
            "outcome_lineage_sha256": problem.outcome.data_lineage_sha256,
            "result_lcb_bps": problem.outcome.result_lcb_bps,
            "strict_pit_verified": True,
            "all_trials_disclosed": True,
            "contracts_unchanged": True,
        } if status == "admitted-controlled" and problem.outcome is not None
          else None),
        "residual_boundaries": [
            "digest authenticity and strict-PIT verifier correctness are external",
            "finite registered trial language may omit real researcher discretion",
            "a positive lower bound does not guarantee future profitability",
            "admission is controlled research status, not order authority",
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
            "prospective-backtest report does not match exact recomputation"
        )
    return expected
