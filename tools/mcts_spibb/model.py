from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError
from tools.robust_pomdp.model import Problem as RobustProblem
from tools.robust_pomdp.model import load_problem as load_robust_problem

from .errors import ValidationError

SCHEMA = "lfv-mcts-spibb-planner-v1"


@dataclass(frozen=True)
class Plan:
    source: Path
    repository_root: Path
    name: str
    simulations: int
    exploration_milli: int
    minimum_support: int
    required_root_margin_bps: int
    baseline_policy: dict[str, str]
    safe_actions: dict[str, tuple[str, ...]]
    support_counts: dict[str, dict[str, int]]
    robust_model_path: Path
    robust_model: RobustProblem


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


def _natural(value: Any, path: str, *, positive: bool = False) -> int:
    result = _integer(value, path)
    if result < 0 or (positive and result == 0):
        qualifier = "positive" if positive else "non-negative"
        raise ValidationError(f"{path}: expected {qualifier} integer")
    return result


def _repository_file(
    repository_root: Path,
    value: Any,
    path: str,
) -> Path:
    relative = Path(_string(value, path))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValidationError(f"{path}: path must stay inside repository root")
    candidate = (repository_root / relative).resolve()
    try:
        candidate.relative_to(repository_root)
    except ValueError as exc:
        raise ValidationError(f"{path}: path escapes repository root") from exc
    if not candidate.is_file():
        raise ValidationError(f"{path}: missing file")
    return candidate


def load_plan(path: Path, repository_root: Path) -> Plan:
    repository_root = repository_root.resolve()
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version", "name", "robust_model", "simulations",
        "exploration_milli", "minimum_support", "required_root_margin_bps",
        "baseline_policy", "safe_actions", "support_counts",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")
    robust_model_path = _repository_file(
        repository_root, raw["robust_model"], "$.robust_model"
    )
    try:
        robust_model = load_robust_problem(robust_model_path)
    except Exception as exc:
        raise ValidationError(f"$.robust_model: {exc}") from exc
    belief_by_id = robust_model.belief_by_id
    belief_ids = set(belief_by_id)

    baseline_raw = _object(raw["baseline_policy"], "$.baseline_policy")
    safe_raw = _object(raw["safe_actions"], "$.safe_actions")
    support_raw = _object(raw["support_counts"], "$.support_counts")
    if set(baseline_raw) != belief_ids:
        raise ValidationError("$.baseline_policy: keys must match beliefs")
    if set(safe_raw) != belief_ids:
        raise ValidationError("$.safe_actions: keys must match beliefs")
    if set(support_raw) != belief_ids:
        raise ValidationError("$.support_counts: keys must match beliefs")

    baseline_policy: dict[str, str] = {}
    safe_actions: dict[str, tuple[str, ...]] = {}
    support_counts: dict[str, dict[str, int]] = {}
    for belief_id, belief in belief_by_id.items():
        action_ids = {action.id for action in belief.actions}
        baseline = _string(
            baseline_raw[belief_id], f"$.baseline_policy.{belief_id}"
        )
        if baseline not in action_ids:
            raise ValidationError(
                f"$.baseline_policy.{belief_id}: unknown action"
            )
        safe_list = safe_raw[belief_id]
        if not isinstance(safe_list, list) or not safe_list or any(
            not isinstance(action, str) or action not in action_ids
            for action in safe_list
        ):
            raise ValidationError(
                f"$.safe_actions.{belief_id}: expected known actions"
            )
        safe_tuple = tuple(safe_list)
        if len(set(safe_tuple)) != len(safe_tuple):
            raise ValidationError(
                f"$.safe_actions.{belief_id}: duplicates are not allowed"
            )
        if baseline not in safe_tuple:
            raise ValidationError(
                f"$.safe_actions.{belief_id}: baseline must be safe"
            )
        counts_raw = _object(
            support_raw[belief_id], f"$.support_counts.{belief_id}"
        )
        if set(counts_raw) != action_ids:
            raise ValidationError(
                f"$.support_counts.{belief_id}: keys must match actions"
            )
        baseline_policy[belief_id] = baseline
        safe_actions[belief_id] = safe_tuple
        support_counts[belief_id] = {
            action: _natural(
                counts_raw[action],
                f"$.support_counts.{belief_id}.{action}",
            )
            for action in action_ids
        }

    return Plan(
        source=path.resolve(),
        repository_root=repository_root,
        name=_string(raw["name"], "$.name"),
        simulations=_natural(raw["simulations"], "$.simulations", positive=True),
        exploration_milli=_natural(
            raw["exploration_milli"], "$.exploration_milli"
        ),
        minimum_support=_natural(
            raw["minimum_support"], "$.minimum_support"
        ),
        required_root_margin_bps=_natural(
            raw["required_root_margin_bps"],
            "$.required_root_margin_bps",
        ),
        baseline_policy=baseline_policy,
        safe_actions=safe_actions,
        support_counts=support_counts,
        robust_model_path=robust_model_path,
        robust_model=robust_model,
    )
