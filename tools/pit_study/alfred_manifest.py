from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json
from tools.pit_study.alfred_revision import PACKAGE_SCHEMA
from tools.pit_study.errors import ValidationError

SPEC_SCHEMA = "lfv-alfred-vintage-package-spec-v1"


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def _safe_path(root: Path, relative: str, path: str) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValidationError(f"{path}: unsafe relative path")
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValidationError(f"{path}: path escapes package root") from exc
    if not candidate.is_file():
        raise ValidationError(f"{path}: missing package file {relative}")
    return candidate


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(spec_path: Path, out_path: Path) -> dict[str, Any]:
    raw = _object(load_json(spec_path), "$")
    expected = {
        "schema_version",
        "series_id",
        "latest_vintage_date",
        "release_calendar",
        "responses",
    }
    if set(raw) != expected or raw["schema_version"] != SPEC_SCHEMA:
        raise ValidationError("$: fields or schema do not match package spec")
    root = spec_path.resolve().parent
    release_relative = _string(
        raw["release_calendar"], "$.release_calendar"
    )
    release_path = _safe_path(
        root, release_relative, "$.release_calendar"
    )
    responses_raw = raw["responses"]
    if not isinstance(responses_raw, list):
        raise ValidationError("$.responses: expected array")
    responses: list[dict[str, str]] = []
    for index, item in enumerate(responses_raw):
        item_path = f"$.responses[{index}]"
        obj = _object(item, item_path)
        expected_item = {
            "kind",
            "as_of_date",
            "vintage_date",
            "relative_path",
        }
        if set(obj) != expected_item:
            raise ValidationError(f"{item_path}: fields do not match")
        relative_path = _string(
            obj["relative_path"], f"{item_path}.relative_path"
        )
        response_path = _safe_path(
            root, relative_path, f"{item_path}.relative_path"
        )
        responses.append(
            {
                "kind": _string(obj["kind"], f"{item_path}.kind"),
                "as_of_date": _string(
                    obj["as_of_date"], f"{item_path}.as_of_date"
                ),
                "vintage_date": _string(
                    obj["vintage_date"], f"{item_path}.vintage_date"
                ),
                "relative_path": relative_path,
                "sha256": _sha256(response_path),
            }
        )
    manifest: dict[str, Any] = {
        "schema_version": PACKAGE_SCHEMA,
        "series_id": _string(raw["series_id"], "$.series_id"),
        "latest_vintage_date": _string(
            raw["latest_vintage_date"], "$.latest_vintage_date"
        ),
        "release_calendar": {
            "relative_path": release_relative,
            "sha256": _sha256(release_path),
        },
        "responses": responses,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(canonical_bytes(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-alfred-manifest")
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        build_manifest(args.spec, args.out)
        print(f"wrote {args.out}")
        return 0
    except (ValidationError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
