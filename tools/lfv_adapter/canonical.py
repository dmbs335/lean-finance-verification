from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from .errors import ValidationError

CANONICAL_FORMAT = "lfv-canonical-json-v1"
SUPPORTED_ARTIFACT_KINDS = {
    "sourceCode",
    "dataset",
    "parameterSet",
    "environment",
    "result",
    "feature",
    "searchLedger",
}
SUPPORTED_HASH_ALGORITHMS = {"sha256", "sha512", "blake3"}


def _validate_json_value(value: Any, path: str = "$") -> None:
    """Validate the deliberately small JSON domain used by canonical v1.

    Canonical v1 accepts null, booleans, integers, strings, arrays, and objects
    with string keys. Floating-point values are rejected so different language
    runtimes cannot silently disagree about number rendering.
    """

    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        raise ValidationError(f"{path}: floating-point JSON numbers are not allowed")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError(f"{path}: object keys must be strings")
            _validate_json_value(item, f"{path}.{key}")
        return
    raise ValidationError(f"{path}: unsupported canonical JSON value {type(value).__name__}")


def canonical_dumps(value: Any) -> str:
    _validate_json_value(value)
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
    _validate_json_value(value)
    return value


def write_canonical_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def write_pretty_json(path: Path, value: Any) -> None:
    _validate_json_value(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2)
        + "\n",
        encoding="utf-8",
    )


def _hash_object(algorithm: str):
    if algorithm == "sha256":
        return hashlib.sha256()
    if algorithm == "sha512":
        return hashlib.sha512()
    if algorithm == "blake3":
        module = importlib.util.find_spec("blake3")
        if module is None:
            raise ValidationError(
                "blake3 requested but the optional 'blake3' Python package is not installed"
            )
        blake3 = importlib.import_module("blake3")
        return blake3.blake3()
    raise ValidationError(f"unsupported hash algorithm: {algorithm}")


def hash_bytes(algorithm: str, payload: bytes) -> str:
    digest = _hash_object(algorithm)
    digest.update(payload)
    return digest.hexdigest()


def validate_digest(algorithm: str, digest: str, path: str = "digest") -> None:
    if algorithm not in SUPPORTED_HASH_ALGORITHMS:
        raise ValidationError(f"{path}: unsupported hash algorithm {algorithm!r}")
    if not isinstance(digest, str) or not digest:
        raise ValidationError(f"{path}: digest must be a non-empty string")
    expected_length = {"sha256": 64, "sha512": 128, "blake3": 64}[algorithm]
    if len(digest) != expected_length:
        raise ValidationError(
            f"{path}: {algorithm} digest must contain {expected_length} lowercase hex characters"
        )
    if digest.lower() != digest or any(char not in "0123456789abcdef" for char in digest):
        raise ValidationError(f"{path}: digest must be lowercase hexadecimal")


def validate_artifact_ref(ref: Any, path: str = "artifact") -> dict[str, str]:
    if not isinstance(ref, dict):
        raise ValidationError(f"{path}: artifact reference must be an object")
    expected = {"algorithm", "schema_id", "digest"}
    unknown = set(ref) - expected
    missing = expected - set(ref)
    if unknown:
        raise ValidationError(f"{path}: unknown fields: {sorted(unknown)}")
    if missing:
        raise ValidationError(f"{path}: missing fields: {sorted(missing)}")
    algorithm = ref["algorithm"]
    schema_id = ref["schema_id"]
    digest = ref["digest"]
    if not isinstance(algorithm, str) or algorithm not in SUPPORTED_HASH_ALGORITHMS:
        raise ValidationError(f"{path}.algorithm: unsupported value {algorithm!r}")
    if not isinstance(schema_id, str) or not schema_id:
        raise ValidationError(f"{path}.schema_id: expected a non-empty string")
    validate_digest(algorithm, digest, f"{path}.digest")
    return {"algorithm": algorithm, "schema_id": schema_id, "digest": digest}


def domain_separated_bytes(domain: str, schema_id: str, payload: Any) -> bytes:
    if not domain:
        raise ValidationError("hash domain must be non-empty")
    if not schema_id:
        raise ValidationError("schema_id must be non-empty")
    prefix = (
        b"LFV\x00ARTIFACT\x00V1\x00"
        + domain.encode("utf-8")
        + b"\x00"
        + schema_id.encode("utf-8")
        + b"\x00"
    )
    return prefix + canonical_bytes(payload)


def make_artifact_ref(
    *, kind: str, schema_id: str, payload: Any, algorithm: str
) -> tuple[dict[str, str], int]:
    if kind not in SUPPORTED_ARTIFACT_KINDS:
        raise ValidationError(f"unsupported artifact kind: {kind}")
    serialized = canonical_bytes(payload)
    digest = hash_bytes(
        algorithm,
        domain_separated_bytes(kind, schema_id, payload),
    )
    return (
        {"algorithm": algorithm, "schema_id": schema_id, "digest": digest},
        len(serialized),
    )


def make_document_digest(
    *, domain: str, schema_id: str, payload: Any, algorithm: str
) -> dict[str, str]:
    return {
        "algorithm": algorithm,
        "schema_id": schema_id,
        "digest": hash_bytes(
            algorithm,
            domain_separated_bytes(domain, schema_id, payload),
        ),
    }
