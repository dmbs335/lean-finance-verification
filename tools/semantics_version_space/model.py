from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError

MODEL_SCHEMA = "lfv-action-semantics-version-space-v1"
MAX_VARIABLES = 10


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected an object")
    return value


def _array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{path}: expected an array")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected a non-empty string")
    return value


def _bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path}: expected a boolean")
    return value


def _nat(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected a non-negative integer")
    return value


def _reject_unknown(obj: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        raise ValidationError(f"{path}: unknown fields: {sorted(unknown)}")


@dataclass(frozen=True)
class Variable:
    id: str
    initial: bool
    probe_cost: int
    description: str


@dataclass(frozen=True)
class PositiveObservation:
    before: dict[str, bool]
    after: dict[str, bool]


@dataclass(frozen=True)
class VersionSpaceModel:
    source_path: Path
    name: str
    variables: tuple[Variable, ...]
    effect_fields: tuple[str, ...]
    positive: tuple[PositiveObservation, ...]
    negative: tuple[dict[str, bool], ...]

    @property
    def variable_ids(self) -> tuple[str, ...]:
        return tuple(variable.id for variable in self.variables)

    @property
    def initial_state(self) -> dict[str, bool]:
        return {variable.id: variable.initial for variable in self.variables}


def _state(value: Any, variables: set[str], path: str) -> dict[str, bool]:
    obj = _object(value, path)
    if set(obj) != variables:
        missing = variables - set(obj)
        extra = set(obj) - variables
        raise ValidationError(
            f"{path}: state must define every variable; "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    return {
        variable: _bool(obj[variable], f"{path}.{variable}")
        for variable in obj
    }


def load_model(path: Path) -> VersionSpaceModel:
    source_path = path.resolve()
    raw = _object(load_json(source_path), "$")
    allowed = {
        "schema_version",
        "name",
        "variables",
        "effect_fields",
        "positive_observations",
        "negative_states",
    }
    _reject_unknown(raw, allowed, "$")
    if raw.get("schema_version") != MODEL_SCHEMA:
        raise ValidationError(
            f"$.schema_version: expected {MODEL_SCHEMA!r}, "
            f"got {raw.get('schema_version')!r}"
        )

    variables: list[Variable] = []
    for index, item in enumerate(_array(raw.get("variables"), "$.variables")):
        item_path = f"$.variables[{index}]"
        obj = _object(item, item_path)
        _reject_unknown(
            obj,
            {"id", "initial", "probe_cost", "description"},
            item_path,
        )
        variable_id = _string(obj.get("id"), f"{item_path}.id")
        variables.append(
            Variable(
                id=variable_id,
                initial=_bool(obj.get("initial"), f"{item_path}.initial"),
                probe_cost=_nat(obj.get("probe_cost"), f"{item_path}.probe_cost"),
                description=_string(
                    obj.get("description", variable_id),
                    f"{item_path}.description",
                ),
            )
        )
    if not variables:
        raise ValidationError("$.variables: expected at least one variable")
    if len(variables) > MAX_VARIABLES:
        raise ValidationError(
            f"$.variables: exact probe enumeration supports at most {MAX_VARIABLES} variables"
        )
    variable_ids = [variable.id for variable in variables]
    if len(set(variable_ids)) != len(variable_ids):
        raise ValidationError("$.variables: ids must be unique")
    variable_set = set(variable_ids)

    effect_fields = tuple(
        _string(value, "$.effect_fields[]")
        for value in _array(raw.get("effect_fields"), "$.effect_fields")
    )
    if not effect_fields:
        raise ValidationError("$.effect_fields: expected at least one field")
    if len(set(effect_fields)) != len(effect_fields):
        raise ValidationError("$.effect_fields: duplicates are not allowed")
    unknown_effects = set(effect_fields) - variable_set
    if unknown_effects:
        raise ValidationError(
            f"$.effect_fields: unknown variables {sorted(unknown_effects)}"
        )

    positive: list[PositiveObservation] = []
    for index, item in enumerate(
        _array(raw.get("positive_observations"), "$.positive_observations")
    ):
        item_path = f"$.positive_observations[{index}]"
        obj = _object(item, item_path)
        _reject_unknown(obj, {"before", "after"}, item_path)
        before = _state(obj.get("before"), variable_set, f"{item_path}.before")
        after_obj = _object(obj.get("after"), f"{item_path}.after")
        if set(after_obj) != set(effect_fields):
            raise ValidationError(
                f"{item_path}.after: keys must equal effect_fields"
            )
        after = {
            field: _bool(after_obj[field], f"{item_path}.after.{field}")
            for field in effect_fields
        }
        positive.append(PositiveObservation(before=before, after=after))
    if not positive:
        raise ValidationError(
            "$.positive_observations: expected at least one transition"
        )

    negative = tuple(
        _state(item, variable_set, f"$.negative_states[{index}]")
        for index, item in enumerate(
            _array(raw.get("negative_states", []), "$.negative_states")
        )
    )
    return VersionSpaceModel(
        source_path=source_path,
        name=_string(raw.get("name"), "$.name"),
        variables=tuple(variables),
        effect_fields=effect_fields,
        positive=tuple(positive),
        negative=negative,
    )
