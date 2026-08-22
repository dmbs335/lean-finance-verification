from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_dumps, load_json

from .errors import ValidationError

SCHEMA = "lfv-multiclaim-evidence-v1"
MAX_CHANNELS = 12


@dataclass(frozen=True)
class World:
    id: str
    claims: dict[str, bool]


@dataclass(frozen=True)
class Channel:
    id: str
    cost: int
    observations: dict[str, Any]


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    claim_ids: tuple[str, ...]
    worlds: tuple[World, ...]
    channels: tuple[Channel, ...]

    @property
    def world_by_id(self) -> dict[str, World]:
        return {world.id: world for world in self.worlds}

    def observation_key(self, channel: Channel, world: World) -> str:
        return canonical_dumps(channel.observations[world.id])


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def load_problem(path: Path) -> Problem:
    raw = _object(load_json(path), "$")
    if raw.get("schema_version") != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")
    claim_ids = tuple(raw.get("claims", []))
    if not claim_ids or any(not isinstance(item, str) or not item for item in claim_ids):
        raise ValidationError("$.claims: expected non-empty string ids")
    if len(set(claim_ids)) != len(claim_ids):
        raise ValidationError("$.claims: ids must be unique")
    worlds: list[World] = []
    for index, item in enumerate(raw.get("worlds", [])):
        obj = _object(item, f"$.worlds[{index}]")
        world_id = obj.get("id")
        claims = _object(obj.get("claims"), f"$.worlds[{index}].claims")
        if not isinstance(world_id, str) or not world_id:
            raise ValidationError(f"$.worlds[{index}].id: expected string")
        if set(claims) != set(claim_ids) or any(
            not isinstance(value, bool) for value in claims.values()
        ):
            raise ValidationError(
                f"$.worlds[{index}].claims: keys and booleans must match claims"
            )
        worlds.append(World(world_id, dict(claims)))
    world_ids = [world.id for world in worlds]
    if len(set(world_ids)) != len(world_ids) or len(worlds) < 2:
        raise ValidationError("$.worlds: expected at least two unique worlds")
    channels: list[Channel] = []
    for index, item in enumerate(raw.get("channels", [])):
        obj = _object(item, f"$.channels[{index}]")
        channel_id = obj.get("id")
        cost = obj.get("cost")
        observations = _object(
            obj.get("observations"), f"$.channels[{index}].observations"
        )
        if not isinstance(channel_id, str) or not channel_id:
            raise ValidationError(f"$.channels[{index}].id: expected string")
        if isinstance(cost, bool) or not isinstance(cost, int) or cost < 0:
            raise ValidationError(f"$.channels[{index}].cost: expected natural")
        if set(observations) != set(world_ids):
            raise ValidationError(
                f"$.channels[{index}].observations: keys must match worlds"
            )
        channels.append(Channel(channel_id, cost, dict(observations)))
    if not channels or len(channels) > MAX_CHANNELS:
        raise ValidationError(
            f"$.channels: expected between 1 and {MAX_CHANNELS} channels"
        )
    if len({channel.id for channel in channels}) != len(channels):
        raise ValidationError("$.channels: ids must be unique")
    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise ValidationError("$.name: expected string")
    return Problem(path.resolve(), name, claim_ids, tuple(worlds), tuple(channels))
