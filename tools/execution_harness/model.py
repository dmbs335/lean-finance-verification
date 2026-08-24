from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-proof-carrying-execution-v1"
AUTHORITY_LEVELS = {
    "observe", "shadow", "recommend", "microAutonomy",
    "boundedAutonomy", "fallback", "revoked",
}
ORDER_STATES = {
    "proposed", "shielded", "authorized", "submitted", "acknowledged",
    "partiallyFilled", "filled", "cancelled", "expired", "reconciled",
}


@dataclass(frozen=True)
class Fill:
    id: str
    side: str
    qty: int
    price: int
    fee: int


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    order_id: str
    side: str
    authority: str
    capital_cap_units: int
    authorized_qty: int
    limit_price: int
    lifecycle: tuple[str, ...]
    fills: tuple[Fill, ...]
    initial_cash: int
    initial_inventory: int


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path}: expected integer")
    return value


def _natural(value: Any, path: str, *, positive: bool = False) -> int:
    result = _integer(value, path)
    if result < 0 or (positive and result == 0):
        qualifier = "positive" if positive else "non-negative"
        raise ValidationError(f"{path}: expected {qualifier} integer")
    return result


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version", "name", "order", "lifecycle", "fills",
        "initial_cash", "initial_inventory",
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")
    order = _object(raw["order"], "$.order")
    if set(order) != {
        "id", "side", "authority", "capital_cap_units",
        "authorized_qty", "limit_price",
    }:
        raise ValidationError("$.order: fields do not match")
    side = _string(order["side"], "$.order.side")
    if side not in {"buy", "sell"}:
        raise ValidationError("$.order.side: expected buy or sell")
    authority = _string(order["authority"], "$.order.authority")
    if authority not in AUTHORITY_LEVELS:
        raise ValidationError("$.order.authority: unsupported level")
    lifecycle_raw = raw["lifecycle"]
    if not isinstance(lifecycle_raw, list) or len(lifecycle_raw) < 2 or any(
        not isinstance(state, str) or state not in ORDER_STATES
        for state in lifecycle_raw
    ):
        raise ValidationError("$.lifecycle: expected known order states")
    fills_raw = raw["fills"]
    if not isinstance(fills_raw, list):
        raise ValidationError("$.fills: expected array")
    fills: list[Fill] = []
    for index, item in enumerate(fills_raw):
        item_path = f"$.fills[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"id", "side", "qty", "price", "fee"}:
            raise ValidationError(f"{item_path}: fields do not match")
        fill_side = _string(obj["side"], f"{item_path}.side")
        if fill_side not in {"buy", "sell"}:
            raise ValidationError(f"{item_path}.side: expected buy or sell")
        fills.append(Fill(
            id=_string(obj["id"], f"{item_path}.id"),
            side=fill_side,
            qty=_natural(obj["qty"], f"{item_path}.qty", positive=True),
            price=_natural(obj["price"], f"{item_path}.price", positive=True),
            fee=_natural(obj["fee"], f"{item_path}.fee"),
        ))
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        order_id=_string(order["id"], "$.order.id"),
        side=side,
        authority=authority,
        capital_cap_units=_natural(
            order["capital_cap_units"], "$.order.capital_cap_units"
        ),
        authorized_qty=_natural(
            order["authorized_qty"], "$.order.authorized_qty", positive=True
        ),
        limit_price=_natural(
            order["limit_price"], "$.order.limit_price", positive=True
        ),
        lifecycle=tuple(lifecycle_raw),
        fills=tuple(fills),
        initial_cash=_integer(raw["initial_cash"], "$.initial_cash"),
        initial_inventory=_integer(
            raw["initial_inventory"], "$.initial_inventory"
        ),
    )
