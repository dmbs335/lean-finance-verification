from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json, write_canonical_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .audit import audit, verify
from .errors import TemporalNoninterferenceError
from .model import load_problem


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-temporal-noninterference")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--model", required=True, type=Path)
    analyze.add_argument("--out", required=True, type=Path)

    check = subparsers.add_parser("verify")
    check.add_argument("--model", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        problem = load_problem(args.model)
        if args.command == "analyze":
            report = audit(problem)
            write_canonical_json(args.out, report)
            aggregate = report["aggregate"]
            print(
                f"safe={aggregate['safe_engines']} "
                f"unsafe={aggregate['unsafe_engines']} "
                f"temporal_violation_engines="
                f"{aggregate['temporal_violation_engine_count']}"
            )
        else:
            verify(problem, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (
        TemporalNoninterferenceError,
        CanonicalValidationError,
        OSError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
