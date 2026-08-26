from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-research-version-space-v1"
MAX_DIMENSIONS = 12
MAX_CHANNELS = 16


@dataclass(frozen=True)
class Dimension:
    id: str
    baseline: str
    alternative: str
    alternative_effect: int
    description: str


@dataclass(frozen=True)
class Interaction:
    requires: tuple[str, ...]
    effect: int
    description: str


@dataclass(frozen=True)
class Channel:
    id: str
    cost: int
    restricts: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    base_metric: int
    target_maximum_width: int
    dimensions: tuple[Dimension, ...]
    interactions: tuple[Interaction, ...]
    channels: tuple[Channel, ...]

    @property
    def dimension_by_id(self) -> dict[str, Dimension]:
        return {dimension.id: dimension for dimension in self.dimensions}


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
    expected = {
        "schema_version", "name", "base_metric",
        "target_maximum_width", "dimensions", "interactions", "channels",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")

    dimensions_raw = raw["dimensions"]
    if not isinstance(dimensions_raw, list) or not dimensions_raw:
        raise ValidationError("$.dimensions: expected non-empty array")
    if len(dimensions_raw) > MAX_DIMENSIONS:
        raise ValidationError(
            f"$.dimensions: exact limit is {MAX_DIMENSIONS}"
        )
    dimensions: list[Dimension] = []
    for index, item in enumerate(dimensions_raw):
        item_path = f"$.dimensions[{index}]"
        obj = _object(item, item_path)
        expected_dimension = {
            "id", "baseline", "alternative", "alternative_effect",
            "description",
        }
        if set(obj) != expected_dimension:
            raise ValidationError(
                f"{item_path}: fields do not match dimension schema"
            )
        baseline = _string(obj["baseline"], f"{item_path}.baseline")
        alternative = _string(
            obj["alternative"], f"{item_path}.alternative"
        )
        if baseline == alternative:
            raise ValidationError(
                f"{item_path}: baseline and alternative must differ"
            )
        dimensions.append(Dimension(
            id=_string(obj["id"], f"{item_path}.id"),
            baseline=baseline,
            alternative=alternative,
            alternative_effect=_integer(
                obj["alternative_effect"],
                f"{item_path}.alternative_effect",
            ),
            description=_string(
                obj["description"], f"{item_path}.description"
            ),
        ))
    dimension_ids = [dimension.id for dimension in dimensions]
    if len(set(dimension_ids)) != len(dimension_ids):
        raise ValidationError("$.dimensions: ids must be unique")
    known_dimensions = set(dimension_ids)

    interactions_raw = raw["interactions"]
    if not isinstance(interactions_raw, list):
        raise ValidationError("$.interactions: expected array")
    interactions: list[Interaction] = []
    seen_interactions: set[tuple[str, ...]] = set()
    for index, item in enumerate(interactions_raw):
        item_path = f"$.interactions[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"requires", "effect", "description"}:
            raise ValidationError(
                f"{item_path}: fields do not match interaction schema"
            )
        requires_raw = obj["requires"]
        if not isinstance(requires_raw, list) or len(requires_raw) < 2:
            raise ValidationError(
                f"{item_path}.requires: expected at least two dimensions"
            )
        if any(
            not isinstance(dimension, str) or not dimension
            for dimension in requires_raw
        ):
            raise ValidationError(
                f"{item_path}.requires: expected string array"
            )
        requires = tuple(sorted(requires_raw))
        if len(set(requires)) != len(requires):
            raise ValidationError(
                f"{item_path}.requires: duplicates are not allowed"
            )
        if not set(requires).issubset(known_dimensions):
            raise ValidationError(
                f"{item_path}.requires: unknown dimension"
            )
        if requires in seen_interactions:
            raise ValidationError(
                f"{item_path}.requires: duplicate interaction"
            )
        seen_interactions.add(requires)
        interactions.append(Interaction(
            requires=requires,
            effect=_integer(obj["effect"], f"{item_path}.effect"),
            description=_string(
                obj["description"], f"{item_path}.description"
            ),
        ))

    channels_raw = raw["channels"]
    if not isinstance(channels_raw, list) or not channels_raw:
        raise ValidationError("$.channels: expected non-empty array")
    if len(channels_raw) > MAX_CHANNELS:
        raise ValidationError(f"$.channels: exact limit is {MAX_CHANNELS}")
    channels: list[Channel] = []
    for index, item in enumerate(channels_raw):
        item_path = f"$.channels[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "cost", "restricts", "description"}:
            raise ValidationError(
                f"{item_path}: fields do not match channel schema"
            )
        restricts_raw = obj["restricts"]
        if not isinstance(restricts_raw, list) or not restricts_raw:
            raise ValidationError(
                f"{item_path}.restricts: expected non-empty array"
            )
        if any(
            not isinstance(dimension, str) or not dimension
            for dimension in restricts_raw
        ):
            raise ValidationError(
                f"{item_path}.restricts: expected strings"
            )
        restricts = tuple(sorted(restricts_raw))
        if len(set(restricts)) != len(restricts):
            raise ValidationError(
                f"{item_path}.restricts: duplicates are not allowed"
            )
        if not set(restricts).issubset(known_dimensions):
            raise ValidationError(
                f"{item_path}.restricts: unknown dimension"
            )
        channels.append(Channel(
            id=_string(obj["id"], f"{item_path}.id"),
            cost=_natural(obj["cost"], f"{item_path}.cost"),
            restricts=restricts,
            description=_string(
                obj["description"], f"{item_path}.description"
            ),
        ))
    if len({channel.id for channel in channels}) != len(channels):
        raise ValidationError("$.channels: ids must be unique")

    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        base_metric=_integer(raw["base_metric"], "$.base_metric"),
        target_maximum_width=_natural(
            raw["target_maximum_width"], "$.target_maximum_width"
        ),
        dimensions=tuple(dimensions),
        interactions=tuple(interactions),
        channels=tuple(channels),
    )
