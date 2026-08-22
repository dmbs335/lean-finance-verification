from __future__ import annotations

import base64
import hashlib
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

from .errors import ValidationError
from .merkle import verify_inclusion

RECEIPT_SCHEMA = "lfv-signed-transparency-receipt-v1"


@dataclass(frozen=True)
class VerifiedReceipt:
    provider_id: str
    trust_domain: str
    target_digest: str
    anchored_at: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "trust_domain": self.trust_domain,
            "target_digest": self.target_digest,
            "anchored_at": self.anchored_at,
        }


def tree_head_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "lfv-signed-tree-head-v1",
        "provider_id": receipt["provider_id"],
        "tree_size": receipt["tree_size"],
        "root_sha256": receipt["root_sha256"],
        "anchored_at": receipt["anchored_at"],
    }


def public_key_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sign_tree_head(
    payload: dict[str, Any],
    private_key: Path,
    *,
    openssl_binary: str = "openssl",
) -> str:
    with tempfile.TemporaryDirectory(prefix="lfv-log-sign-") as temporary:
        message = Path(temporary) / "head.json"
        signature = Path(temporary) / "head.sig"
        message.write_bytes(canonical_bytes(payload))
        completed = subprocess.run(
            [openssl_binary, "dgst", "-sha256", "-sign", str(private_key),
             "-out", str(signature), str(message)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        if completed.returncode != 0:
            raise ValidationError(
                completed.stderr.decode("utf-8", errors="replace")
            )
        return base64.b64encode(signature.read_bytes()).decode("ascii")


def _verify_signature(
    payload: dict[str, Any],
    signature_base64: str,
    public_key: Path,
    openssl_binary: str,
) -> None:
    try:
        signature_bytes = base64.b64decode(signature_base64, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValidationError("tree-head signature is not valid base64") from exc
    with tempfile.TemporaryDirectory(prefix="lfv-log-verify-") as temporary:
        message = Path(temporary) / "head.json"
        signature = Path(temporary) / "head.sig"
        message.write_bytes(canonical_bytes(payload))
        signature.write_bytes(signature_bytes)
        completed = subprocess.run(
            [openssl_binary, "dgst", "-sha256", "-verify", str(public_key),
             "-signature", str(signature), str(message)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        if completed.returncode != 0:
            raise ValidationError("signed tree head signature verification failed")


def verify_receipt(
    receipt: Any,
    public_key: Path,
    cutoff: int,
    *,
    openssl_binary: str = "openssl",
) -> VerifiedReceipt:
    if not isinstance(receipt, dict):
        raise ValidationError("transparency receipt must be an object")
    required = {
        "schema_version", "provider_id", "trust_domain", "target_digest",
        "leaf_index", "tree_size", "root_sha256", "audit_path",
        "anchored_at", "public_key_sha256", "signature_base64",
    }
    if set(receipt) != required:
        raise ValidationError("transparency receipt fields do not match schema")
    if receipt["schema_version"] != RECEIPT_SCHEMA:
        raise ValidationError("unsupported transparency receipt schema")
    for field in ("provider_id", "trust_domain", "target_digest", "root_sha256"):
        if not isinstance(receipt[field], str) or not receipt[field]:
            raise ValidationError(f"receipt {field} must be a non-empty string")
    for field in ("leaf_index", "tree_size", "anchored_at"):
        if isinstance(receipt[field], bool) or not isinstance(receipt[field], int):
            raise ValidationError(f"receipt {field} must be an integer")
    if receipt["anchored_at"] > cutoff:
        raise ValidationError("tree head is later than the verification cutoff")
    if receipt["public_key_sha256"] != public_key_sha256(public_key):
        raise ValidationError("verifier-selected public key does not match receipt binding")
    verify_inclusion(
        receipt["target_digest"], receipt["leaf_index"], receipt["tree_size"],
        receipt["audit_path"], receipt["root_sha256"],
    )
    _verify_signature(
        tree_head_payload(receipt), receipt["signature_base64"],
        public_key, openssl_binary,
    )
    return VerifiedReceipt(
        provider_id=receipt["provider_id"],
        trust_domain=receipt["trust_domain"],
        target_digest=receipt["target_digest"],
        anchored_at=receipt["anchored_at"],
    )


def load_receipt(path: Path) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValidationError(f"receipt {path} must be an object")
    return value
