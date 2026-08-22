from __future__ import annotations

import hashlib
from typing import Iterable

from .errors import ValidationError


def _digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def leaf_hash(target_digest: str) -> bytes:
    try:
        raw = bytes.fromhex(target_digest)
    except ValueError as exc:
        raise ValidationError("target digest must be lowercase hexadecimal") from exc
    if len(raw) != 32 or target_digest != target_digest.lower():
        raise ValidationError("target digest must be a 32-byte lowercase SHA-256 value")
    return _digest(b"\x00" + raw)


def node_hash(left: bytes, right: bytes) -> bytes:
    if len(left) != 32 or len(right) != 32:
        raise ValidationError("Merkle node inputs must be 32 bytes")
    return _digest(b"\x01" + left + right)


def build_tree(target_digests: Iterable[str]) -> list[list[bytes]]:
    leaves = [leaf_hash(value) for value in target_digests]
    if not leaves or len(leaves) & (len(leaves) - 1):
        raise ValidationError("test/reference Merkle trees require a power-of-two leaf count")
    levels = [leaves]
    while len(levels[-1]) > 1:
        current = levels[-1]
        levels.append([
            node_hash(current[index], current[index + 1])
            for index in range(0, len(current), 2)
        ])
    return levels


def inclusion_proof(levels: list[list[bytes]], leaf_index: int) -> list[dict[str, str]]:
    if not levels or leaf_index < 0 or leaf_index >= len(levels[0]):
        raise ValidationError("leaf index outside Merkle tree")
    proof: list[dict[str, str]] = []
    index = leaf_index
    for level in levels[:-1]:
        sibling_index = index ^ 1
        proof.append({
            "side": "left" if sibling_index < index else "right",
            "digest": level[sibling_index].hex(),
        })
        index //= 2
    return proof


def verify_inclusion(
    target_digest: str,
    leaf_index: int,
    tree_size: int,
    audit_path: list[dict[str, str]],
    expected_root: str,
) -> None:
    if tree_size <= 0 or tree_size & (tree_size - 1):
        raise ValidationError("tree size must be a positive power of two")
    if leaf_index < 0 or leaf_index >= tree_size:
        raise ValidationError("leaf index outside tree size")
    expected_depth = tree_size.bit_length() - 1
    if len(audit_path) != expected_depth:
        raise ValidationError("audit path length does not match tree size")
    current = leaf_hash(target_digest)
    for index, item in enumerate(audit_path):
        if not isinstance(item, dict) or set(item) != {"side", "digest"}:
            raise ValidationError(f"audit path item {index} has invalid shape")
        side = item["side"]
        try:
            sibling = bytes.fromhex(item["digest"])
        except (TypeError, ValueError) as exc:
            raise ValidationError("audit-path digest is not hexadecimal") from exc
        if len(sibling) != 32 or item["digest"] != item["digest"].lower():
            raise ValidationError("audit-path digest must be lowercase SHA-256")
        if side == "left":
            current = node_hash(sibling, current)
        elif side == "right":
            current = node_hash(current, sibling)
        else:
            raise ValidationError("audit-path side must be left or right")
    if current.hex() != expected_root:
        raise ValidationError("Merkle inclusion proof does not match signed root")
