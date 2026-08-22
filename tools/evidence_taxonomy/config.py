from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError

CONFIG_SCHEMA = "lfv-evidence-taxonomy-config-v1"


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


def _reject_unknown(obj: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        raise ValidationError(f"{path}: unknown fields: {sorted(unknown)}")


@dataclass(frozen=True)
class TaxonomyConfig:
    source_path: Path
    name: str
    honest_histories: tuple[str, ...]
    attack_histories: tuple[str, ...]


def load_config(path: Path) -> TaxonomyConfig:
    source_path = path.resolve()
    raw = _object(load_json(source_path), "$")
    allowed = {
        "schema_version",
        "name",
        "honest_histories",
        "attack_histories",
    }
    _reject_unknown(raw, allowed, "$")
    if raw.get("schema_version") != CONFIG_SCHEMA:
        raise ValidationError(
            f"$.schema_version: expected {CONFIG_SCHEMA!r}, "
            f"got {raw.get('schema_version')!r}"
        )
    honest = tuple(
        _string(value, "$.honest_histories[]")
        for value in _array(raw.get("honest_histories"), "$.honest_histories")
    )
    attacks = tuple(
        _string(value, "$.attack_histories[]")
        for value in _array(raw.get("attack_histories"), "$.attack_histories")
    )
    if not honest:
        raise ValidationError("$.honest_histories: expected at least one history")
    if not attacks:
        raise ValidationError("$.attack_histories: expected at least one history")
    if len(set(honest)) != len(honest):
        raise ValidationError("$.honest_histories: duplicates are not allowed")
    if len(set(attacks)) != len(attacks):
        raise ValidationError("$.attack_histories: duplicates are not allowed")
    overlap = set(honest).intersection(attacks)
    if overlap:
        raise ValidationError(
            f"taxonomy honest/attack catalogs overlap: {sorted(overlap)}"
        )
    return TaxonomyConfig(
        source_path=source_path,
        name=_string(raw.get("name"), "$.name"),
        honest_histories=honest,
        attack_histories=attacks,
    )
