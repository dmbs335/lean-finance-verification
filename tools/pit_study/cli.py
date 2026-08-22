from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .checker import check, verify
from .errors import PITStudyError
from .model import load_study


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-pit-study")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--study", required=True, type=Path)
    analyze.add_argument("--out", required=True, type=Path)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--study", required=True, type=Path)
    verify_parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        study = load_study(args.study)
        if args.command == "analyze":
            report = check(study)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(report, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            print("selections=" + ",".join(
                decision["selected"] for decision in report["decisions"]
            ))
        else:
            verify(study, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (PITStudyError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
