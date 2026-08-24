from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .errors import FakeAlphaError
from .model import load_benchmark
from .solver import solve, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-fake-alpha-benchmark")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--benchmark", required=True, type=Path)
    analyze.add_argument("--out", required=True, type=Path)

    check = subparsers.add_parser("verify")
    check.add_argument("--benchmark", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        benchmark = load_benchmark(args.benchmark)
        if args.command == "analyze":
            report = solve(benchmark)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(report, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            selected = report["synthesis"]["selected"]
            print(
                f"selected={selected['channels']} cost={selected['cost']} "
                f"observed_top={report['ground_truth']['observed_top']} "
                f"clean_top={report['ground_truth']['clean_top']}"
            )
        else:
            verify(benchmark, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (FakeAlphaError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
