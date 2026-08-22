from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyze import analyze, verify_report
from .canonical import canonical_bytes, load_json, write_canonical_json, write_pretty_json
from .errors import TaxonomyError, ValidationError


def _path(value: str) -> Path:
    return Path(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lfv-evidence-taxonomy",
        description=(
            "Classify adversarial histories by separator signatures and "
            "detect genuinely new evidence obligations"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    synth = subparsers.add_parser("synth", help="emit a canonical taxonomy report")
    synth.add_argument("--spec", required=True, type=_path)
    synth.add_argument("--out", required=True, type=_path)
    synth.add_argument("--pretty", action="store_true")
    verify = subparsers.add_parser("verify", help="recompute and verify a report")
    verify.add_argument("--spec", required=True, type=_path)
    verify.add_argument("--report", required=True, type=_path)
    check = subparsers.add_parser(
        "check-generated", help="fail when a checked-in taxonomy report drifts"
    )
    check.add_argument("--spec", required=True, type=_path)
    check.add_argument("--report", required=True, type=_path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "synth":
            report = analyze(args.spec)
            write_canonical_json(args.out, report)
            if args.pretty:
                write_pretty_json(args.out.with_suffix(".pretty.json"), report)
            print(f"wrote {args.out}")
            for candidate in report["candidate_novelty"]:
                print(
                    f"{candidate['attack']}={candidate['classification']} "
                    f"separators={','.join(candidate['separators'])}"
                )
        elif args.command == "verify":
            verify_report(args.spec, load_json(args.report))
            print(f"verified {args.report}")
        elif args.command == "check-generated":
            expected = analyze(args.spec)
            if args.report.read_bytes() != canonical_bytes(expected):
                raise ValidationError(
                    f"taxonomy report drift: regenerate {args.report}"
                )
            print("generated evidence-taxonomy report is reproducible")
        else:
            parser.error(f"unknown command: {args.command}")
        return 0
    except (TaxonomyError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
