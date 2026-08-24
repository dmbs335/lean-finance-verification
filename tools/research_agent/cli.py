from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .errors import ResearchAgentError
from .model import load_plan
from .runner import run, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-research-agent")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    subparsers = parser.add_subparsers(dest="command", required=True)

    execute = subparsers.add_parser("run")
    execute.add_argument("--plan", required=True, type=Path)
    execute.add_argument("--out", required=True, type=Path)

    check = subparsers.add_parser("verify")
    check.add_argument("--plan", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        plan = load_plan(args.plan, args.repository_root)
        if args.command == "run":
            report = run(plan)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(report, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            print(
                f"status={report['status']} "
                f"stages={len(report['completed_stages'])}"
            )
        else:
            verify(plan, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (ResearchAgentError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
