from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .errors import ValidationError

CANONICAL_FORMAT = "lfv-canonical-json-v1"


def validate_json_value(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        raise ValidationError(f"{path}: floating-point JSON numbers are not allowed")
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError(f"{path}: object keys must be strings")
            validate_json_value(item, f"{path}.{key}")
        return
    raise ValidationError(f"{path}: unsupported JSON value {type(value).__name__}")


def canonical_dumps(value: Any) -> str:
    validate_json_value(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_bytes(value: Any) -> bytes:
    return canonical_dumps(value).encode("utf-8")


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError as exc:
        raise ValidationError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc
    validate_json_value(value)
    return value


def write_canonical_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def write_pretty_json(path: Path, value: Any) -> None:
    validate_json_value(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2)
        + "\n",
        encoding="utf-8",
    )


def document_digest(domain: str, schema_id: str, payload: Any) -> dict[str, str]:
    if not domain or not schema_id:
        raise ValidationError("digest domain and schema id must be non-empty")
    prefix = (
        b"LFV\x00WORKFLOW-CEGIS\x00V1\x00"
        + domain.encode("utf-8")
        + b"\x00"
        + schema_id.encode("utf-8")
        + b"\x00"
    )
    digest = hashlib.sha256(prefix + canonical_bytes(payload)).hexdigest()
    return {"algorithm": "sha256", "schema_id": schema_id, "digest": digest}
