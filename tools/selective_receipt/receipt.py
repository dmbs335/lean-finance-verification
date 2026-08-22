from __future__ import annotations

import base64
import hashlib
import hmac
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .merkle import build_tree, proof, verify as verify_merkle
from .policy import Policy

RECEIPT_SCHEMA = "lfv-selective-execution-receipt-v1"


def _salt(seed: bytes, action: str) -> str:
    return hmac.new(seed, b"LFV\x00ACTION-COUNT\x00" + action.encode(),
                    hashlib.sha256).hexdigest()


def _leaf(action: str, count: int, salt: str) -> bytes:
    payload = {"action": action, "count": count, "salt": salt}
    return hashlib.sha256(b"\x00" + canonical_bytes(payload)).digest()


def _public_key_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "lfv-selective-execution-head-v1",
        "policy_id": receipt["policy_id"],
        "policy_digest": receipt["policy_digest"],
        "universe_digest": receipt["universe_digest"],
        "runner_id": receipt["runner_id"],
        "trust_domain": receipt["trust_domain"],
        "root_sha256": receipt["root_sha256"],
        "tree_size": receipt["tree_size"],
        "total_events": receipt["total_events"],
        "finished_at": receipt["finished_at"],
    }


def _sign(payload: dict[str, Any], private_key: Path, openssl: str) -> str:
    with tempfile.TemporaryDirectory(prefix="lfv-selective-sign-") as temporary:
        message = Path(temporary) / "payload.json"
        signature = Path(temporary) / "signature.bin"
        message.write_bytes(canonical_bytes(payload))
        completed = subprocess.run(
            [openssl, "dgst", "-sha256", "-sign", str(private_key),
             "-out", str(signature), str(message)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False, timeout=30,
        )
        if completed.returncode != 0:
            raise ValidationError(
                completed.stderr.decode("utf-8", errors="replace")
            )
        return base64.b64encode(signature.read_bytes()).decode("ascii")


def _verify_signature(
    payload: dict[str, Any], signature_base64: str,
    public_key: Path, openssl: str,
) -> None:
    try:
        signature_bytes = base64.b64decode(signature_base64, validate=True)
    except (TypeError, ValueError) as exc:
        raise ValidationError("receipt signature is not valid base64") from exc
    with tempfile.TemporaryDirectory(prefix="lfv-selective-verify-") as temporary:
        message = Path(temporary) / "payload.json"
        signature = Path(temporary) / "signature.bin"
        message.write_bytes(canonical_bytes(payload))
        signature.write_bytes(signature_bytes)
        completed = subprocess.run(
            [openssl, "dgst", "-sha256", "-verify", str(public_key),
             "-signature", str(signature), str(message)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False, timeout=30,
        )
        if completed.returncode != 0:
            raise ValidationError("receipt signature verification failed")


def issue_receipt(
    policy: Policy,
    events: list[str],
    *,
    salt_seed_hex: str,
    private_key: Path,
    public_key: Path,
    finished_at: int,
    openssl: str = "openssl",
) -> dict[str, Any]:
    try:
        seed = bytes.fromhex(salt_seed_hex)
    except ValueError as exc:
        raise ValidationError("salt seed must be hexadecimal") from exc
    if len(seed) < 16:
        raise ValidationError("salt seed must contain at least 128 bits")
    unknown = set(events) - set(policy.action_universe)
    if unknown:
        raise ValidationError(f"execution log contains unknown actions: {sorted(unknown)}")
    counts = {action: 0 for action in policy.action_universe}
    for event in events:
        counts[event] += 1
    salts = {action: _salt(seed, action) for action in policy.action_universe}
    leaves = [
        _leaf(action, counts[action], salts[action])
        for action in policy.action_universe
    ]
    levels = build_tree(leaves)
    disclosures = []
    for action in policy.forbidden_actions:
        index = policy.action_universe.index(action)
        disclosures.append({
            "action": action,
            "count": counts[action],
            "salt": salts[action],
            "leaf_index": index,
            "audit_path": proof(levels, index),
        })
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "policy_id": policy.policy_id,
        "policy_digest": policy.policy_digest,
        "universe_digest": policy.universe_digest,
        "runner_id": policy.runner_id,
        "trust_domain": policy.trust_domain,
        "root_sha256": levels[-1][0].hex(),
        "tree_size": len(policy.action_universe),
        "total_events": len(events),
        "finished_at": finished_at,
        "public_key_sha256": _public_key_hash(public_key),
        "disclosures": disclosures,
        "signature_base64": "",
    }
    receipt["signature_base64"] = _sign(
        _payload(receipt), private_key, openssl
    )
    return receipt


def verify_receipt(
    policy: Policy,
    receipt: Any,
    public_key: Path,
    *,
    cutoff: int,
    openssl: str = "openssl",
) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ValidationError("receipt must be an object")
    required = {
        "schema_version", "policy_id", "policy_digest", "universe_digest",
        "runner_id", "trust_domain", "root_sha256", "tree_size",
        "total_events", "finished_at", "public_key_sha256", "disclosures",
        "signature_base64",
    }
    if set(receipt) != required or receipt["schema_version"] != RECEIPT_SCHEMA:
        raise ValidationError("receipt fields or schema are invalid")
    if receipt["policy_id"] != policy.policy_id or receipt["policy_digest"] != policy.policy_digest:
        raise ValidationError("receipt binds a different execution policy")
    if receipt["universe_digest"] != policy.universe_digest:
        raise ValidationError("receipt binds a different action universe")
    if receipt["runner_id"] != policy.runner_id or receipt["trust_domain"] != policy.trust_domain:
        raise ValidationError("receipt runner identity does not match policy")
    if receipt["tree_size"] != len(policy.action_universe):
        raise ValidationError("receipt tree size does not match action universe")
    if receipt["finished_at"] > cutoff:
        raise ValidationError("execution receipt is later than cutoff")
    if receipt["public_key_sha256"] != _public_key_hash(public_key):
        raise ValidationError("verifier-selected public key does not match receipt")
    disclosures = receipt["disclosures"]
    if not isinstance(disclosures, list):
        raise ValidationError("receipt disclosures must be an array")
    disclosed_actions = [item.get("action") for item in disclosures if isinstance(item, dict)]
    if disclosed_actions != list(policy.forbidden_actions):
        raise ValidationError("receipt must disclose every forbidden class and no others")
    for disclosure in disclosures:
        action = disclosure["action"]
        if disclosure["count"] != 0:
            raise ValidationError(f"forbidden action occurred: {action}")
        expected_index = policy.action_universe.index(action)
        if disclosure["leaf_index"] != expected_index:
            raise ValidationError("disclosure leaf index does not match action universe")
        leaf = _leaf(action, disclosure["count"], disclosure["salt"])
        verify_merkle(leaf, disclosure["audit_path"], receipt["root_sha256"])
    _verify_signature(_payload(receipt), receipt["signature_base64"], public_key, openssl)
    return {
        "schema_version": "lfv-verified-selective-execution-v1",
        "policy_id": policy.policy_id,
        "runner_id": policy.runner_id,
        "trust_domain": policy.trust_domain,
        "root_sha256": receipt["root_sha256"],
        "total_events": receipt["total_events"],
        "finished_at": receipt["finished_at"],
        "forbidden_absent": list(policy.forbidden_actions),
        "disclosed_classes": disclosed_actions,
    }
