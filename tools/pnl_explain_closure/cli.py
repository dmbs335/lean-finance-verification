from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json, write_canonical_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .analyzer import analyze, verify
from .errors import PnlExplainClosureError
from .model import load_problem


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-pnl-explain-closure")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--model", required=True, type=Path)
    analyze_parser.add_argument("--out", required=True, type=Path)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--model", required=True, type=Path)
    verify_parser.add_argument("--report", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        problem = load_problem(args.model)
        if args.command == "analyze":
            report = analyze(problem)
            write_canonical_json(args.out, report)
            aggregate = report["aggregate"]
            print(
                f"closed={aggregate['closed_count']} "
                f"partial={aggregate['partial_count']} "
                f"open={aggregate['open_count']}"
            )
        else:
            verify(problem, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (PnlExplainClosureError, CanonicalValidationError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
