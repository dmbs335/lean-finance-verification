from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-autonomous-pipeline-composition-v1"
ARTIFACT_IDS = (
    "dataset", "state", "policy", "decision", "authorization",
    "execution", "reconciliation",
)
BINDINGS = {
    "datasetState": ("dataset", "state"),
    "stateDecision": ("state", "decision"),
    "policyDecision": ("policy", "decision"),
    "decisionAuthorization": ("decision", "authorization"),
    "authorizationExecution": ("authorization", "execution"),
    "executionReconciliation": ("execution", "reconciliation"),
}


@dataclass(frozen=True)
class Artifact:
    id: str
    sha256: str
    input_sha256: tuple[str, ...]
    local_valid: bool


@dataclass(frozen=True)
class Channel:
    id: str
    kind: str
    cost: int
    covers: tuple[str, ...]


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    artifacts: dict[str, Artifact]
    channels: tuple[Channel, ...]

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


def _natural(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return value


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path}: expected boolean")
    return value


def _digest(value: Any, path: str) -> str:
    result = _string(value, path)
    if len(result) != 64 or any(character not in "0123456789abcdef" for character in result):
        raise ValidationError(f"{path}: expected lowercase SHA-256")
    return result


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    if set(raw) != {"schema_version", "name", "artifacts", "channels"} or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")
    artifacts_raw = _object(raw["artifacts"], "$.artifacts")
    if set(artifacts_raw) != set(ARTIFACT_IDS):
        raise ValidationError("$.artifacts: keys must match autonomous pipeline")
    artifacts: dict[str, Artifact] = {}
    for artifact_id in ARTIFACT_IDS:
        artifact_path = f"$.artifacts.{artifact_id}"
        obj = _object(artifacts_raw[artifact_id], artifact_path)
        if set(obj) != {"sha256", "input_sha256", "local_valid"}:
            raise ValidationError(f"{artifact_path}: fields do not match")
        inputs_raw = obj["input_sha256"]
        if not isinstance(inputs_raw, list) or any(
            not isinstance(item, str) for item in inputs_raw
        ):
            raise ValidationError(f"{artifact_path}.input_sha256: expected strings")
        artifacts[artifact_id] = Artifact(
            id=artifact_id,
            sha256=_digest(obj["sha256"], f"{artifact_path}.sha256"),
            input_sha256=tuple(
                _digest(item, f"{artifact_path}.input_sha256")
                for item in inputs_raw
            ),
            local_valid=_boolean(obj["local_valid"], f"{artifact_path}.local_valid"),
        )
    if not all(artifact.local_valid for artifact in artifacts.values()):
        raise ValidationError("all controlled local certificates must be valid")
    for binding_id, (left, right) in BINDINGS.items():
        if artifacts[left].sha256 not in artifacts[right].input_sha256:
            raise ValidationError(
                f"binding {binding_id} is absent from matched artifact inputs"
            )

    channels_raw = raw["channels"]
    if not isinstance(channels_raw, list) or not channels_raw:
        raise ValidationError("$.channels: expected non-empty array")
    channels: list[Channel] = []
    for index, item in enumerate(channels_raw):
        item_path = f"$.channels[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "kind", "cost", "covers"}:
            raise ValidationError(f"{item_path}: fields do not match")
        kind = _string(obj["kind"], f"{item_path}.kind")
        if kind not in {"local-summary", "bridge", "global-bundle"}:
            raise ValidationError(f"{item_path}.kind: unsupported")
        covers_raw = obj["covers"]
        if not isinstance(covers_raw, list) or any(
            not isinstance(binding, str) or binding not in BINDINGS
            for binding in covers_raw
        ):
            raise ValidationError(f"{item_path}.covers: unknown binding")
        covers = tuple(covers_raw)
        if kind == "bridge" and not covers:
            raise ValidationError(f"{item_path}: bridge must cover a binding")
        if kind != "bridge" and covers:
            raise ValidationError(f"{item_path}: non-bridge cannot declare covers")
        channels.append(Channel(
            id=_string(obj["id"], f"{item_path}.id"),
            kind=kind,
            cost=_natural(obj["cost"], f"{item_path}.cost"),
            covers=covers,
        ))
    if len({channel.id for channel in channels}) != len(channels):
        raise ValidationError("$.channels: ids must be unique")
    if sum(channel.kind == "local-summary" for channel in channels) != 1:
        raise ValidationError("exactly one local-summary channel is required")
    if sum(channel.kind == "global-bundle" for channel in channels) != 1:
        raise ValidationError("exactly one global-bundle channel is required")
    covered = {
        binding for channel in channels if channel.kind == "bridge"
        for binding in channel.covers
    }
    if covered != set(BINDINGS):
        raise ValidationError("bridge channels must cover every binding")
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        artifacts=artifacts,
        channels=tuple(channels),
    )
