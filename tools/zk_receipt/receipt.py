from __future__ import annotations

import base64
import hashlib
import hmac
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes
from tools.selective_receipt.merkle import build_tree, proof as merkle_proof, verify as verify_merkle
from tools.selective_receipt.policy import Policy

from .errors import ValidationError
from .group import GroupParameters
from .proof import commitment, prove_zero, verify_zero

SCHEMA = "lfv-experimental-zk-execution-receipt-v1"


def _scalar(seed: bytes, label: bytes, q: int) -> int:
    value = int.from_bytes(hmac.new(seed, label, hashlib.sha256).digest(), "big") % q
    return value or 1


def _leaf(action: str, committed: int) -> bytes:
    return hashlib.sha256(b"\x00" + canonical_bytes({
        "action": action,
        "commitment": format(committed, "x"),
    })).digest()


def _public_key_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _signed_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "lfv-experimental-zk-execution-head-v1",
        "policy_id": receipt["policy_id"],
        "policy_digest": receipt["policy_digest"],
        "universe_digest": receipt["universe_digest"],
        "parameter_digest": receipt["parameter_digest"],
        "runner_id": receipt["runner_id"],
        "trust_domain": receipt["trust_domain"],
        "root_sha256": receipt["root_sha256"],
        "tree_size": receipt["tree_size"],
        "total_events": receipt["total_events"],
        "finished_at": receipt["finished_at"],
    }


def _sign(payload: dict[str, Any], private_key: Path, openssl: str) -> str:
    with tempfile.TemporaryDirectory(prefix="lfv-zk-sign-") as temporary:
        message = Path(temporary) / "payload.json"
        signature = Path(temporary) / "signature.bin"
        message.write_bytes(canonical_bytes(payload))
        signature_result = subprocess.run(
            [openssl, "dgst", "-sha256", "-sign", str(private_key), "-out", str(signature), str(message)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=30,
        )
        if signature_result.returncode != 0:
            raise ValidationError(signature_result.stderr.decode("utf-8", errors="replace"))
        return base64.b64encode(signature.read_bytes()).decode("ascii")


def _verify_signature(payload: dict[str, Any], signature_base64: str, public_key: Path, openssl: str) -> None:
    try:
        signature_bytes = base64.b64decode(signature_base64, validate=True)
    except (TypeError, ValueError) as exc:
        raise ValidationError("receipt signature is not valid base64") from exc
    with tempfile.TemporaryDirectory(prefix="lfv-zk-verify-") as temporary:
        message = Path(temporary) / "payload.json"
        signature = Path(temporary) / "signature.bin"
        message.write_bytes(canonical_bytes(payload))
        signature.write_bytes(signature_bytes)
        result = subprocess.run(
            [openssl, "dgst", "-sha256", "-verify", str(public_key), "-signature", str(signature), str(message)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=30,
        )
        if result.returncode != 0:
            raise ValidationError("receipt signature verification failed")


def issue_receipt(
    policy: Policy,
    parameters: GroupParameters,
    events: list[str],
    *,
    blinding_seed: bytes,
    nonce_seed: bytes | None,
    private_key: Path,
    public_key: Path,
    finished_at: int,
    openssl: str = "openssl",
) -> dict[str, Any]:
    if len(blinding_seed) < 16:
        raise ValidationError("blinding seed must contain at least 128 bits")
    unknown = set(events) - set(policy.action_universe)
    if unknown:
        raise ValidationError(f"execution log contains unknown actions: {sorted(unknown)}")
    counts = {action: 0 for action in policy.action_universe}
    for event in events:
        counts[event] += 1
    blindings = {
        action: _scalar(blinding_seed, b"LFV\x00BLIND\x00" + action.encode(), parameters.q)
        for action in policy.action_universe
    }
    commitments = {
        action: commitment(parameters, counts[action], blindings[action])
        for action in policy.action_universe
    }
    levels = build_tree([_leaf(action, commitments[action]) for action in policy.action_universe])
    root = levels[-1][0].hex()
    disclosures = []
    for action in policy.forbidden_actions:
        index = policy.action_universe.index(action)
        context = {
            "policy_digest": policy.policy_digest,
            "parameter_digest": parameters.digest,
            "root_sha256": root,
            "action": action,
            "commitment": format(commitments[action], "x"),
        }
        action_seed = None if nonce_seed is None else hmac.new(
            nonce_seed, action.encode(), hashlib.sha256
        ).digest()
        disclosures.append({
            "action": action,
            "commitment": format(commitments[action], "x"),
            "leaf_index": index,
            "audit_path": merkle_proof(levels, index),
            "zero_proof": prove_zero(
                parameters, commitments[action], blindings[action], context,
                nonce_seed=action_seed,
            ),
        })
    receipt = {
        "schema_version": SCHEMA,
        "policy_id": policy.policy_id,
        "policy_digest": policy.policy_digest,
        "universe_digest": policy.universe_digest,
        "parameter_digest": parameters.digest,
        "runner_id": policy.runner_id,
        "trust_domain": policy.trust_domain,
        "root_sha256": root,
        "tree_size": len(policy.action_universe),
        "total_events": len(events),
        "finished_at": finished_at,
        "public_key_sha256": _public_key_hash(public_key),
        "proofs": disclosures,
        "signature_base64": "",
    }
    receipt["signature_base64"] = _sign(_signed_payload(receipt), private_key, openssl)
    return receipt


def verify_receipt(
    policy: Policy,
    parameters: GroupParameters,
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
        "parameter_digest", "runner_id", "trust_domain", "root_sha256",
        "tree_size", "total_events", "finished_at", "public_key_sha256",
        "proofs", "signature_base64",
    }
    if set(receipt) != required or receipt["schema_version"] != SCHEMA:
        raise ValidationError("receipt fields or schema are invalid")
    if receipt["policy_id"] != policy.policy_id or receipt["policy_digest"] != policy.policy_digest:
        raise ValidationError("receipt binds a different policy")
    if receipt["universe_digest"] != policy.universe_digest:
        raise ValidationError("receipt binds a different action universe")
    if receipt["parameter_digest"] != parameters.digest:
        raise ValidationError("receipt binds different ZK parameters")
    if receipt["runner_id"] != policy.runner_id or receipt["trust_domain"] != policy.trust_domain:
        raise ValidationError("receipt runner identity does not match policy")
    if receipt["tree_size"] != len(policy.action_universe):
        raise ValidationError("receipt tree size does not match universe")
    if receipt["finished_at"] > cutoff:
        raise ValidationError("receipt is later than cutoff")
    if receipt["public_key_sha256"] != _public_key_hash(public_key):
        raise ValidationError("verifier-selected public key does not match receipt")
    proofs = receipt["proofs"]
    if not isinstance(proofs, list):
        raise ValidationError("receipt proofs must be an array")
    actions = [item.get("action") for item in proofs if isinstance(item, dict)]
    if actions != list(policy.forbidden_actions):
        raise ValidationError("receipt must prove every forbidden class and no others")
    for item in proofs:
        if set(item) != {"action", "commitment", "leaf_index", "audit_path", "zero_proof"}:
            raise ValidationError("private proof disclosure has invalid fields")
        action = item["action"]
        try:
            committed = int(item["commitment"], 16)
        except (TypeError, ValueError) as exc:
            raise ValidationError("commitment is not hexadecimal") from exc
        index = policy.action_universe.index(action)
        if item["leaf_index"] != index:
            raise ValidationError("commitment index does not match action universe")
        verify_merkle(_leaf(action, committed), item["audit_path"], receipt["root_sha256"])
        context = {
            "policy_digest": policy.policy_digest,
            "parameter_digest": parameters.digest,
            "root_sha256": receipt["root_sha256"],
            "action": action,
            "commitment": item["commitment"],
        }
        verify_zero(parameters, committed, item["zero_proof"], context)
    _verify_signature(_signed_payload(receipt), receipt["signature_base64"], public_key, openssl)
    return {
        "schema_version": "lfv-verified-private-execution-v1",
        "policy_id": policy.policy_id,
        "runner_id": policy.runner_id,
        "trust_domain": policy.trust_domain,
        "root_sha256": receipt["root_sha256"],
        "finished_at": receipt["finished_at"],
        "forbidden_absent": list(policy.forbidden_actions),
        "backend": "experimental-pedersen-schnorr-zero-opening-v1",
    }
