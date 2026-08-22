from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .canonical import (
    CANONICAL_FORMAT,
    load_json,
    make_artifact_ref,
    validate_artifact_ref,
    write_canonical_json,
    write_pretty_json,
)
from .errors import ValidationError

if TYPE_CHECKING:
    from .rfc3161 import Rfc3161Trust

LEDGER_SCHEMA = "lfv-search-ledger-v1"
LEDGER_ENTRY_SCHEMA = "lfv-search-ledger-entry-v1"
ANCHOR_SCHEMA = "lfv-ledger-anchor-v1"


def _nat(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected a non-negative integer")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected a non-empty string")
    return value


def _entry_body(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "hypothesis_id": entry["hypothesis_id"],
        "parameters": entry["parameters"],
        "code": entry["code"],
        "registered_at": entry["registered_at"],
        "previous_commitment": entry["previous_commitment"],
    }


def empty_ledger() -> dict[str, Any]:
    return {
        "schema_version": LEDGER_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "entries": [],
    }


def load_ledger(path: Path, *, allow_missing: bool = False) -> dict[str, Any]:
    if allow_missing and not path.exists():
        return empty_ledger()
    ledger = load_json(path)
    if not isinstance(ledger, dict):
        raise ValidationError("ledger: expected an object")
    verify_ledger(ledger)
    return ledger


def verify_ledger(ledger: Any) -> dict[str, Any]:
    if not isinstance(ledger, dict):
        raise ValidationError("ledger: expected an object")
    expected_fields = {"schema_version", "canonical_format", "entries"}
    unknown = set(ledger) - expected_fields
    missing = expected_fields - set(ledger)
    if unknown:
        raise ValidationError(f"ledger: unknown fields: {sorted(unknown)}")
    if missing:
        raise ValidationError(f"ledger: missing fields: {sorted(missing)}")
    if ledger["schema_version"] != LEDGER_SCHEMA:
        raise ValidationError(f"ledger.schema_version: expected {LEDGER_SCHEMA!r}")
    if ledger["canonical_format"] != CANONICAL_FORMAT:
        raise ValidationError(f"ledger.canonical_format: expected {CANONICAL_FORMAT!r}")
    entries = ledger["entries"]
    if not isinstance(entries, list):
        raise ValidationError("ledger.entries: expected an array")

    previous_ref: dict[str, str] | None = None
    previous_time: int | None = None
    normalized_entries: list[dict[str, Any]] = []
    for index, raw in enumerate(entries):
        path = f"ledger.entries[{index}]"
        if not isinstance(raw, dict):
            raise ValidationError(f"{path}: expected an object")
        expected_entry_fields = {
            "hypothesis_id",
            "parameters",
            "code",
            "registered_at",
            "previous_commitment",
            "commitment",
        }
        unknown_entry = set(raw) - expected_entry_fields
        missing_entry = expected_entry_fields - set(raw)
        if unknown_entry:
            raise ValidationError(f"{path}: unknown fields: {sorted(unknown_entry)}")
        if missing_entry:
            raise ValidationError(f"{path}: missing fields: {sorted(missing_entry)}")
        hypothesis = _string(raw["hypothesis_id"], f"{path}.hypothesis_id")
        parameters = validate_artifact_ref(raw["parameters"], f"{path}.parameters")
        code = validate_artifact_ref(raw["code"], f"{path}.code")
        registered_at = _nat(raw["registered_at"], f"{path}.registered_at")
        commitment = validate_artifact_ref(raw["commitment"], f"{path}.commitment")
        if commitment["schema_id"] != LEDGER_ENTRY_SCHEMA:
            raise ValidationError(
                f"{path}.commitment.schema_id: expected {LEDGER_ENTRY_SCHEMA!r}"
            )

        previous = raw["previous_commitment"]
        if index == 0:
            if previous is not None:
                raise ValidationError(f"{path}.previous_commitment: first entry must be null")
            normalized_previous = None
        else:
            normalized_previous = validate_artifact_ref(
                previous, f"{path}.previous_commitment"
            )
            if normalized_previous != previous_ref:
                raise ValidationError(
                    f"{path}.previous_commitment: does not match prior commitment"
                )
            assert previous_time is not None
            if previous_time > registered_at:
                raise ValidationError(
                    f"{path}.registered_at: ledger timestamps must be monotone"
                )

        normalized = {
            "hypothesis_id": hypothesis,
            "parameters": parameters,
            "code": code,
            "registered_at": registered_at,
            "previous_commitment": normalized_previous,
            "commitment": commitment,
        }
        expected_commitment, _ = make_artifact_ref(
            kind="searchLedger",
            schema_id=LEDGER_ENTRY_SCHEMA,
            payload=_entry_body(normalized),
            algorithm=commitment["algorithm"],
        )
        if expected_commitment != commitment:
            raise ValidationError(f"{path}.commitment: canonical entry digest mismatch")

        normalized_entries.append(normalized)
        previous_ref = commitment
        previous_time = registered_at

    return {
        "schema_version": LEDGER_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "entries": normalized_entries,
    }


def append_trial(
    ledger: dict[str, Any],
    *,
    hypothesis_id: str,
    parameters: dict[str, str],
    code: dict[str, str],
    registered_at: int,
    algorithm: str,
) -> dict[str, Any]:
    verified = verify_ledger(ledger)
    if not hypothesis_id:
        raise ValidationError("hypothesis_id must be non-empty")
    if registered_at < 0:
        raise ValidationError("registered_at must be non-negative")
    validate_artifact_ref(parameters, "parameters")
    validate_artifact_ref(code, "code")
    entries = list(verified["entries"])
    if entries and entries[-1]["registered_at"] > registered_at:
        raise ValidationError("registered_at precedes the last ledger entry")
    previous = entries[-1]["commitment"] if entries else None
    entry: dict[str, Any] = {
        "hypothesis_id": hypothesis_id,
        "parameters": deepcopy(parameters),
        "code": deepcopy(code),
        "registered_at": registered_at,
        "previous_commitment": deepcopy(previous),
    }
    commitment, _ = make_artifact_ref(
        kind="searchLedger",
        schema_id=LEDGER_ENTRY_SCHEMA,
        payload=entry,
        algorithm=algorithm,
    )
    entry["commitment"] = commitment
    result = {
        "schema_version": LEDGER_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "entries": entries + [entry],
    }
    return verify_ledger(result)


def write_ledger(path: Path, ledger: dict[str, Any]) -> None:
    verified = verify_ledger(ledger)
    write_canonical_json(path, verified)
    write_pretty_json(path.with_suffix(path.suffix + ".pretty"), verified)


def make_local_anchor(
    ledger: dict[str, Any], *, anchored_at: int, provider: str = "local-development"
) -> dict[str, Any]:
    verified = verify_ledger(ledger)
    entries = verified["entries"]
    if not entries:
        raise ValidationError("cannot anchor an empty ledger")
    if anchored_at < entries[-1]["registered_at"]:
        raise ValidationError("anchor time precedes the final ledger entry")
    return {
        "schema_version": ANCHOR_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "commitment": deepcopy(entries[-1]["commitment"]),
        "entry_count": len(entries),
        "anchored_at": anchored_at,
        "provider": provider,
        "evidence_id": f"{provider}:{entries[-1]['commitment']['digest']}",
    }


def load_anchor(
    path: Path,
    *,
    allow_local: bool = False,
    rfc3161_trust: Rfc3161Trust | None = None,
) -> dict[str, Any]:
    return verify_anchor(
        load_json(path),
        allow_local=allow_local,
        rfc3161_trust=rfc3161_trust,
    )


def verify_anchor(
    anchor: Any,
    ledger: dict[str, Any] | None = None,
    *,
    cutoff_time: int | None = None,
    allow_local: bool = False,
    rfc3161_trust: Rfc3161Trust | None = None,
) -> dict[str, Any]:
    if not isinstance(anchor, dict):
        raise ValidationError("anchor: expected an object")
    required = {
        "schema_version",
        "canonical_format",
        "commitment",
        "entry_count",
        "anchored_at",
        "provider",
        "evidence_id",
    }
    allowed = required | {"evidence"}
    unknown = set(anchor) - allowed
    missing = required - set(anchor)
    if unknown:
        raise ValidationError(f"anchor: unknown fields: {sorted(unknown)}")
    if missing:
        raise ValidationError(f"anchor: missing fields: {sorted(missing)}")
    if anchor["schema_version"] != ANCHOR_SCHEMA:
        raise ValidationError(f"anchor.schema_version: expected {ANCHOR_SCHEMA!r}")
    if anchor["canonical_format"] != CANONICAL_FORMAT:
        raise ValidationError(f"anchor.canonical_format: expected {CANONICAL_FORMAT!r}")
    commitment = validate_artifact_ref(anchor["commitment"], "anchor.commitment")
    entry_count = _nat(anchor["entry_count"], "anchor.entry_count")
    anchored_at = _nat(anchor["anchored_at"], "anchor.anchored_at")
    provider = _string(anchor["provider"], "anchor.provider")
    evidence_id = _string(anchor["evidence_id"], "anchor.evidence_id")

    normalized: dict[str, Any] = {
        "schema_version": ANCHOR_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "commitment": commitment,
        "entry_count": entry_count,
        "anchored_at": anchored_at,
        "provider": provider,
        "evidence_id": evidence_id,
    }

    if provider == "local-development":
        if "evidence" in anchor:
            raise ValidationError("local-development anchors must not claim external evidence")
        if not allow_local:
            raise ValidationError(
                "local-development anchor rejected; pass --allow-local-anchor only for fixtures"
            )
    elif provider == "rfc3161":
        from .rfc3161 import verify_rfc3161_anchor_evidence

        normalized["evidence"] = verify_rfc3161_anchor_evidence(
            {**normalized, "evidence": anchor.get("evidence")},
            trust=rfc3161_trust,
        )
    else:
        raise ValidationError(f"unsupported anchor provider: {provider!r}")

    if ledger is not None:
        verified_ledger = verify_ledger(ledger)
        entries = verified_ledger["entries"]
        if not entries:
            raise ValidationError("anchor cannot bind an empty ledger")
        if entry_count != len(entries):
            raise ValidationError("anchor.entry_count does not match the ledger length")
        if commitment != entries[-1]["commitment"]:
            raise ValidationError("anchor.commitment does not match the terminal ledger entry")
        if anchored_at < entries[-1]["registered_at"]:
            raise ValidationError("anchor time precedes the terminal ledger entry")
    if cutoff_time is not None and anchored_at > cutoff_time:
        raise ValidationError("anchor was not available by the decision cutoff")
    return normalized


def find_selected_trial(
    ledger: dict[str, Any],
    *,
    strategy_id: str,
    parameters: dict[str, str],
    code: dict[str, str],
    cutoff_time: int,
) -> tuple[int, dict[str, Any]]:
    verified = verify_ledger(ledger)
    matches: list[tuple[int, dict[str, Any]]] = []
    for index, entry in enumerate(verified["entries"]):
        if (
            entry["hypothesis_id"] == strategy_id
            and entry["parameters"] == parameters
            and entry["code"] == code
            and entry["registered_at"] <= cutoff_time
        ):
            matches.append((index, entry))
    if not matches:
        raise ValidationError(
            "no preregistered trial matches the selected strategy, code, and parameters"
        )
    return matches[-1]
