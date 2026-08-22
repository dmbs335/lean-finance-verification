from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .errors import SymbolicEvidenceError
from .model import load_corpus
from .solver import solve, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-symbolic-evidence")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--corpus", required=True, type=Path)
    analyze.add_argument("--out", required=True, type=Path)
    check = sub.add_parser("verify")
    check.add_argument("--corpus", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        corpus = load_corpus(args.corpus)
        if args.command == "analyze":
            report = solve(corpus)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(report, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            print(
                f"attacks={report['attack_count']} "
                f"classes={len(report['signature_classes'])} "
                f"selected={report['selected']['channels']} "
                f"cost={report['selected']['cost']}"
            )
        else:
            verify(corpus, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (SymbolicEvidenceError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
