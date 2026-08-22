from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_dumps, load_json
from tools.evidence_synth.errors import ValidationError

MODEL_SCHEMA = "lfv-robust-evidence-model-v1"
MAX_CHANNELS = 12
MAX_DOMAINS = 8
_NAMESPACE_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$"
)


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


def _positive(value: Any, path: str) -> int:
    result = _nat(value, path)
    if result == 0:
        raise ValidationError(f"{path}: expected a positive integer")
    return result


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
            self.operational + other.operational,
            self.privacy + other.privacy,
            self.trust + other.trust,
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
    domain: str
    cost: CostVector
    observations: dict[str, Any]
    description: str


@dataclass(frozen=True)
class RobustEvidenceModel:
    source_path: Path
    name: str
    namespace: str
    claim_name: str
    required_connectivity: int
    weights: CostVector
    histories: tuple[History, ...]
    channels: tuple[Channel, ...]
    domains: tuple[str, ...]

    @property
    def channel_by_id(self) -> dict[str, Channel]:
        return {channel.id: channel for channel in self.channels}

    def observation_key(self, channel_id: str, history_id: str) -> str:
        return canonical_dumps(
            self.channel_by_id[channel_id].observations[history_id]
        )

    def weighted_channel_cost(self, channel_id: str) -> int:
        return self.channel_by_id[channel_id].cost.weighted(self.weights)


def _parse_cost(value: Any, path: str) -> CostVector:
    obj = _object(value, path)
    expected = {"operational", "privacy", "trust"}
    _reject_unknown(obj, expected, path)
    missing = expected - set(obj)
    if missing:
        raise ValidationError(f"{path}: missing fields: {sorted(missing)}")
    return CostVector(
        operational=_nat(obj["operational"], f"{path}.operational"),
        privacy=_nat(obj["privacy"], f"{path}.privacy"),
        trust=_nat(obj["trust"], f"{path}.trust"),
    )


def load_model(path: Path) -> RobustEvidenceModel:
    source_path = path.resolve()
    raw = _object(load_json(source_path), "$")
    allowed = {
        "schema_version",
        "name",
        "namespace",
        "claim_name",
        "required_connectivity",
        "cost_weights",
        "histories",
        "channels",
    }
    _reject_unknown(raw, allowed, "$")
    if raw.get("schema_version") != MODEL_SCHEMA:
        raise ValidationError(
            f"$.schema_version: expected {MODEL_SCHEMA!r}, "
            f"got {raw.get('schema_version')!r}"
        )
    namespace = _string(raw.get("namespace"), "$.namespace")
    if not _NAMESPACE_RE.fullmatch(namespace):
        raise ValidationError("$.namespace: invalid Lean namespace")

    histories: list[History] = []
    for index, item in enumerate(_array(raw.get("histories"), "$.histories")):
        item_path = f"$.histories[{index}]"
        obj = _object(item, item_path)
        _reject_unknown(obj, {"id", "claim", "description"}, item_path)
        history_id = _string(obj.get("id"), f"{item_path}.id")
        histories.append(
            History(
                id=history_id,
                claim=_bool(obj.get("claim"), f"{item_path}.claim"),
                description=_string(
                    obj.get("description", history_id),
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
        raise ValidationError(
            "$.histories: expected at least one claim-disagreement pair"
        )

    channels: list[Channel] = []
    domains: list[str] = []
    for index, item in enumerate(_array(raw.get("channels"), "$.channels")):
        item_path = f"$.channels[{index}]"
        obj = _object(item, item_path)
        _reject_unknown(
            obj,
            {"id", "domain", "cost", "observations", "description"},
            item_path,
        )
        channel_id = _string(obj.get("id"), f"{item_path}.id")
        domain = _string(obj.get("domain"), f"{item_path}.domain")
        observations = _object(
            obj.get("observations"), f"{item_path}.observations"
        )
        if set(observations) != set(history_ids):
            missing = set(history_ids) - set(observations)
            extra = set(observations) - set(history_ids)
            raise ValidationError(
                f"{item_path}.observations: keys must equal histories; "
                f"missing={sorted(missing)}, extra={sorted(extra)}"
            )
        channels.append(
            Channel(
                id=channel_id,
                domain=domain,
                cost=_parse_cost(obj.get("cost"), f"{item_path}.cost"),
                observations=dict(observations),
                description=_string(
                    obj.get("description", channel_id),
                    f"{item_path}.description",
                ),
            )
        )
        if domain not in domains:
            domains.append(domain)
    if not channels:
        raise ValidationError("$.channels: expected at least one channel")
    if len(channels) > MAX_CHANNELS:
        raise ValidationError(
            f"$.channels: exact synthesis supports at most {MAX_CHANNELS} channels"
        )
    channel_ids = [channel.id for channel in channels]
    if len(set(channel_ids)) != len(channel_ids):
        raise ValidationError("$.channels: channel ids must be unique")
    if len(domains) > MAX_DOMAINS:
        raise ValidationError(
            f"$.channels: exact fault enumeration supports at most {MAX_DOMAINS} domains"
        )

    required_connectivity = _positive(
        raw.get("required_connectivity"), "$.required_connectivity"
    )
    if required_connectivity > len(domains) + 1:
        raise ValidationError(
            "$.required_connectivity: exceeds the finite trust-domain universe"
        )
    weights = _parse_cost(raw.get("cost_weights"), "$.cost_weights")
    if weights == ZERO_COST:
        raise ValidationError(
            "$.cost_weights: at least one dimension must have positive weight"
        )
    return RobustEvidenceModel(
        source_path=source_path,
        name=_string(raw.get("name"), "$.name"),
        namespace=namespace,
        claim_name=_string(raw.get("claim_name"), "$.claim_name"),
        required_connectivity=required_connectivity,
        weights=weights,
        histories=tuple(histories),
        channels=tuple(channels),
        domains=tuple(domains),
    )
