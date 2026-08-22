from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json

from .errors import ValidationError
from .signature import public_key_sha256, sign, verify

METADATA_SCHEMA = "lfv-pit-vendor-package-metadata-v1"
MANIFEST_SCHEMA = "lfv-signed-pit-vendor-manifest-v1"
HEADERS = {
    "vintages": ["id", "revision", "first_published_at", "supersedes"],
    "listings": ["asset", "listed_at", "delisted_at"],
    "prices": ["asset", "time", "available_at", "value", "vintage"],
    "corporate_actions": ["id", "asset", "announced_at", "effective_at"],
}


def _safe_relative(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError("vendor file path must be non-empty")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValidationError("vendor file path must stay inside package root")
    return value


def _file_info(root: Path, relative: str, kind: str) -> dict[str, Any]:
    if kind not in HEADERS:
        raise ValidationError(f"unsupported vendor file kind: {kind}")
    path = root / relative
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise ValidationError(f"missing vendor file: {relative}") from exc
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValidationError(f"vendor file is empty: {relative}") from exc
        if header != HEADERS[kind]:
            raise ValidationError(
                f"{relative}: expected header {HEADERS[kind]}, got {header}"
            )
        rows = sum(1 for _ in reader)
    if rows <= 0:
        raise ValidationError(f"vendor file has no data rows: {relative}")
    return {
        "path": relative,
        "kind": kind,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "rows": rows,
    }


def manifest_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "signature_base64"}


def build_manifest(metadata_path: Path, package_root: Path, public_key: Path,
                   private_key: Path, *, signed_at: int,
                   openssl: str = "openssl") -> dict[str, Any]:
    metadata = load_json(metadata_path)
    if not isinstance(metadata, dict) or metadata.get("schema_version") != METADATA_SCHEMA:
        raise ValidationError("unsupported vendor metadata schema")
    for field in ("package_id", "vendor_id", "license_id", "redistribution_policy"):
        if not isinstance(metadata.get(field), str) or not metadata[field]:
            raise ValidationError(f"metadata {field} must be non-empty")
    if metadata["redistribution_policy"] not in {"allowed", "restricted", "metadata-only"}:
        raise ValidationError("unsupported redistribution policy")
    files_raw = metadata.get("files")
    if not isinstance(files_raw, list) or not files_raw:
        raise ValidationError("metadata files must be a non-empty array")
    files = []
    seen_paths: set[str] = set()
    seen_kinds: set[str] = set()
    for item in files_raw:
        if not isinstance(item, dict) or set(item) != {"path", "kind"}:
            raise ValidationError("metadata file entries require path and kind")
        relative = _safe_relative(item["path"])
        kind = item["kind"]
        if relative in seen_paths or kind in seen_kinds:
            raise ValidationError("vendor paths and file kinds must be unique")
        seen_paths.add(relative)
        seen_kinds.add(kind)
        files.append(_file_info(package_root, relative, kind))
    missing = set(HEADERS) - seen_kinds
    if missing:
        raise ValidationError(f"vendor package misses required kinds: {sorted(missing)}")
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "package_id": metadata["package_id"],
        "vendor_id": metadata["vendor_id"],
        "license_id": metadata["license_id"],
        "redistribution_policy": metadata["redistribution_policy"],
        "signed_at": signed_at,
        "public_key_sha256": public_key_sha256(public_key),
        "files": files,
        "signature_base64": "",
    }
    manifest["signature_base64"] = sign(
        manifest_payload(manifest), private_key, openssl=openssl
    )
    return manifest


def verify_manifest(manifest: Any, package_root: Path, public_key: Path,
                    *, openssl: str = "openssl") -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ValidationError("vendor manifest must be an object")
    required = {
        "schema_version", "package_id", "vendor_id", "license_id",
        "redistribution_policy", "signed_at", "public_key_sha256", "files",
        "signature_base64",
    }
    if set(manifest) != required or manifest["schema_version"] != MANIFEST_SCHEMA:
        raise ValidationError("vendor manifest fields or schema are invalid")
    for field in ("package_id", "vendor_id", "license_id", "redistribution_policy"):
        if not isinstance(manifest[field], str) or not manifest[field]:
            raise ValidationError(f"manifest {field} must be non-empty")
    if manifest["redistribution_policy"] not in {"allowed", "restricted", "metadata-only"}:
        raise ValidationError("unsupported redistribution policy")
    if manifest["public_key_sha256"] != public_key_sha256(public_key):
        raise ValidationError("verifier-selected public key does not match manifest")
    verify(manifest_payload(manifest), manifest["signature_base64"], public_key,
           openssl=openssl)
    files = manifest["files"]
    if not isinstance(files, list) or not files:
        raise ValidationError("manifest files must be non-empty")
    verified_files = []
    seen_kinds: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "kind", "sha256", "rows"}:
            raise ValidationError("manifest file entry has invalid shape")
        relative = _safe_relative(item["path"])
        actual = _file_info(package_root, relative, item["kind"])
        if item != actual:
            raise ValidationError(f"vendor file digest, row count, or schema mismatch: {relative}")
        if item["kind"] in seen_kinds:
            raise ValidationError("manifest repeats one file kind")
        seen_kinds.add(item["kind"])
        verified_files.append(actual)
    if set(HEADERS) != seen_kinds:
        raise ValidationError("manifest does not cover all required file kinds")
    return {
        "package_id": manifest["package_id"],
        "vendor_id": manifest["vendor_id"],
        "license_id": manifest["license_id"],
        "redistribution_policy": manifest["redistribution_policy"],
        "signed_at": manifest["signed_at"],
        "public_key_sha256": manifest["public_key_sha256"],
        "files": verified_files,
    }
