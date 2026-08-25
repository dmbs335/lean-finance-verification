from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json, write_canonical_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import MctsSpibbError
from .model import load_plan
from .solver import solve, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-mcts-spibb")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--plan", required=True, type=Path)
    analyze.add_argument("--out", required=True, type=Path)
    check = subparsers.add_parser("verify")
    check.add_argument("--plan", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        plan = load_plan(args.plan, args.repository_root)
        if args.command == "analyze":
            report = solve(plan)
            write_canonical_json(args.out, report)
            gate = report["exact_root_gate"]
            print(
                f"proposal={gate['proposal_action']} "
                f"selected={gate['selected_action']} "
                f"gate={gate['passed']}"
            )
        else:
            verify(plan, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (MctsSpibbError, CanonicalValidationError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
