from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .errors import VendorImportError
from .importer import import_study
from .manifest import build_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-pit-vendor-import")
    sub = parser.add_subparsers(dest="command", required=True)
    pack = sub.add_parser("pack")
    pack.add_argument("--metadata", required=True, type=Path)
    pack.add_argument("--package-root", required=True, type=Path)
    pack.add_argument("--private-key", required=True, type=Path)
    pack.add_argument("--public-key", required=True, type=Path)
    pack.add_argument("--signed-at", required=True, type=int)
    pack.add_argument("--out", required=True, type=Path)
    load = sub.add_parser("import")
    load.add_argument("--manifest", required=True, type=Path)
    load.add_argument("--package-root", required=True, type=Path)
    load.add_argument("--public-key", required=True, type=Path)
    load.add_argument("--plan", required=True, type=Path)
    load.add_argument("--out-study", required=True, type=Path)
    load.add_argument("--out-report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "pack":
            result = build_manifest(
                args.metadata, args.package_root, args.public_key,
                args.private_key, signed_at=args.signed_at,
            )
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        else:
            study, report = import_study(
                load_json(args.manifest), args.package_root,
                args.public_key, args.plan,
            )
            args.out_study.parent.mkdir(parents=True, exist_ok=True)
            args.out_report.parent.mkdir(parents=True, exist_ok=True)
            args.out_study.write_text(json.dumps(study, sort_keys=True, separators=(",", ":")), encoding="utf-8")
            args.out_report.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return 0
    except (VendorImportError, OSError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
