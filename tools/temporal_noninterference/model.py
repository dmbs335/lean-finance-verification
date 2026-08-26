from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-temporal-noninterference-v1"
ALLOWED_OPERATIONS = {
    "direct_exact",
    "causal_forward_fill",
    "causal_trailing_mean",
    "append_tail_forward_fill",
    "two_sided_interpolation",
}


@dataclass(frozen=True)
class Observation:
    id: str
    time: int
    available_at: int
    value: int


@dataclass(frozen=True)
class Pipeline:
    id: str
    operation: str
    threshold: int
    window: int


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    cutoff: int
    query_times: tuple[int, ...]
    base_history: tuple[Observation, ...]
    extended_history: tuple[Observation, ...]
    pipelines: tuple[Pipeline, ...]


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


def _observations(value: Any, path: str) -> tuple[Observation, ...]:
    if not isinstance(value, list) or not value:
        raise ValidationError(f"{path}: expected non-empty array")
    result: list[Observation] = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "time", "available_at", "value"}:
            raise ValidationError(
                f"{item_path}: fields do not match observation schema"
            )
        result.append(
            Observation(
                id=_string(obj["id"], f"{item_path}.id"),
                time=_natural(obj["time"], f"{item_path}.time"),
                available_at=_natural(
                    obj["available_at"], f"{item_path}.available_at"
                ),
                value=_integer(obj["value"], f"{item_path}.value"),
            )
        )
    if len({item.id for item in result}) != len(result):
        raise ValidationError(f"{path}: ids must be unique")
    if len({item.time for item in result}) != len(result):
        raise ValidationError(f"{path}: observation times must be unique")
    return tuple(result)


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version",
        "name",
        "cutoff",
        "query_times",
        "base_history",
        "extended_history",
        "pipelines",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")

    cutoff = _natural(raw["cutoff"], "$.cutoff")
    query_raw = raw["query_times"]
    if not isinstance(query_raw, list) or not query_raw:
        raise ValidationError("$.query_times: expected non-empty array")
    query_times = tuple(
        _natural(value, f"$.query_times[{index}]")
        for index, value in enumerate(query_raw)
    )
    if query_times != tuple(sorted(query_times)):
        raise ValidationError("$.query_times: values must be sorted")
    if len(set(query_times)) != len(query_times):
        raise ValidationError("$.query_times: values must be unique")
    if any(value > cutoff for value in query_times):
        raise ValidationError("$.query_times: every query must be within cutoff")

    base = _observations(raw["base_history"], "$.base_history")
    extended = _observations(
        raw["extended_history"], "$.extended_history"
    )
    extended_by_id = {item.id: item for item in extended}
    for item in base:
        if extended_by_id.get(item.id) != item:
            raise ValidationError(
                "$.extended_history must preserve every base observation exactly"
            )
    extras = [item for item in extended if item.id not in {x.id for x in base}]
    if not extras:
        raise ValidationError("$.extended_history: expected a future extension")
    if any(item.available_at <= cutoff for item in extras):
        raise ValidationError(
            "$.extended_history: added observations must be unavailable by cutoff"
        )

    pipelines_raw = raw["pipelines"]
    if not isinstance(pipelines_raw, list) or not pipelines_raw:
        raise ValidationError("$.pipelines: expected non-empty array")
    pipelines: list[Pipeline] = []
    for index, item in enumerate(pipelines_raw):
        item_path = f"$.pipelines[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "operation", "threshold", "window"}:
            raise ValidationError(
                f"{item_path}: fields do not match pipeline schema"
            )
        operation = _string(obj["operation"], f"{item_path}.operation")
        if operation not in ALLOWED_OPERATIONS:
            raise ValidationError(
                f"{item_path}.operation: unsupported operation {operation}"
            )
        window = _natural(obj["window"], f"{item_path}.window", positive=True)
        pipelines.append(
            Pipeline(
                id=_string(obj["id"], f"{item_path}.id"),
                operation=operation,
                threshold=_integer(obj["threshold"], f"{item_path}.threshold"),
                window=window,
            )
        )
    if len({item.id for item in pipelines}) != len(pipelines):
        raise ValidationError("$.pipelines: ids must be unique")

    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        cutoff=cutoff,
        query_times=query_times,
        base_history=base,
        extended_history=extended,
        pipelines=tuple(pipelines),
    )
