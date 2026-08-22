from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .errors import ModelFamilyError
from .model import load_problem
from .solver import solve, verify


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="lfv-model-family-synth")
    sub = result.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--model", required=True, type=Path)
    analyze.add_argument("--out", required=True, type=Path)
    check = sub.add_parser("verify")
    check.add_argument("--model", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        problem = load_problem(args.model)
        if args.command == "analyze":
            report = solve(problem)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(report, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            print(
                f"point={report['point_optimum'].get('selected', {}).get('channels', [])} "
                f"family={report['family_optimum'].get('selected', {}).get('channels', [])} "
                f"gap={report['underestimation_gap']}"
            )
        else:
            verify(problem, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (ModelFamilyError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
