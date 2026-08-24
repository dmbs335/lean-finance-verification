from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .analyzer import analyze, verify
from .errors import EpistemicEventStudyError
from .model import load_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-epistemic-event-study")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("analyze")
    run.add_argument("--plan", required=True, type=Path)
    run.add_argument("--out", required=True, type=Path)
    check = subparsers.add_parser("verify")
    check.add_argument("--plan", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        plan = load_plan(args.plan)
        if args.command == "analyze":
            report = analyze(plan)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(report, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            effect = report["gates"]["event_effect"]
            print(
                f"status={report['status']} "
                f"did={effect['did_numerator_bps']}/{effect['did_denominator']}"
            )
        else:
            verify(plan, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (EpistemicEventStudyError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
