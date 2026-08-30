from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-safe-tree-policy-search-v1"
MAX_STATES = 64
MAX_ACTIONS = 24
MAX_HORIZON = 12


@dataclass(frozen=True)
class Action:
    id: str
    support_count: int
    safe: bool
    reward_lcb: int
    next_states: tuple[str, ...]


@dataclass(frozen=True)
class State:
    id: str
    baseline_action: str
    terminal_value_lcb: int
    actions: tuple[Action, ...]

    @property
    def action_by_id(self) -> dict[str, Action]:
        return {action.id: action for action in self.actions}


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    root_state: str
    horizon: int
    minimum_support: int
    discount_numerator: int
    discount_denominator: int
    states: tuple[State, ...]

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
        "schema_version", "name", "root_state", "horizon",
        "minimum_support", "discount", "states",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")
    discount = _object(raw["discount"], "$.discount")
    if set(discount) != {"numerator", "denominator"}:
        raise ValidationError("$.discount: fields do not match")
    numerator = _natural(discount["numerator"], "$.discount.numerator")
    denominator = _natural(
        discount["denominator"], "$.discount.denominator", positive=True
    )
    if numerator > denominator:
        raise ValidationError("$.discount: factor must be at most one")
    horizon = _natural(raw["horizon"], "$.horizon", positive=True)
    if horizon > MAX_HORIZON:
        raise ValidationError(f"$.horizon: maximum is {MAX_HORIZON}")
    states_raw = raw["states"]
    if not isinstance(states_raw, list) or not 1 <= len(states_raw) <= MAX_STATES:
        raise ValidationError(f"$.states: expected 1..{MAX_STATES} entries")
    states: list[State] = []
    for state_index, state_item in enumerate(states_raw):
        state_path = f"$.states[{state_index}]"
        state_obj = _object(state_item, state_path)
        if set(state_obj) != {
            "id", "baseline_action", "terminal_value_lcb", "actions"
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
            if set(action_obj) != {
                "id", "support_count", "safe", "reward_lcb", "next_states"
            }:
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
                support_count=_natural(
                    action_obj["support_count"], f"{action_path}.support_count"
                ),
                safe=_boolean(action_obj["safe"], f"{action_path}.safe"),
                reward_lcb=_integer(
                    action_obj["reward_lcb"], f"{action_path}.reward_lcb"
                ),
                next_states=tuple(next_raw),
            ))
        if len({action.id for action in actions}) != len(actions):
            raise ValidationError(f"{state_path}.actions: ids must be unique")
        state = State(
            id=_string(state_obj["id"], f"{state_path}.id"),
            baseline_action=_string(
                state_obj["baseline_action"], f"{state_path}.baseline_action"
            ),
            terminal_value_lcb=_integer(
                state_obj["terminal_value_lcb"],
                f"{state_path}.terminal_value_lcb",
            ),
            actions=tuple(actions),
        )
        baseline = state.action_by_id.get(state.baseline_action)
        if baseline is None:
            raise ValidationError(f"{state_path}: unknown baseline action")
        if not baseline.safe:
            raise ValidationError(f"{state_path}: baseline action must be safe")
        states.append(state)
    if len({state.id for state in states}) != len(states):
        raise ValidationError("$.states: ids must be unique")
    state_ids = {state.id for state in states}
    for state in states:
        for action in state.actions:
            unknown = set(action.next_states) - state_ids
            if unknown:
                raise ValidationError(
                    f"state {state.id} action {action.id}: unknown next states "
                    f"{sorted(unknown)}"
                )
    root_state = _string(raw["root_state"], "$.root_state")
    if root_state not in state_ids:
        raise ValidationError("$.root_state: unknown state")
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        root_state=root_state,
        horizon=horizon,
        minimum_support=_natural(
            raw["minimum_support"], "$.minimum_support"
        ),
        discount_numerator=numerator,
        discount_denominator=denominator,
        states=tuple(states),
    )
