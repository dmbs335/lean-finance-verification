from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json

from .errors import ValidationError

SCHEMA = "lfv-attack-evidence-corpus-v1"
MAX_CHANNELS = 30
MAX_ATTACKS = 120


@dataclass(frozen=True)
class Channel:
    id: str
    cost: int
    description: str


@dataclass(frozen=True)
class Attack:
    id: str
    category: str
    boundary: str
    separators: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class Corpus:
    source: Path
    name: str
    channels: tuple[Channel, ...]
    attacks: tuple[Attack, ...]

    @property
    def channel_by_id(self) -> dict[str, Channel]:
        return {channel.id: channel for channel in self.channels}


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def load_corpus(path: Path) -> Corpus:
    raw = _object(load_json(path), "$")
    if raw.get("schema_version") != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")
    channels: list[Channel] = []
    for index, item in enumerate(raw.get("channels", [])):
        obj = _object(item, f"$.channels[{index}]")
        cost = obj.get("cost")
        if isinstance(cost, bool) or not isinstance(cost, int) or cost < 0:
            raise ValidationError(f"$.channels[{index}].cost: expected natural")
        channels.append(Channel(
            id=_string(obj.get("id"), f"$.channels[{index}].id"),
            cost=cost,
            description=_string(obj.get("description", obj.get("id")),
                f"$.channels[{index}].description"),
        ))
    if not channels or len(channels) > MAX_CHANNELS:
        raise ValidationError(
            f"$.channels: expected between 1 and {MAX_CHANNELS} channels"
        )
    channel_ids = [channel.id for channel in channels]
    if len(set(channel_ids)) != len(channel_ids):
        raise ValidationError("$.channels: ids must be unique")
    known = set(channel_ids)

    attacks: list[Attack] = []
    for index, item in enumerate(raw.get("attacks", [])):
        obj = _object(item, f"$.attacks[{index}]")
        separators = tuple(obj.get("separators", []))
        if not separators or any(
            not isinstance(value, str) or value not in known
            for value in separators
        ):
            raise ValidationError(
                f"$.attacks[{index}].separators: expected known non-empty channels"
            )
        if len(set(separators)) != len(separators):
            raise ValidationError(
                f"$.attacks[{index}].separators: duplicates are not allowed"
            )
        attacks.append(Attack(
            id=_string(obj.get("id"), f"$.attacks[{index}].id"),
            category=_string(obj.get("category"), f"$.attacks[{index}].category"),
            boundary=_string(obj.get("boundary"), f"$.attacks[{index}].boundary"),
            separators=separators,
            description=_string(obj.get("description", obj.get("id")),
                f"$.attacks[{index}].description"),
        ))
    if not attacks or len(attacks) > MAX_ATTACKS:
        raise ValidationError(
            f"$.attacks: expected between 1 and {MAX_ATTACKS} attacks"
        )
    if len({attack.id for attack in attacks}) != len(attacks):
        raise ValidationError("$.attacks: ids must be unique")
    name = _string(raw.get("name"), "$.name")
    return Corpus(path.resolve(), name, tuple(channels), tuple(attacks))
