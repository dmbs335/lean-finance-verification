from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-belief-state-robust-control-v1"


@dataclass(frozen=True)
class Action:
    id: str
    execution_cost_bps: int
    hidden_values_bps: dict[str, int]


@dataclass(frozen=True)
class Observation:
    id: str
    likelihood_weights: dict[str, int]


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    prior_weights: dict[str, int]
    actions: tuple[Action, ...]
    observations: tuple[Observation, ...]
    query_cost_bps: int


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
    if set(raw) != {
        "schema_version", "name", "prior_weights", "actions",
        "observations", "query_cost_bps",
    } or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")
    prior_raw = _object(raw["prior_weights"], "$.prior_weights")
    if not prior_raw:
        raise ValidationError("$.prior_weights: expected hidden states")
    prior = {
        _string(hidden, "$.prior_weights key"):
            _natural(weight, f"$.prior_weights.{hidden}")
        for hidden, weight in prior_raw.items()
    }
    if sum(prior.values()) <= 0:
        raise ValidationError("$.prior_weights: total must be positive")
    hidden_states = set(prior)
    actions_raw = raw["actions"]
    if not isinstance(actions_raw, list) or not actions_raw:
        raise ValidationError("$.actions: expected non-empty array")
    actions: list[Action] = []
    for index, item in enumerate(actions_raw):
        item_path = f"$.actions[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "execution_cost_bps", "hidden_values_bps"}:
            raise ValidationError(f"{item_path}: fields do not match")
        values = _object(obj["hidden_values_bps"], f"{item_path}.hidden_values_bps")
        if set(values) != hidden_states:
            raise ValidationError(f"{item_path}: values must cover hidden states")
        actions.append(Action(
            id=_string(obj["id"], f"{item_path}.id"),
            execution_cost_bps=_natural(
                obj["execution_cost_bps"], f"{item_path}.execution_cost_bps"
            ),
            hidden_values_bps={
                hidden: _integer(values[hidden], f"{item_path}.hidden_values_bps.{hidden}")
                for hidden in prior
            },
        ))
    if len({action.id for action in actions}) != len(actions):
        raise ValidationError("$.actions: ids must be unique")
    observations_raw = raw["observations"]
    if not isinstance(observations_raw, list) or not observations_raw:
        raise ValidationError("$.observations: expected non-empty array")
    observations: list[Observation] = []
    for index, item in enumerate(observations_raw):
        item_path = f"$.observations[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "likelihood_weights"}:
            raise ValidationError(f"{item_path}: fields do not match")
        likelihood = _object(obj["likelihood_weights"], f"{item_path}.likelihood_weights")
        if set(likelihood) != hidden_states:
            raise ValidationError(f"{item_path}: likelihoods must cover hidden states")
        weights = {
            hidden: _natural(likelihood[hidden], f"{item_path}.likelihood_weights.{hidden}")
            for hidden in prior
        }
        if sum(prior[hidden] * weights[hidden] for hidden in prior) <= 0:
            raise ValidationError(f"{item_path}: observation has zero posterior mass")
        observations.append(Observation(
            id=_string(obj["id"], f"{item_path}.id"),
            likelihood_weights=weights,
        ))
    if len({observation.id for observation in observations}) != len(observations):
        raise ValidationError("$.observations: ids must be unique")
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        prior_weights=prior,
        actions=tuple(actions),
        observations=tuple(observations),
        query_cost_bps=_natural(raw["query_cost_bps"], "$.query_cost_bps"),
    )
