from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.model import EvidenceModel

from .errors import ValidationError

POLICY_SCHEMA = "lfv-robust-evidence-policy-v1"


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


def _reject_unknown(obj: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        raise ValidationError(f"{path}: unknown fields: {sorted(unknown)}")


@dataclass(frozen=True)
class FaultScenario:
    id: str
    rank: int
    compromised_domains: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class RobustEvidencePolicy:
    source_path: Path
    name: str
    required_connectivity: int
    channel_domains: dict[str, str]
    faults: tuple[FaultScenario, ...]

    @property
    def domains(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.channel_domains.values())))

    @property
    def fault_by_id(self) -> dict[str, FaultScenario]:
        return {fault.id: fault for fault in self.faults}


def load_policy(path: Path, model: EvidenceModel) -> RobustEvidencePolicy:
    source_path = path.resolve()
    raw = _object(load_json(source_path), "$")
    allowed = {
        "schema_version",
        "name",
        "required_connectivity",
        "channel_domains",
        "faults",
    }
    _reject_unknown(raw, allowed, "$")
    if raw.get("schema_version") != POLICY_SCHEMA:
        raise ValidationError(
            f"$.schema_version: expected {POLICY_SCHEMA!r}, "
            f"got {raw.get('schema_version')!r}"
        )
    channel_domains_raw = _object(raw.get("channel_domains"), "$.channel_domains")
    expected_channels = {channel.id for channel in model.channels}
    actual_channels = set(channel_domains_raw)
    if actual_channels != expected_channels:
        raise ValidationError(
            "$.channel_domains: keys must exactly match evidence channels; "
            f"missing={sorted(expected_channels - actual_channels)}, "
            f"extra={sorted(actual_channels - expected_channels)}"
        )
    channel_domains = {
        channel_id: _string(domain, f"$.channel_domains.{channel_id}")
        for channel_id, domain in channel_domains_raw.items()
    }
    domains = set(channel_domains.values())

    faults: list[FaultScenario] = []
    for index, item in enumerate(_array(raw.get("faults"), "$.faults")):
        item_path = f"$.faults[{index}]"
        obj = _object(item, item_path)
        _reject_unknown(
            obj,
            {"id", "rank", "compromised_domains", "description"},
            item_path,
        )
        compromised = tuple(
            _string(value, f"{item_path}.compromised_domains[]")
            for value in _array(
                obj.get("compromised_domains"),
                f"{item_path}.compromised_domains",
            )
        )
        if len(set(compromised)) != len(compromised):
            raise ValidationError(
                f"{item_path}.compromised_domains: duplicates are not allowed"
            )
        unknown_domains = set(compromised) - domains
        if unknown_domains:
            raise ValidationError(
                f"{item_path}.compromised_domains: unknown domains "
                f"{sorted(unknown_domains)}"
            )
        fault_id = _string(obj.get("id"), f"{item_path}.id")
        faults.append(
            FaultScenario(
                id=fault_id,
                rank=_nat(obj.get("rank"), f"{item_path}.rank"),
                compromised_domains=compromised,
                description=_string(
                    obj.get("description", fault_id),
                    f"{item_path}.description",
                ),
            )
        )
    if not faults:
        raise ValidationError("$.faults: expected at least one fault scenario")
    fault_ids = [fault.id for fault in faults]
    if len(set(fault_ids)) != len(fault_ids):
        raise ValidationError("$.faults: ids must be unique")
    if not any(fault.rank == 0 and not fault.compromised_domains for fault in faults):
        raise ValidationError(
            "$.faults: expected a rank-zero no-compromise scenario"
        )
    required_connectivity = _positive(
        raw.get("required_connectivity"), "$.required_connectivity"
    )
    relevant_ranks = {
        fault.rank for fault in faults if fault.rank < required_connectivity
    }
    if 0 not in relevant_ranks:
        raise ValidationError(
            "fault policy does not exercise the no-fault connectivity level"
        )
    return RobustEvidencePolicy(
        source_path=source_path,
        name=_string(raw.get("name"), "$.name"),
        required_connectivity=required_connectivity,
        channel_domains=channel_domains,
        faults=tuple(faults),
    )
