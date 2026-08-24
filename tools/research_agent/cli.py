from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json

from .candidate import (
    evaluate_candidate_batch,
    load_candidate_batch,
    verify_candidate_batch,
)
from .errors import ResearchAgentError
from .model import load_plan
from .runner import run, verify


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


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

    gate_candidates = subparsers.add_parser("gate-candidates")
    gate_candidates.add_argument("--batch", required=True, type=Path)
    gate_candidates.add_argument("--out", required=True, type=Path)

    verify_candidates = subparsers.add_parser("verify-candidates")
    verify_candidates.add_argument("--batch", required=True, type=Path)
    verify_candidates.add_argument("--report", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            plan = load_plan(args.plan, args.repository_root)
            report = run(plan)
            _write_json(args.out, report)
            print(
                f"status={report['status']} "
                f"stages={len(report['completed_stages'])}"
            )
        elif args.command == "verify":
            plan = load_plan(args.plan, args.repository_root)
            verify(plan, load_json(args.report))
            print(f"verified {args.report}")
        elif args.command == "gate-candidates":
            batch = load_candidate_batch(args.batch)
            report = evaluate_candidate_batch(batch)
            _write_json(args.out, report)
            counts = report["decision_counts"]
            print(
                "human_review="
                f"{counts['advanceToHumanReview']} "
                f"repair={counts['repairEvidence']} "
                f"reject={counts['rejectCandidate']}"
            )
        else:
            batch = load_candidate_batch(args.batch)
            verify_candidate_batch(batch, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (ResearchAgentError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
