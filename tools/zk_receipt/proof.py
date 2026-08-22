from __future__ import annotations

import hashlib
import secrets
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .group import GroupParameters

DOMAIN = "LFV-ZERO-COUNT-SCHNORR-V1"


def commitment(parameters: GroupParameters, count: int, blinding: int) -> int:
    if count < 0 or count >= parameters.q:
        raise ValidationError("count is outside the scalar field")
    if blinding < 0 or blinding >= parameters.q:
        raise ValidationError("blinding is outside the scalar field")
    return (
        pow(parameters.g, count, parameters.p)
        * pow(parameters.h, blinding, parameters.p)
    ) % parameters.p


def _challenge(
    parameters: GroupParameters,
    committed: int,
    announcement: int,
    context: dict[str, Any],
) -> int:
    payload = {
        "domain": DOMAIN,
        "parameters": parameters.digest,
        "commitment": format(committed, "x"),
        "announcement": format(announcement, "x"),
        "context": context,
    }
    return int.from_bytes(hashlib.sha256(canonical_bytes(payload)).digest(), "big") % parameters.q


def prove_zero(
    parameters: GroupParameters,
    committed: int,
    blinding: int,
    context: dict[str, Any],
    *,
    nonce_seed: bytes | None = None,
) -> dict[str, str]:
    if committed != commitment(parameters, 0, blinding):
        raise ValidationError("commitment does not open to zero")
    seed = nonce_seed if nonce_seed is not None else secrets.token_bytes(32)
    if len(seed) < 16:
        raise ValidationError("proof nonce seed must contain at least 128 bits")
    nonce = int.from_bytes(hashlib.sha256(
        b"LFV\x00ZK-NONCE\x00" + seed + canonical_bytes(context)
        + blinding.to_bytes((parameters.q.bit_length() + 7) // 8, "big")
    ).digest(), "big") % parameters.q
    if nonce == 0:
        nonce = 1
    announcement = pow(parameters.h, nonce, parameters.p)
    challenge = _challenge(parameters, committed, announcement, context)
    response = (nonce + challenge * blinding) % parameters.q
    return {"announcement": format(announcement, "x"), "response": format(response, "x")}


def verify_zero(
    parameters: GroupParameters,
    committed: int,
    proof: Any,
    context: dict[str, Any],
) -> None:
    if not isinstance(proof, dict) or set(proof) != {"announcement", "response"}:
        raise ValidationError("zero-count proof has invalid shape")
    try:
        announcement = int(proof["announcement"], 16)
        response = int(proof["response"], 16)
    except (TypeError, ValueError) as exc:
        raise ValidationError("zero-count proof contains invalid hexadecimal") from exc
    if not (1 < committed < parameters.p) or pow(committed, parameters.q, parameters.p) != 1:
        raise ValidationError("commitment is outside the q-order subgroup")
    if not (1 <= announcement < parameters.p) or pow(announcement, parameters.q, parameters.p) != 1:
        raise ValidationError("proof announcement is outside the subgroup")
    if not (0 <= response < parameters.q):
        raise ValidationError("proof response is outside the scalar field")
    challenge = _challenge(parameters, committed, announcement, context)
    left = pow(parameters.h, response, parameters.p)
    right = (announcement * pow(committed, challenge, parameters.p)) % parameters.p
    if left != right:
        raise ValidationError("zero-count Schnorr proof verification failed")
