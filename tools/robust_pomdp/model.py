from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-robust-pomdp-bellman-v1"
MAX_BELIEFS = 32
MAX_ACTIONS = 16
MAX_MODELS = 16


@dataclass(frozen=True)
class Branch:
    next_belief: str
    weight: int


@dataclass(frozen=True)
class Action:
    id: str
    execution_cost_bps: int
    reward_bps: dict[str, int]
    transitions: dict[str, tuple[Branch, ...]]


@dataclass(frozen=True)
class BeliefNode:
    id: str
    actions: tuple[Action, ...]


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    horizon: int
    discount_numerator: int
    discount_denominator: int
    models: tuple[str, ...]
    initial_belief: str
    beliefs: tuple[BeliefNode, ...]

    @property
    def belief_by_id(self) -> dict[str, BeliefNode]:
        return {belief.id: belief for belief in self.beliefs}


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


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version", "name", "horizon", "discount", "models",
        "initial_belief", "beliefs",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")

    models_raw = raw["models"]
    if not isinstance(models_raw, list) or not 1 <= len(models_raw) <= MAX_MODELS:
        raise ValidationError(f"$.models: expected 1..{MAX_MODELS} entries")
    models = tuple(_string(model, "$.models[]") for model in models_raw)
    if len(set(models)) != len(models):
        raise ValidationError("$.models: ids must be unique")
    model_set = set(models)

    discount = _object(raw["discount"], "$.discount")
    if set(discount) != {"numerator", "denominator"}:
        raise ValidationError("$.discount: fields do not match")
    discount_numerator = _natural(discount["numerator"], "$.discount.numerator")
    discount_denominator = _natural(
        discount["denominator"], "$.discount.denominator", positive=True
    )
    if discount_numerator > discount_denominator:
        raise ValidationError("$.discount: expected a factor in [0, 1]")

    beliefs_raw = raw["beliefs"]
    if not isinstance(beliefs_raw, list) or not 1 <= len(beliefs_raw) <= MAX_BELIEFS:
        raise ValidationError(f"$.beliefs: expected 1..{MAX_BELIEFS} entries")
    beliefs: list[BeliefNode] = []
    for belief_index, belief_item in enumerate(beliefs_raw):
        belief_path = f"$.beliefs[{belief_index}]"
        belief_obj = _object(belief_item, belief_path)
        if set(belief_obj) != {"id", "actions"}:
            raise ValidationError(f"{belief_path}: fields do not match")
        actions_raw = belief_obj["actions"]
        if not isinstance(actions_raw, list) or not 1 <= len(actions_raw) <= MAX_ACTIONS:
            raise ValidationError(
                f"{belief_path}.actions: expected 1..{MAX_ACTIONS} entries"
            )
        actions: list[Action] = []
        for action_index, action_item in enumerate(actions_raw):
            action_path = f"{belief_path}.actions[{action_index}]"
            action_obj = _object(action_item, action_path)
            if set(action_obj) != {
                "id", "execution_cost_bps", "reward_bps", "transitions"
            }:
                raise ValidationError(f"{action_path}: fields do not match")
            rewards = _object(action_obj["reward_bps"], f"{action_path}.reward_bps")
            transitions_raw = _object(
                action_obj["transitions"], f"{action_path}.transitions"
            )
            if set(rewards) != model_set or set(transitions_raw) != model_set:
                raise ValidationError(
                    f"{action_path}: rewards and transitions must cover models"
                )
            transitions: dict[str, tuple[Branch, ...]] = {}
            for model in models:
                branches_raw = transitions_raw[model]
                if not isinstance(branches_raw, list) or not branches_raw:
                    raise ValidationError(
                        f"{action_path}.transitions.{model}: expected branches"
                    )
                branches: list[Branch] = []
                for branch_index, branch_item in enumerate(branches_raw):
                    branch_path = (
                        f"{action_path}.transitions.{model}[{branch_index}]"
                    )
                    branch_obj = _object(branch_item, branch_path)
                    if set(branch_obj) != {"next", "weight"}:
                        raise ValidationError(f"{branch_path}: fields do not match")
                    branches.append(Branch(
                        next_belief=_string(branch_obj["next"], f"{branch_path}.next"),
                        weight=_natural(
                            branch_obj["weight"], f"{branch_path}.weight", positive=True
                        ),
                    ))
                if len({branch.next_belief for branch in branches}) != len(branches):
                    raise ValidationError(
                        f"{action_path}.transitions.{model}: duplicate successor"
                    )
                transitions[model] = tuple(branches)
            actions.append(Action(
                id=_string(action_obj["id"], f"{action_path}.id"),
                execution_cost_bps=_natural(
                    action_obj["execution_cost_bps"],
                    f"{action_path}.execution_cost_bps",
                ),
                reward_bps={
                    model: _integer(rewards[model], f"{action_path}.reward_bps.{model}")
                    for model in models
                },
                transitions=transitions,
            ))
        if len({action.id for action in actions}) != len(actions):
            raise ValidationError(f"{belief_path}.actions: ids must be unique")
        beliefs.append(BeliefNode(
            id=_string(belief_obj["id"], f"{belief_path}.id"),
            actions=tuple(actions),
        ))
    if len({belief.id for belief in beliefs}) != len(beliefs):
        raise ValidationError("$.beliefs: ids must be unique")
    known_beliefs = {belief.id for belief in beliefs}
    initial_belief = _string(raw["initial_belief"], "$.initial_belief")
    if initial_belief not in known_beliefs:
        raise ValidationError("$.initial_belief: unknown belief")
    for belief in beliefs:
        for action in belief.actions:
            for model, branches in action.transitions.items():
                unknown = {
                    branch.next_belief for branch in branches
                    if branch.next_belief not in known_beliefs
                }
                if unknown:
                    raise ValidationError(
                        f"belief {belief.id} action {action.id} model {model}: "
                        f"unknown successors {sorted(unknown)}"
                    )
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        horizon=_natural(raw["horizon"], "$.horizon", positive=True),
        discount_numerator=discount_numerator,
        discount_denominator=discount_denominator,
        models=models,
        initial_belief=initial_belief,
        beliefs=tuple(beliefs),
    )
