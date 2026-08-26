from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-temporal-noninterference-v1"
MAX_ENGINES = 12
MAX_MUTATION_OPERATIONS = 12
REPRESENTATIONS = {"date", "timestamp", "epoch"}
SEMANTICS = {
    "causal_forward_fill",
    "observation_only_forward_fill",
    "global_last_fill",
    "mutating_global_last_fill",
    "bidirectional_interpolation",
}


@dataclass(frozen=True)
class Point:
    id: str
    observation_time: int
    available_time: int
    value: int
    representation: str


@dataclass(frozen=True)
class EngineSpec:
    id: str
    semantics: str
    threshold: int


@dataclass(frozen=True)
class Operation:
    kind: str
    data: dict[str, Any]


@dataclass(frozen=True)
class Mutation:
    id: str
    description: str
    operations: tuple[Operation, ...]


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    cutoff_time: int
    decision_times: tuple[int, ...]
    points: tuple[Point, ...]
    engines: tuple[EngineSpec, ...]
    mutations: tuple[Mutation, ...]


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


def _point(value: Any, path: str) -> Point:
    obj = _object(value, path)
    expected = {
        "id", "observation_time", "available_time", "value", "representation"
    }
    if set(obj) != expected:
        raise ValidationError(f"{path}: fields do not match point schema")
    representation = _string(obj["representation"], f"{path}.representation")
    if representation not in REPRESENTATIONS:
        raise ValidationError(
            f"{path}.representation: expected one of {sorted(REPRESENTATIONS)}"
        )
    return Point(
        id=_string(obj["id"], f"{path}.id"),
        observation_time=_natural(
            obj["observation_time"], f"{path}.observation_time"
        ),
        available_time=_natural(
            obj["available_time"], f"{path}.available_time"
        ),
        value=_integer(obj["value"], f"{path}.value"),
        representation=representation,
    )


def _operation(
    value: Any,
    path: str,
    known_point_ids: set[str],
) -> Operation:
    obj = _object(value, path)
    kind = _string(obj.get("kind"), f"{path}.kind")
    if kind == "append_point":
        if set(obj) != {"kind", "point"}:
            raise ValidationError(f"{path}: invalid append_point fields")
        point = _point(obj["point"], f"{path}.point")
        if point.id in known_point_ids:
            raise ValidationError(f"{path}.point.id: already exists in base data")
        return Operation(kind=kind, data={"point": {
            "id": point.id,
            "observation_time": point.observation_time,
            "available_time": point.available_time,
            "value": point.value,
            "representation": point.representation,
        }})
    if kind == "revise_value":
        if set(obj) != {"kind", "point_id", "value"}:
            raise ValidationError(f"{path}: invalid revise_value fields")
        point_id = _string(obj["point_id"], f"{path}.point_id")
        if point_id not in known_point_ids:
            raise ValidationError(f"{path}.point_id: unknown base point")
        return Operation(kind=kind, data={
            "point_id": point_id,
            "value": _integer(obj["value"], f"{path}.value"),
        })
    if kind == "reorder":
        if set(obj) != {"kind", "order"}:
            raise ValidationError(f"{path}: invalid reorder fields")
        order = obj["order"]
        if not isinstance(order, list) or any(
            not isinstance(point_id, str) or not point_id for point_id in order
        ):
            raise ValidationError(f"{path}.order: expected point-id array")
        if len(order) != len(set(order)):
            raise ValidationError(f"{path}.order: duplicates are not allowed")
        if set(order) != known_point_ids:
            raise ValidationError(
                f"{path}.order: must contain every base point exactly once"
            )
        return Operation(kind=kind, data={"order": list(order)})
    if kind == "change_representation":
        if set(obj) != {"kind", "point_id", "representation"}:
            raise ValidationError(
                f"{path}: invalid change_representation fields"
            )
        point_id = _string(obj["point_id"], f"{path}.point_id")
        if point_id not in known_point_ids:
            raise ValidationError(f"{path}.point_id: unknown base point")
        representation = _string(
            obj["representation"], f"{path}.representation"
        )
        if representation not in REPRESENTATIONS:
            raise ValidationError(
                f"{path}.representation: expected one of "
                f"{sorted(REPRESENTATIONS)}"
            )
        return Operation(kind=kind, data={
            "point_id": point_id,
            "representation": representation,
        })
    if kind == "change_availability":
        if set(obj) != {"kind", "point_id", "available_time"}:
            raise ValidationError(
                f"{path}: invalid change_availability fields"
            )
        point_id = _string(obj["point_id"], f"{path}.point_id")
        if point_id not in known_point_ids:
            raise ValidationError(f"{path}.point_id: unknown base point")
        return Operation(kind=kind, data={
            "point_id": point_id,
            "available_time": _natural(
                obj["available_time"], f"{path}.available_time"
            ),
        })
    raise ValidationError(f"{path}.kind: unsupported operation {kind}")


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version", "name", "cutoff_time", "decision_times",
        "points", "engines", "mutations",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")

    cutoff_time = _natural(raw["cutoff_time"], "$.cutoff_time")
    decision_times_raw = raw["decision_times"]
    if not isinstance(decision_times_raw, list) or not decision_times_raw:
        raise ValidationError("$.decision_times: expected non-empty array")
    decision_times = tuple(
        _natural(value, f"$.decision_times[{index}]")
        for index, value in enumerate(decision_times_raw)
    )
    if tuple(sorted(decision_times)) != decision_times:
        raise ValidationError("$.decision_times: must be sorted")
    if len(set(decision_times)) != len(decision_times):
        raise ValidationError("$.decision_times: duplicates are not allowed")
    if decision_times[-1] > cutoff_time:
        raise ValidationError(
            "$.decision_times: every decision must be at or before cutoff"
        )

    points_raw = raw["points"]
    if not isinstance(points_raw, list) or not points_raw:
        raise ValidationError("$.points: expected non-empty array")
    points = tuple(
        _point(item, f"$.points[{index}]")
        for index, item in enumerate(points_raw)
    )
    point_ids = [point.id for point in points]
    if len(set(point_ids)) != len(point_ids):
        raise ValidationError("$.points: ids must be unique")
    known_point_ids = set(point_ids)

    engines_raw = raw["engines"]
    if not isinstance(engines_raw, list) or not engines_raw:
        raise ValidationError("$.engines: expected non-empty array")
    if len(engines_raw) > MAX_ENGINES:
        raise ValidationError(
            f"$.engines: maximum exact benchmark size is {MAX_ENGINES}"
        )
    engines: list[EngineSpec] = []
    for index, item in enumerate(engines_raw):
        item_path = f"$.engines[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "semantics", "threshold"}:
            raise ValidationError(
                f"{item_path}: fields do not match engine schema"
            )
        semantics = _string(obj["semantics"], f"{item_path}.semantics")
        if semantics not in SEMANTICS:
            raise ValidationError(
                f"{item_path}.semantics: expected one of {sorted(SEMANTICS)}"
            )
        engines.append(EngineSpec(
            id=_string(obj["id"], f"{item_path}.id"),
            semantics=semantics,
            threshold=_integer(obj["threshold"], f"{item_path}.threshold"),
        ))
    if len({engine.id for engine in engines}) != len(engines):
        raise ValidationError("$.engines: ids must be unique")

    mutations_raw = raw["mutations"]
    if not isinstance(mutations_raw, list) or not mutations_raw:
        raise ValidationError("$.mutations: expected non-empty array")
    mutations: list[Mutation] = []
    for index, item in enumerate(mutations_raw):
        item_path = f"$.mutations[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "description", "operations"}:
            raise ValidationError(
                f"{item_path}: fields do not match mutation schema"
            )
        operations_raw = obj["operations"]
        if not isinstance(operations_raw, list) or not operations_raw:
            raise ValidationError(
                f"{item_path}.operations: expected non-empty array"
            )
        if len(operations_raw) > MAX_MUTATION_OPERATIONS:
            raise ValidationError(
                f"{item_path}.operations: maximum is "
                f"{MAX_MUTATION_OPERATIONS}"
            )
        operations = tuple(
            _operation(
                operation,
                f"{item_path}.operations[{operation_index}]",
                known_point_ids,
            )
            for operation_index, operation in enumerate(operations_raw)
        )
        appended = [
            operation.data["point"]["id"]
            for operation in operations
            if operation.kind == "append_point"
        ]
        if len(set(appended)) != len(appended):
            raise ValidationError(
                f"{item_path}.operations: appended point ids must be unique"
            )
        mutations.append(Mutation(
            id=_string(obj["id"], f"{item_path}.id"),
            description=_string(
                obj["description"], f"{item_path}.description"
            ),
            operations=operations,
        ))
    if len({mutation.id for mutation in mutations}) != len(mutations):
        raise ValidationError("$.mutations: ids must be unique")

    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        cutoff_time=cutoff_time,
        decision_times=decision_times,
        points=points,
        engines=tuple(engines),
        mutations=tuple(mutations),
    )
