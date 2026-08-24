from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-autonomous-control-foundation-v1"
AUTHORITY_LEVELS = (
    "observe", "shadow", "recommend", "microAutonomy",
    "boundedAutonomy", "fallback", "revoked",
)
MAX_STATES = 32
MAX_ACTIONS = 16


@dataclass(frozen=True)
class Action:
    id: str
    count: int
    reward_lcb: int
    next_states: tuple[str, ...]


@dataclass(frozen=True)
class State:
    id: str
    safe: bool
    baseline_action: str
    proposed_action: str
    actions: tuple[Action, ...]

    @property
    def action_by_id(self) -> dict[str, Action]:
        return {action.id: action for action in self.actions}


@dataclass(frozen=True)
class AuthorityEvidence:
    current: str
    improvement_lcb: int
    effective_sample_size: int
    minimum_effective_sample_size: int
    risk_ucb: int
    risk_budget: int
    model_shift: bool
    operational_breach: bool
    capital_caps: dict[str, int]


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    horizon: int
    minimum_support: int
    required_improvement: int
    evaluation_states: tuple[str, ...]
    states: tuple[State, ...]
    authority: AuthorityEvidence

    @property
    def state_by_id(self) -> dict[str, State]:
        return {state.id: state for state in self.states}


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


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path}: expected boolean")
    return value


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version", "name", "horizon", "minimum_support",
        "required_improvement", "evaluation_states", "states", "authority",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")

    states_raw = raw["states"]
    if not isinstance(states_raw, list) or not 1 <= len(states_raw) <= MAX_STATES:
        raise ValidationError(f"$.states: expected 1..{MAX_STATES} entries")
    states: list[State] = []
    for state_index, state_item in enumerate(states_raw):
        state_path = f"$.states[{state_index}]"
        state_obj = _object(state_item, state_path)
        if set(state_obj) != {
            "id", "safe", "baseline_action", "proposed_action", "actions"
        }:
            raise ValidationError(f"{state_path}: fields do not match")
        actions_raw = state_obj["actions"]
        if not isinstance(actions_raw, list) or not 1 <= len(actions_raw) <= MAX_ACTIONS:
            raise ValidationError(
                f"{state_path}.actions: expected 1..{MAX_ACTIONS} entries"
            )
        actions: list[Action] = []
        for action_index, action_item in enumerate(actions_raw):
            action_path = f"{state_path}.actions[{action_index}]"
            action_obj = _object(action_item, action_path)
            if set(action_obj) != {"id", "count", "reward_lcb", "next_states"}:
                raise ValidationError(f"{action_path}: fields do not match")
            next_raw = action_obj["next_states"]
            if not isinstance(next_raw, list) or not next_raw or any(
                not isinstance(item, str) or not item for item in next_raw
            ):
                raise ValidationError(
                    f"{action_path}.next_states: expected non-empty strings"
                )
            actions.append(Action(
                id=_string(action_obj["id"], f"{action_path}.id"),
                count=_natural(action_obj["count"], f"{action_path}.count"),
                reward_lcb=_integer(
                    action_obj["reward_lcb"], f"{action_path}.reward_lcb"
                ),
                next_states=tuple(next_raw),
            ))
        if len({action.id for action in actions}) != len(actions):
            raise ValidationError(f"{state_path}.actions: ids must be unique")
        state = State(
            id=_string(state_obj["id"], f"{state_path}.id"),
            safe=_boolean(state_obj["safe"], f"{state_path}.safe"),
            baseline_action=_string(
                state_obj["baseline_action"], f"{state_path}.baseline_action"
            ),
            proposed_action=_string(
                state_obj["proposed_action"], f"{state_path}.proposed_action"
            ),
            actions=tuple(actions),
        )
        if state.baseline_action not in state.action_by_id:
            raise ValidationError(f"{state_path}: unknown baseline action")
        if state.proposed_action not in state.action_by_id:
            raise ValidationError(f"{state_path}: unknown proposed action")
        states.append(state)
    if len({state.id for state in states}) != len(states):
        raise ValidationError("$.states: ids must be unique")
    known_states = {state.id for state in states}
    for state in states:
        for action in state.actions:
            unknown = set(action.next_states) - known_states
            if unknown:
                raise ValidationError(
                    f"state {state.id} action {action.id}: unknown next states "
                    f"{sorted(unknown)}"
                )

    evaluation_raw = raw["evaluation_states"]
    if not isinstance(evaluation_raw, list) or not evaluation_raw or any(
        not isinstance(item, str) or not item for item in evaluation_raw
    ):
        raise ValidationError("$.evaluation_states: expected non-empty strings")
    if len(set(evaluation_raw)) != len(evaluation_raw):
        raise ValidationError("$.evaluation_states: duplicates are not allowed")
    if not set(evaluation_raw).issubset(known_states):
        raise ValidationError("$.evaluation_states: unknown state")

    authority_obj = _object(raw["authority"], "$.authority")
    expected_authority = {
        "current", "improvement_lcb", "effective_sample_size",
        "minimum_effective_sample_size", "risk_ucb", "risk_budget",
        "model_shift", "operational_breach", "capital_caps",
    }
    if set(authority_obj) != expected_authority:
        raise ValidationError("$.authority: fields do not match")
    current = _string(authority_obj["current"], "$.authority.current")
    if current not in AUTHORITY_LEVELS:
        raise ValidationError("$.authority.current: unsupported level")
    caps_raw = _object(authority_obj["capital_caps"], "$.authority.capital_caps")
    if set(caps_raw) != set(AUTHORITY_LEVELS):
        raise ValidationError("$.authority.capital_caps: keys must match levels")
    caps = {
        level: _natural(caps_raw[level], f"$.authority.capital_caps.{level}")
        for level in AUTHORITY_LEVELS
    }
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        horizon=_natural(raw["horizon"], "$.horizon", positive=True),
        minimum_support=_natural(
            raw["minimum_support"], "$.minimum_support"
        ),
        required_improvement=_integer(
            raw["required_improvement"], "$.required_improvement"
        ),
        evaluation_states=tuple(evaluation_raw),
        states=tuple(states),
        authority=AuthorityEvidence(
            current=current,
            improvement_lcb=_integer(
                authority_obj["improvement_lcb"],
                "$.authority.improvement_lcb",
            ),
            effective_sample_size=_natural(
                authority_obj["effective_sample_size"],
                "$.authority.effective_sample_size",
            ),
            minimum_effective_sample_size=_natural(
                authority_obj["minimum_effective_sample_size"],
                "$.authority.minimum_effective_sample_size",
            ),
            risk_ucb=_natural(authority_obj["risk_ucb"], "$.authority.risk_ucb"),
            risk_budget=_natural(
                authority_obj["risk_budget"], "$.authority.risk_budget"
            ),
            model_shift=_boolean(
                authority_obj["model_shift"], "$.authority.model_shift"
            ),
            operational_breach=_boolean(
                authority_obj["operational_breach"],
                "$.authority.operational_breach",
            ),
            capital_caps=caps,
        ),
    )
