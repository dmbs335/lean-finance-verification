from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

from .errors import ValidationError
from .manifest import verify_manifest

PLAN_SCHEMA = "lfv-pit-research-plan-v1"
REPORT_SCHEMA = "lfv-pit-vendor-import-report-v1"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _nat(value: str, path: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise ValidationError(f"{path}: expected integer") from exc
    if result < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return result


def _optional_nat(value: str, path: str) -> int | None:
    return None if value == "" else _nat(value, path)


def import_study(manifest: Any, package_root: Path, public_key: Path,
                 plan_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    verified = verify_manifest(manifest, package_root, public_key)
    plan = load_json(plan_path)
    if not isinstance(plan, dict) or plan.get("schema_version") != PLAN_SCHEMA:
        raise ValidationError("unsupported PIT research plan")
    file_by_kind = {item["kind"]: package_root / item["path"] for item in verified["files"]}
    vintages = [{
        "id": row["id"],
        "revision": _nat(row["revision"], "revision"),
        "first_published_at": _nat(row["first_published_at"], "first_published_at"),
        "supersedes": row["supersedes"] or None,
    } for row in _rows(file_by_kind["vintages"])]
    vintage_ids = {item["id"] for item in vintages}
    if len(vintage_ids) != len(vintages):
        raise ValidationError("vendor vintages contain duplicate ids")
    by_id = {item["id"]: item for item in vintages}
    for newer in vintages:
        if newer["supersedes"] is None:
            continue
        older = by_id.get(newer["supersedes"])
        if older is None or not (
            older["revision"] < newer["revision"]
            and older["first_published_at"] < newer["first_published_at"]
        ):
            raise ValidationError("vendor revision chain is invalid")
    assets = [{
        "id": row["asset"],
        "listed_at": _nat(row["listed_at"], "listed_at"),
        "delisted_at": _optional_nat(row["delisted_at"], "delisted_at"),
    } for row in _rows(file_by_kind["listings"])]
    asset_ids = {item["id"] for item in assets}
    if len(asset_ids) != len(assets):
        raise ValidationError("vendor listings contain duplicate assets")
    prices = [{
        "asset": row["asset"],
        "time": _nat(row["time"], "price time"),
        "available_at": _nat(row["available_at"], "price available_at"),
        "value": _nat(row["value"], "price value"),
        "vintage": row["vintage"],
    } for row in _rows(file_by_kind["prices"])]
    for price in prices:
        if price["asset"] not in asset_ids or price["vintage"] not in vintage_ids:
            raise ValidationError("vendor price references unknown asset or vintage")
        if price["value"] == 0:
            raise ValidationError("vendor price cannot be zero")
    actions = [{
        "id": row["id"],
        "asset": row["asset"],
        "announced_at": _nat(row["announced_at"], "action announced_at"),
        "effective_at": _nat(row["effective_at"], "action effective_at"),
    } for row in _rows(file_by_kind["corporate_actions"])]
    if any(action["asset"] not in asset_ids for action in actions):
        raise ValidationError("corporate action references unknown asset")
    study = {
        "schema_version": "lfv-pit-micro-study-v1",
        "name": plan["name"],
        "vintages": vintages,
        "assets": assets,
        "prices": prices,
        "universe_snapshots": plan["universe_snapshots"],
        "decisions": plan["decisions"],
        "corporate_actions": actions,
        "adjustments": plan["adjustments"],
        "evaluation_contract": plan["evaluation_contract"],
    }
    report = {
        "schema_version": REPORT_SCHEMA,
        "package": verified,
        "study_sha256": hashlib.sha256(canonical_bytes(study)).hexdigest(),
        "study_name": study["name"],
        "vintage_count": len(vintages),
        "asset_count": len(assets),
        "price_count": len(prices),
        "corporate_action_count": len(actions),
    }
    report["report_sha256"] = hashlib.sha256(canonical_bytes(report)).hexdigest()
    return study, report
