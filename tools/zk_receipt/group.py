from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

from .errors import ValidationError

SCHEMA = "lfv-experimental-pedersen-group-v1"


def _probable_prime(value: int, rounds: int = 32) -> bool:
    if value < 2:
        return False
    for prime in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43):
        if value == prime:
            return True
        if value % prime == 0:
            return False
    odd = value - 1
    powers = 0
    while odd % 2 == 0:
        powers += 1
        odd //= 2
    for index in range(rounds):
        seed = hashlib.sha256(f"{value}:{index}".encode("ascii")).digest()
        base = 2 + int.from_bytes(seed, "big") % (value - 3)
        witness = pow(base, odd, value)
        if witness in (1, value - 1):
            continue
        for _ in range(powers - 1):
            witness = pow(witness, 2, value)
            if witness == value - 1:
                break
        else:
            return False
    return True


@dataclass(frozen=True)
class GroupParameters:
    parameter_id: str
    p: int
    q: int
    g: int
    h: int

    @property
    def digest(self) -> str:
        return hashlib.sha256(canonical_bytes({
            "schema_version": SCHEMA,
            "parameter_id": self.parameter_id,
            "p": format(self.p, "x"),
            "q": format(self.q, "x"),
            "g": format(self.g, "x"),
            "h": format(self.h, "x"),
        })).hexdigest()


def _hex_integer(value: Any, path: str) -> int:
    if not isinstance(value, str) or not value or value != value.lower():
        raise ValidationError(f"{path}: expected lowercase hexadecimal")
    try:
        result = int(value, 16)
    except ValueError as exc:
        raise ValidationError(f"{path}: invalid hexadecimal") from exc
    if result <= 0:
        raise ValidationError(f"{path}: expected positive integer")
    return result


def load_parameters(path: Path) -> GroupParameters:
    raw = load_json(path)
    if not isinstance(raw, dict) or raw.get("schema_version") != SCHEMA:
        raise ValidationError("unsupported group-parameter document")
    expected = {"schema_version", "parameter_id", "p", "q", "g", "h"}
    if set(raw) != expected:
        raise ValidationError("group-parameter fields do not match schema")
    parameter_id = raw["parameter_id"]
    if not isinstance(parameter_id, str) or not parameter_id:
        raise ValidationError("parameter id must be non-empty")
    parameters = GroupParameters(
        parameter_id=parameter_id,
        p=_hex_integer(raw["p"], "$.p"),
        q=_hex_integer(raw["q"], "$.q"),
        g=_hex_integer(raw["g"], "$.g"),
        h=_hex_integer(raw["h"], "$.h"),
    )
    if parameters.p != 2 * parameters.q + 1:
        raise ValidationError("parameters must describe a safe-prime subgroup")
    if not _probable_prime(parameters.q) or not _probable_prime(parameters.p):
        raise ValidationError("p or q is not probably prime")
    for name, generator in (("g", parameters.g), ("h", parameters.h)):
        if generator <= 1 or generator >= parameters.p:
            raise ValidationError(f"{name} is outside the group")
        if pow(generator, parameters.q, parameters.p) != 1:
            raise ValidationError(f"{name} is outside the q-order subgroup")
    if parameters.g == parameters.h:
        raise ValidationError("Pedersen generators must differ")
    return parameters
