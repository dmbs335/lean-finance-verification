from __future__ import annotations

import hashlib

from .errors import ValidationError


def node_hash(left: bytes, right: bytes) -> bytes:
    if len(left) != 32 or len(right) != 32:
        raise ValidationError("Merkle nodes must be SHA-256 digests")
    return hashlib.sha256(b"\x01" + left + right).digest()


def build_tree(leaves: list[bytes]) -> list[list[bytes]]:
    if not leaves or len(leaves) & (len(leaves) - 1):
        raise ValidationError("Merkle leaf count must be a power of two")
    if any(len(leaf) != 32 for leaf in leaves):
        raise ValidationError("Merkle leaves must be SHA-256 digests")
    levels = [leaves]
    while len(levels[-1]) > 1:
        current = levels[-1]
        levels.append([
            node_hash(current[index], current[index + 1])
            for index in range(0, len(current), 2)
        ])
    return levels


def proof(levels: list[list[bytes]], index: int) -> list[dict[str, str]]:
    if not levels or index < 0 or index >= len(levels[0]):
        raise ValidationError("Merkle proof index outside tree")
    result: list[dict[str, str]] = []
    current = index
    for level in levels[:-1]:
        sibling = current ^ 1
        result.append({
            "side": "left" if sibling < current else "right",
            "digest": level[sibling].hex(),
        })
        current //= 2
    return result


def verify(leaf: bytes, path: list[dict[str, str]], expected_root: str) -> None:
    current = leaf
    for item in path:
        if not isinstance(item, dict) or set(item) != {"side", "digest"}:
            raise ValidationError("invalid Merkle path item")
        try:
            sibling = bytes.fromhex(item["digest"])
        except (TypeError, ValueError) as exc:
            raise ValidationError("invalid Merkle path digest") from exc
        if len(sibling) != 32:
            raise ValidationError("invalid Merkle path digest length")
        if item["side"] == "left":
            current = node_hash(sibling, current)
        elif item["side"] == "right":
            current = node_hash(current, sibling)
        else:
            raise ValidationError("invalid Merkle path side")
    if current.hex() != expected_root:
        raise ValidationError("disclosure does not match committed histogram root")
