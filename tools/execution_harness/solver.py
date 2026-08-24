from __future__ import annotations

import hashlib
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Fill, Problem

REPORT_SCHEMA = "lfv-proof-carrying-execution-report-v1"
ALLOWED_TRANSITIONS = {
    ("proposed", "shielded"), ("proposed", "cancelled"),
    ("shielded", "authorized"), ("shielded", "cancelled"),
    ("authorized", "submitted"), ("authorized", "cancelled"),
    ("authorized", "expired"), ("submitted", "acknowledged"),
    ("submitted", "cancelled"), ("submitted", "expired"),
    ("acknowledged", "partiallyFilled"), ("acknowledged", "filled"),
    ("acknowledged", "cancelled"), ("acknowledged", "expired"),
    ("partiallyFilled", "partiallyFilled"),
    ("partiallyFilled", "filled"), ("partiallyFilled", "cancelled"),
    ("partiallyFilled", "expired"), ("filled", "reconciled"),
    ("cancelled", "reconciled"), ("expired", "reconciled"),
}
SUBMIT_AUTHORITIES = {"microAutonomy", "boundedAutonomy"}


def _cash_delta(fill: Fill) -> int:
    notional = fill.qty * fill.price
    return -notional - fill.fee if fill.side == "buy" else notional - fill.fee


def _inventory_delta(fill: Fill) -> int:
    return fill.qty if fill.side == "buy" else -fill.qty


def solve(problem: Problem) -> dict[str, Any]:
    if problem.authority not in SUBMIT_AUTHORITIES:
        raise ValidationError("authority cannot submit an order")
    if problem.authorized_qty > problem.capital_cap_units:
        raise ValidationError("authorized quantity exceeds capital cap")
    transitions = list(zip(problem.lifecycle, problem.lifecycle[1:]))
    illegal = [pair for pair in transitions if pair not in ALLOWED_TRANSITIONS]
    if illegal:
        raise ValidationError(f"illegal lifecycle transition: {illegal[0]}")
    if problem.lifecycle[0] != "proposed":
        raise ValidationError("lifecycle must start at proposed")
    if problem.lifecycle[-1] != "reconciled":
        raise ValidationError("lifecycle must end at reconciled")
    terminal = problem.lifecycle[-2]
    if terminal not in {"filled", "cancelled", "expired"}:
        raise ValidationError("reconciliation requires a terminal order state")
    fill_ids = [fill.id for fill in problem.fills]
    if len(fill_ids) != len(set(fill_ids)):
        raise ValidationError("duplicate fill id")
    if problem.fills and "acknowledged" not in problem.lifecycle:
        raise ValidationError("fills require broker acknowledgement")
    for fill in problem.fills:
        if fill.side != problem.side:
            raise ValidationError("fill side does not match order side")
        if problem.side == "buy" and fill.price > problem.limit_price:
            raise ValidationError("buy fill exceeds limit price")
        if problem.side == "sell" and fill.price < problem.limit_price:
            raise ValidationError("sell fill is below limit price")
    filled_qty = sum(fill.qty for fill in problem.fills)
    if filled_qty > problem.authorized_qty:
        raise ValidationError("fills exceed authorized quantity")
    if terminal == "filled" and filled_qty != problem.authorized_qty:
        raise ValidationError("filled terminal requires exact authorized quantity")
    if terminal in {"cancelled", "expired"} and filled_qty == problem.authorized_qty:
        raise ValidationError("cancelled or expired order cannot be fully filled")
    cash_delta = sum(_cash_delta(fill) for fill in problem.fills)
    inventory_delta = sum(_inventory_delta(fill) for fill in problem.fills)
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "order": {
            "id": problem.order_id,
            "side": problem.side,
            "authority": problem.authority,
            "capital_cap_units": problem.capital_cap_units,
            "authorized_qty": problem.authorized_qty,
            "limit_price": problem.limit_price,
        },
        "lifecycle": {
            "states": list(problem.lifecycle),
            "transitions": [list(pair) for pair in transitions],
            "valid": True,
            "terminal_before_reconciliation": terminal,
        },
        "fills": [
            {
                "id": fill.id,
                "side": fill.side,
                "qty": fill.qty,
                "price": fill.price,
                "fee": fill.fee,
                "cash_delta": _cash_delta(fill),
                "inventory_delta": _inventory_delta(fill),
            }
            for fill in problem.fills
        ],
        "reconciliation": {
            "filled_qty": filled_qty,
            "remaining_authorized_qty": problem.authorized_qty - filled_qty,
            "cash_delta": cash_delta,
            "inventory_delta": inventory_delta,
            "initial_cash": problem.initial_cash,
            "final_cash": problem.initial_cash + cash_delta,
            "initial_inventory": problem.initial_inventory,
            "final_inventory": problem.initial_inventory + inventory_delta,
            "unique_fill_ids": True,
            "within_authorization": True,
            "reconciled": True,
        },
        "controlled_claims": {
            "authority_permitted_submission": True,
            "no_illegal_transition": True,
            "no_duplicate_fill": True,
            "no_overfill": True,
            "limit_price_respected": True,
            "cash_conserved": True,
            "inventory_conserved": True,
        },
        "residual_boundaries": [
            "broker acknowledgements and fills are declared controlled inputs",
            "no network authenticity or exchange finality claim",
            "capital cap is a governance unit rather than calibrated market capacity",
            "no investment recommendation or future-return claim",
        ],
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "execution report does not match exact recomputation"
        )
    return expected
