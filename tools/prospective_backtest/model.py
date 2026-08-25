from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-prospective-backtest-admission-v1"
DIGEST_FIELDS = (
    "code_sha256", "parameter_sha256", "metric_sha256",
    "benchmark_sha256", "cost_model_sha256", "universe_sha256",
)


@dataclass(frozen=True)
class Plan:
    plan_id: str
    registered_at: str
    first_decision_at: str
    outcome_start_at: str
    outcome_end_at: str
    primary_trial_id: str
    registered_trial_ids: tuple[str, ...]
    minimum_result_lcb_bps: int
    digests: dict[str, str]


@dataclass(frozen=True)
class Execution:
    selected_trial_id: str
    executed_trial_ids: tuple[str, ...]
    digests: dict[str, str]


@dataclass(frozen=True)
class Outcome:
    window_start_at: str
    window_end_at: str
    available_at: str
    strict_pit_verified: bool
    data_lineage_sha256: str
    result_lcb_bps: int


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    plan: Plan
    execution: Execution
    outcome: Outcome | None
    all_executed_trials_disclosed: bool


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path}: expected integer")
    return value


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path}: expected boolean")
    return value


def _instant(value: Any, path: str) -> str:
    text = _string(value, path)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{path}: expected ISO instant") from exc
    return text


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _digest(value: Any, path: str) -> str:
    text = _string(value, path)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ValidationError(f"{path}: expected lowercase SHA-256")
    return text


def _trial_ids(value: Any, path: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ValidationError(f"{path}: expected non-empty string array")
    result = tuple(value)
    if len(set(result)) != len(result):
        raise ValidationError(f"{path}: duplicate trial id")
    return result


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version", "name", "plan", "execution", "outcome",
        "search_ledger",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")

    plan_raw = _object(raw["plan"], "$.plan")
    expected_plan = {
        "plan_id", "registered_at", "first_decision_at",
        "outcome_start_at", "outcome_end_at", "primary_trial_id",
        "registered_trial_ids", "minimum_result_lcb_bps", *DIGEST_FIELDS,
    }
    if set(plan_raw) != expected_plan:
        raise ValidationError("$.plan: fields do not match")
    plan = Plan(
        plan_id=_string(plan_raw["plan_id"], "$.plan.plan_id"),
        registered_at=_instant(plan_raw["registered_at"], "$.plan.registered_at"),
        first_decision_at=_instant(
            plan_raw["first_decision_at"], "$.plan.first_decision_at"
        ),
        outcome_start_at=_instant(
            plan_raw["outcome_start_at"], "$.plan.outcome_start_at"
        ),
        outcome_end_at=_instant(
            plan_raw["outcome_end_at"], "$.plan.outcome_end_at"
        ),
        primary_trial_id=_string(
            plan_raw["primary_trial_id"], "$.plan.primary_trial_id"
        ),
        registered_trial_ids=_trial_ids(
            plan_raw["registered_trial_ids"], "$.plan.registered_trial_ids"
        ),
        minimum_result_lcb_bps=_integer(
            plan_raw["minimum_result_lcb_bps"],
            "$.plan.minimum_result_lcb_bps",
        ),
        digests={
            field: _digest(plan_raw[field], f"$.plan.{field}")
            for field in DIGEST_FIELDS
        },
    )
    if plan.primary_trial_id not in plan.registered_trial_ids:
        raise ValidationError("$.plan.primary_trial_id: not registered")

    execution_raw = _object(raw["execution"], "$.execution")
    expected_execution = {
        "selected_trial_id", "executed_trial_ids", *DIGEST_FIELDS,
    }
    if set(execution_raw) != expected_execution:
        raise ValidationError("$.execution: fields do not match")
    execution = Execution(
        selected_trial_id=_string(
            execution_raw["selected_trial_id"],
            "$.execution.selected_trial_id",
        ),
        executed_trial_ids=_trial_ids(
            execution_raw["executed_trial_ids"],
            "$.execution.executed_trial_ids",
        ),
        digests={
            field: _digest(execution_raw[field], f"$.execution.{field}")
            for field in DIGEST_FIELDS
        },
    )

    outcome_raw = raw["outcome"]
    outcome: Outcome | None
    if outcome_raw is None:
        outcome = None
    else:
        outcome_obj = _object(outcome_raw, "$.outcome")
        expected_outcome = {
            "window_start_at", "window_end_at", "available_at",
            "strict_pit_verified", "data_lineage_sha256", "result_lcb_bps",
        }
        if set(outcome_obj) != expected_outcome:
            raise ValidationError("$.outcome: fields do not match")
        outcome = Outcome(
            window_start_at=_instant(
                outcome_obj["window_start_at"], "$.outcome.window_start_at"
            ),
            window_end_at=_instant(
                outcome_obj["window_end_at"], "$.outcome.window_end_at"
            ),
            available_at=_instant(
                outcome_obj["available_at"], "$.outcome.available_at"
            ),
            strict_pit_verified=_boolean(
                outcome_obj["strict_pit_verified"],
                "$.outcome.strict_pit_verified",
            ),
            data_lineage_sha256=_digest(
                outcome_obj["data_lineage_sha256"],
                "$.outcome.data_lineage_sha256",
            ),
            result_lcb_bps=_integer(
                outcome_obj["result_lcb_bps"], "$.outcome.result_lcb_bps"
            ),
        )

    ledger = _object(raw["search_ledger"], "$.search_ledger")
    if set(ledger) != {"all_executed_trials_disclosed"}:
        raise ValidationError("$.search_ledger: fields do not match")
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        plan=plan,
        execution=execution,
        outcome=outcome,
        all_executed_trials_disclosed=_boolean(
            ledger["all_executed_trials_disclosed"],
            "$.search_ledger.all_executed_trials_disclosed",
        ),
    )
