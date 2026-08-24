from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-certificate-composition-v1"
MAX_CHANNELS = 16


@dataclass(frozen=True)
class Component:
    id: str
    description: str


@dataclass(frozen=True)
class Binding:
    id: str
    left: str
    right: str
    channel_id: str
    cost: int
    description: str


@dataclass(frozen=True)
class Channel:
    id: str
    cost: int
    description: str
    kind: str
    binding_id: str | None = None


@dataclass(frozen=True)
class World:
    id: str
    local_claims: dict[str, bool]
    bindings: dict[str, bool]
    global_claim: bool


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    components: tuple[Component, ...]
    bindings: tuple[Binding, ...]
    local_summary_channel: Channel
    global_bundle_channel: Channel
    worlds: tuple[World, ...]

    @property
    def channels(self) -> tuple[Channel, ...]:
        binding_channels = tuple(
            Channel(
                id=binding.channel_id,
                cost=binding.cost,
                description=binding.description,
                kind="binding",
                binding_id=binding.id,
            )
            for binding in self.bindings
        )
        return (
            self.local_summary_channel,
            *binding_channels,
            self.global_bundle_channel,
        )

    @property
    def channel_by_id(self) -> dict[str, Channel]:
        return {channel.id: channel for channel in self.channels}

    def observation(self, world: World, channel_id: str) -> object:
        channel = self.channel_by_id[channel_id]
        if channel.kind == "local-summary":
            return tuple(
                world.local_claims[component.id]
                for component in self.components
            )
        if channel.kind == "binding":
            assert channel.binding_id is not None
            return world.bindings[channel.binding_id]
        if channel.kind == "global-bundle":
            return world.global_claim
        raise AssertionError(f"unknown channel kind {channel.kind}")


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def _natural(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return value


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path}: expected boolean")
    return value


def _channel(value: Any, path: str, kind: str) -> Channel:
    obj = _object(value, path)
    if set(obj) != {"id", "cost", "description"}:
        raise ValidationError(f"{path}: fields do not match channel schema")
    return Channel(
        id=_string(obj["id"], f"{path}.id"),
        cost=_natural(obj["cost"], f"{path}.cost"),
        description=_string(obj["description"], f"{path}.description"),
        kind=kind,
    )


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version",
        "name",
        "components",
        "bindings",
        "local_summary_channel",
        "global_bundle_channel",
        "worlds",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")

    components_raw = raw["components"]
    if not isinstance(components_raw, list) or len(components_raw) < 2:
        raise ValidationError("$.components: expected at least two components")
    components: list[Component] = []
    for index, item in enumerate(components_raw):
        item_path = f"$.components[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "description"}:
            raise ValidationError(f"{item_path}: fields do not match component schema")
        components.append(
            Component(
                id=_string(obj["id"], f"{item_path}.id"),
                description=_string(
                    obj["description"], f"{item_path}.description"
                ),
            )
        )
    component_ids = [component.id for component in components]
    if len(set(component_ids)) != len(component_ids):
        raise ValidationError("$.components: ids must be unique")
    known_components = set(component_ids)

    bindings_raw = raw["bindings"]
    if not isinstance(bindings_raw, list) or not bindings_raw:
        raise ValidationError("$.bindings: expected non-empty array")
    bindings: list[Binding] = []
    for index, item in enumerate(bindings_raw):
        item_path = f"$.bindings[{index}]"
        obj = _object(item, item_path)
        expected_binding = {
            "id", "left", "right", "channel_id", "cost", "description"
        }
        if set(obj) != expected_binding:
            raise ValidationError(f"{item_path}: fields do not match binding schema")
        left = _string(obj["left"], f"{item_path}.left")
        right = _string(obj["right"], f"{item_path}.right")
        if left not in known_components or right not in known_components:
            raise ValidationError(f"{item_path}: binding references unknown component")
        if left == right:
            raise ValidationError(f"{item_path}: binding endpoints must differ")
        bindings.append(
            Binding(
                id=_string(obj["id"], f"{item_path}.id"),
                left=left,
                right=right,
                channel_id=_string(
                    obj["channel_id"], f"{item_path}.channel_id"
                ),
                cost=_natural(obj["cost"], f"{item_path}.cost"),
                description=_string(
                    obj["description"], f"{item_path}.description"
                ),
            )
        )
    binding_ids = [binding.id for binding in bindings]
    if len(set(binding_ids)) != len(binding_ids):
        raise ValidationError("$.bindings: ids must be unique")
    known_bindings = set(binding_ids)

    local_summary = _channel(
        raw["local_summary_channel"],
        "$.local_summary_channel",
        "local-summary",
    )
    global_bundle = _channel(
        raw["global_bundle_channel"],
        "$.global_bundle_channel",
        "global-bundle",
    )
    channel_ids = [
        local_summary.id,
        *(binding.channel_id for binding in bindings),
        global_bundle.id,
    ]
    if len(channel_ids) > MAX_CHANNELS:
        raise ValidationError(
            f"channel count exceeds exact-solver limit {MAX_CHANNELS}"
        )
    if len(set(channel_ids)) != len(channel_ids):
        raise ValidationError("channel ids must be unique")

    worlds_raw = raw["worlds"]
    if not isinstance(worlds_raw, list) or len(worlds_raw) < 2:
        raise ValidationError("$.worlds: expected at least two worlds")
    worlds: list[World] = []
    for index, item in enumerate(worlds_raw):
        item_path = f"$.worlds[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "local_claims", "bindings", "global_claim"}:
            raise ValidationError(f"{item_path}: fields do not match world schema")
        local_raw = _object(obj["local_claims"], f"{item_path}.local_claims")
        if set(local_raw) != known_components:
            raise ValidationError(
                f"{item_path}.local_claims: keys must match components"
            )
        local_claims = {
            component_id: _boolean(
                local_raw[component_id],
                f"{item_path}.local_claims.{component_id}",
            )
            for component_id in component_ids
        }
        binding_raw = _object(obj["bindings"], f"{item_path}.bindings")
        if set(binding_raw) != known_bindings:
            raise ValidationError(
                f"{item_path}.bindings: keys must match declared bindings"
            )
        binding_values = {
            binding_id: _boolean(
                binding_raw[binding_id],
                f"{item_path}.bindings.{binding_id}",
            )
            for binding_id in binding_ids
        }
        global_claim = _boolean(
            obj["global_claim"], f"{item_path}.global_claim"
        )
        expected_global = all(local_claims.values()) and all(
            binding_values.values()
        )
        if global_claim != expected_global:
            raise ValidationError(
                f"{item_path}.global_claim does not equal local claims and bindings"
            )
        worlds.append(
            World(
                id=_string(obj["id"], f"{item_path}.id"),
                local_claims=local_claims,
                bindings=binding_values,
                global_claim=global_claim,
            )
        )
    if len({world.id for world in worlds}) != len(worlds):
        raise ValidationError("$.worlds: ids must be unique")
    claims = {world.global_claim for world in worlds}
    if claims != {False, True}:
        raise ValidationError("$.worlds: expected both true and false global claims")

    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        components=tuple(components),
        bindings=tuple(bindings),
        local_summary_channel=local_summary,
        global_bundle_channel=global_bundle,
        worlds=tuple(worlds),
    )
