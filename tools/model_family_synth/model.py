from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_dumps, load_json

from .errors import ValidationError

SCHEMA_VERSION = "lfv-model-family-evidence-v1"
MAX_CHANNELS = 12


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


def _nat(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected a non-negative integer")
    return value


@dataclass(frozen=True)
class Model:
    id: str
    consistent: bool
    description: str


@dataclass(frozen=True)
class World:
    id: str
    model: str
    claim: bool
    description: str


@dataclass(frozen=True)
class Channel:
    id: str
    cost: int
    observations: dict[str, Any]
    description: str


@dataclass(frozen=True)
class FamilyProblem:
    source_path: Path
    name: str
    chosen_model: str
    models: tuple[Model, ...]
    worlds: tuple[World, ...]
    channels: tuple[Channel, ...]

    @property
    def model_by_id(self) -> dict[str, Model]:
        return {model.id: model for model in self.models}

    @property
    def world_by_id(self) -> dict[str, World]:
        return {world.id: world for world in self.worlds}

    def observation_key(self, channel_id: str, world_id: str) -> str:
        channel = next(channel for channel in self.channels if channel.id == channel_id)
        return canonical_dumps(channel.observations[world_id])

    @property
    def allowed_worlds(self) -> tuple[World, ...]:
        consistent = {model.id for model in self.models if model.consistent}
        return tuple(world for world in self.worlds if world.model in consistent)


def load_problem(path: Path) -> FamilyProblem:
    raw = _object(load_json(path), "$")
    allowed_fields = {
        "schema_version", "name", "chosen_model", "models", "worlds", "channels"
    }
    unknown = set(raw) - allowed_fields
    if unknown:
        raise ValidationError(f"$: unknown fields: {sorted(unknown)}")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ValidationError(
            f"$.schema_version: expected {SCHEMA_VERSION!r}"
        )
    models: list[Model] = []
    for index, item in enumerate(_array(raw.get("models"), "$.models")):
        obj = _object(item, f"$.models[{index}]")
        models.append(Model(
            id=_string(obj.get("id"), f"$.models[{index}].id"),
            consistent=bool(obj.get("consistent")),
            description=_string(obj.get("description", obj.get("id")),
                f"$.models[{index}].description"),
        ))
    model_ids = [model.id for model in models]
    if len(set(model_ids)) != len(model_ids):
        raise ValidationError("$.models: ids must be unique")
    chosen_model = _string(raw.get("chosen_model"), "$.chosen_model")
    if chosen_model not in set(model_ids):
        raise ValidationError("$.chosen_model: unknown model")

    worlds: list[World] = []
    for index, item in enumerate(_array(raw.get("worlds"), "$.worlds")):
        obj = _object(item, f"$.worlds[{index}]")
        model_id = _string(obj.get("model"), f"$.worlds[{index}].model")
        if model_id not in set(model_ids):
            raise ValidationError(f"$.worlds[{index}].model: unknown model")
        claim = obj.get("claim")
        if not isinstance(claim, bool):
            raise ValidationError(f"$.worlds[{index}].claim: expected boolean")
        worlds.append(World(
            id=_string(obj.get("id"), f"$.worlds[{index}].id"),
            model=model_id,
            claim=claim,
            description=_string(obj.get("description", obj.get("id")),
                f"$.worlds[{index}].description"),
        ))
    world_ids = [world.id for world in worlds]
    if len(set(world_ids)) != len(world_ids):
        raise ValidationError("$.worlds: ids must be unique")
    if not worlds:
        raise ValidationError("$.worlds: expected at least one world")

    channels: list[Channel] = []
    for index, item in enumerate(_array(raw.get("channels"), "$.channels")):
        obj = _object(item, f"$.channels[{index}]")
        observations = _object(
            obj.get("observations"), f"$.channels[{index}].observations"
        )
        if set(observations) != set(world_ids):
            raise ValidationError(
                f"$.channels[{index}].observations: keys must equal world ids"
            )
        channels.append(Channel(
            id=_string(obj.get("id"), f"$.channels[{index}].id"),
            cost=_nat(obj.get("cost"), f"$.channels[{index}].cost"),
            observations=dict(observations),
            description=_string(obj.get("description", obj.get("id")),
                f"$.channels[{index}].description"),
        ))
    channel_ids = [channel.id for channel in channels]
    if len(set(channel_ids)) != len(channel_ids):
        raise ValidationError("$.channels: ids must be unique")
    if not channels or len(channels) > MAX_CHANNELS:
        raise ValidationError(
            f"$.channels: expected between 1 and {MAX_CHANNELS} channels"
        )
    return FamilyProblem(
        source_path=path.resolve(),
        name=_string(raw.get("name"), "$.name"),
        chosen_model=chosen_model,
        models=tuple(models),
        worlds=tuple(worlds),
        channels=tuple(channels),
    )
