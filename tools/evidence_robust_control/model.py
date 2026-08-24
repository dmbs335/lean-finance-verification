from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-evidence-robust-control-v1"


@dataclass(frozen=True)
class Action:
    id: str
    execution_cost_bps: int
    model_values_bps: dict[str, int]


@dataclass(frozen=True)
class Query:
    id: str
    cost_bps: int
    observations: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class CapitalRule:
    robust_value_before_bps: int
    robust_value_after_bps: int
    crowding_cost_before_bps: int
    crowding_cost_after_bps: int


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    current_models: tuple[str, ...]
    actions: tuple[Action, ...]
    queries: tuple[Query, ...]
    capital_rule: CapitalRule


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


def _natural(value: Any, path: str) -> int:
    value = _integer(value, path)
    if value < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return value


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    if set(raw) != {
        "schema_version", "name", "current_models", "actions", "queries",
        "capital_rule",
    } or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")
    models_raw = raw["current_models"]
    if not isinstance(models_raw, list) or not models_raw or any(
        not isinstance(model, str) or not model for model in models_raw
    ):
        raise ValidationError("$.current_models: expected non-empty strings")
    models = tuple(models_raw)
    if len(set(models)) != len(models):
        raise ValidationError("$.current_models: duplicates are not allowed")
    known_models = set(models)

    actions_raw = raw["actions"]
    if not isinstance(actions_raw, list) or not actions_raw:
        raise ValidationError("$.actions: expected non-empty array")
    actions: list[Action] = []
    for index, item in enumerate(actions_raw):
        item_path = f"$.actions[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "execution_cost_bps", "model_values_bps"}:
            raise ValidationError(f"{item_path}: fields do not match")
        values_raw = _object(obj["model_values_bps"], f"{item_path}.model_values_bps")
        if set(values_raw) != known_models:
            raise ValidationError(f"{item_path}: values must cover every model")
        actions.append(Action(
            id=_string(obj["id"], f"{item_path}.id"),
            execution_cost_bps=_natural(
                obj["execution_cost_bps"], f"{item_path}.execution_cost_bps"
            ),
            model_values_bps={
                model: _integer(values_raw[model], f"{item_path}.model_values_bps.{model}")
                for model in models
            },
        ))
    if len({action.id for action in actions}) != len(actions):
        raise ValidationError("$.actions: ids must be unique")

    queries_raw = raw["queries"]
    if not isinstance(queries_raw, list) or not queries_raw:
        raise ValidationError("$.queries: expected non-empty array")
    queries: list[Query] = []
    for index, item in enumerate(queries_raw):
        item_path = f"$.queries[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "cost_bps", "observations"}:
            raise ValidationError(f"{item_path}: fields do not match")
        observations_raw = _object(obj["observations"], f"{item_path}.observations")
        if not observations_raw:
            raise ValidationError(f"{item_path}.observations: expected entries")
        observations: dict[str, tuple[str, ...]] = {}
        for observation, remaining_raw in observations_raw.items():
            if not isinstance(remaining_raw, list) or not remaining_raw or any(
                not isinstance(model, str) or not model for model in remaining_raw
            ):
                raise ValidationError(
                    f"{item_path}.observations.{observation}: expected strings"
                )
            remaining = tuple(remaining_raw)
            if not set(remaining).issubset(known_models):
                raise ValidationError(
                    f"{item_path}.observations.{observation}: unknown model"
                )
            observations[_string(observation, f"{item_path}.observation key")] = remaining
        queries.append(Query(
            id=_string(obj["id"], f"{item_path}.id"),
            cost_bps=_natural(obj["cost_bps"], f"{item_path}.cost_bps"),
            observations=observations,
        ))
    if len({query.id for query in queries}) != len(queries):
        raise ValidationError("$.queries: ids must be unique")

    capital_obj = _object(raw["capital_rule"], "$.capital_rule")
    expected_capital = {
        "robust_value_before_bps", "robust_value_after_bps",
        "crowding_cost_before_bps", "crowding_cost_after_bps",
    }
    if set(capital_obj) != expected_capital:
        raise ValidationError("$.capital_rule: fields do not match")
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        current_models=models,
        actions=tuple(actions),
        queries=tuple(queries),
        capital_rule=CapitalRule(**{
            key: _integer(capital_obj[key], f"$.capital_rule.{key}")
            for key in expected_capital
        }),
    )
