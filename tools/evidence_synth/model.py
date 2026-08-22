from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import canonical_dumps, load_json
from .errors import ValidationError

MODEL_SCHEMA = "lfv-evidence-synthesis-model-v1"
MAX_CHANNELS = 12
_NAMESPACE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
_COST_DIMENSIONS = ("operational", "privacy", "trust")


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


def _bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path}: expected a boolean")
    return value


def _reject_unknown(obj: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        raise ValidationError(f"{path}: unknown fields: {sorted(unknown)}")


@dataclass(frozen=True)
class CostVector:
    operational: int
    privacy: int
    trust: int

    def as_dict(self) -> dict[str, int]:
        return {
            "operational": self.operational,
            "privacy": self.privacy,
            "trust": self.trust,
        }

    def weighted(self, weights: CostVector) -> int:
        return (
            self.operational * weights.operational
            + self.privacy * weights.privacy
            + self.trust * weights.trust
        )

    def __add__(self, other: CostVector) -> CostVector:
        return CostVector(
            operational=self.operational + other.operational,
            privacy=self.privacy + other.privacy,
            trust=self.trust + other.trust,
        )


ZERO_COST = CostVector(0, 0, 0)


@dataclass(frozen=True)
class History:
    id: str
    claim: bool
    description: str


@dataclass(frozen=True)
class Channel:
    id: str
    cost: CostVector
    observations: dict[str, Any]
    description: str


@dataclass(frozen=True)
class EvidenceModel:
    source_path: Path
    name: str
    namespace: str
    claim_name: str
    histories: tuple[History, ...]
    channels: tuple[Channel, ...]
    weights: CostVector

    @property
    def history_by_id(self) -> dict[str, History]:
        return {history.id: history for history in self.histories}

    @property
    def channel_by_id(self) -> dict[str, Channel]:
        return {channel.id: channel for channel in self.channels}

    def observation_key(self, channel_id: str, history_id: str) -> str:
        channel = self.channel_by_id[channel_id]
        return canonical_dumps(channel.observations[history_id])

    def weighted_channel_cost(self, channel_id: str) -> int:
        return self.channel_by_id[channel_id].cost.weighted(self.weights)


def _parse_cost(value: Any, path: str) -> CostVector:
    obj = _object(value, path)
    _reject_unknown(obj, set(_COST_DIMENSIONS), path)
    missing = set(_COST_DIMENSIONS) - set(obj)
    if missing:
        raise ValidationError(f"{path}: missing fields: {sorted(missing)}")
    return CostVector(
        operational=_nat(obj["operational"], f"{path}.operational"),
        privacy=_nat(obj["privacy"], f"{path}.privacy"),
        trust=_nat(obj["trust"], f"{path}.trust"),
    )


def load_model(path: Path) -> EvidenceModel:
    source_path = path.resolve()
    raw = _object(load_json(source_path), "$")
    allowed = {
        "schema_version",
        "name",
        "namespace",
        "claim_name",
        "cost_weights",
        "histories",
        "channels",
    }
    _reject_unknown(raw, allowed, "$")
    if raw.get("schema_version") != MODEL_SCHEMA:
        raise ValidationError(
            f"$.schema_version: expected {MODEL_SCHEMA!r}, got {raw.get('schema_version')!r}"
        )
    namespace = _string(raw.get("namespace"), "$.namespace")
    if not _NAMESPACE_RE.fullmatch(namespace):
        raise ValidationError("$.namespace: invalid Lean namespace")
    histories: list[History] = []
    for index, item in enumerate(_array(raw.get("histories"), "$.histories")):
        item_path = f"$.histories[{index}]"
        obj = _object(item, item_path)
        _reject_unknown(obj, {"id", "claim", "description"}, item_path)
        histories.append(
            History(
                id=_string(obj.get("id"), f"{item_path}.id"),
                claim=_bool(obj.get("claim"), f"{item_path}.claim"),
                description=_string(
                    obj.get("description", obj.get("id")),
                    f"{item_path}.description",
                ),
            )
        )
    if len(histories) < 2:
        raise ValidationError("$.histories: expected at least two histories")
    history_ids = [history.id for history in histories]
    if len(set(history_ids)) != len(history_ids):
        raise ValidationError("$.histories: history ids must be unique")
    if len({history.claim for history in histories}) < 2:
        raise ValidationError("$.histories: claim must disagree on at least one pair")

    channels: list[Channel] = []
    for index, item in enumerate(_array(raw.get("channels"), "$.channels")):
        item_path = f"$.channels[{index}]"
        obj = _object(item, item_path)
        _reject_unknown(obj, {"id", "cost", "observations", "description"}, item_path)
        observations = _object(obj.get("observations"), f"{item_path}.observations")
        if set(observations) != set(history_ids):
            missing = set(history_ids) - set(observations)
            extra = set(observations) - set(history_ids)
            raise ValidationError(
                f"{item_path}.observations: keys must equal histories; "
                f"missing={sorted(missing)}, extra={sorted(extra)}"
            )
        channels.append(
            Channel(
                id=_string(obj.get("id"), f"{item_path}.id"),
                cost=_parse_cost(obj.get("cost"), f"{item_path}.cost"),
                observations=dict(observations),
                description=_string(
                    obj.get("description", obj.get("id")),
                    f"{item_path}.description",
                ),
            )
        )
    if not channels:
        raise ValidationError("$.channels: expected at least one channel")
    if len(channels) > MAX_CHANNELS:
        raise ValidationError(
            f"$.channels: exact synthesis supports at most {MAX_CHANNELS} channels"
        )
    channel_ids = [channel.id for channel in channels]
    if len(set(channel_ids)) != len(channel_ids):
        raise ValidationError("$.channels: channel ids must be unique")

    weights = _parse_cost(raw.get("cost_weights"), "$.cost_weights")
    if weights == ZERO_COST:
        raise ValidationError("$.cost_weights: at least one dimension must have positive weight")
    return EvidenceModel(
        source_path=source_path,
        name=_string(raw.get("name"), "$.name"),
        namespace=namespace,
        claim_name=_string(raw.get("claim_name"), "$.claim_name"),
        histories=tuple(histories),
        channels=tuple(channels),
        weights=weights,
    )
