from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json, write_canonical_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import SafeTreeSearchError
from .model import load_problem
from .solver import solve, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-safe-tree-policy-search")
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
            report = solve(problem)
            write_canonical_json(args.out, report)
            root = report["root_decision"]
            print(
                f"action={root['action']} "
                f"lower={root['pessimistic_lower_value']['numerator']}/"
                f"{root['pessimistic_lower_value']['denominator']}"
            )
        else:
            verify(problem, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (SafeTreeSearchError, CanonicalValidationError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
