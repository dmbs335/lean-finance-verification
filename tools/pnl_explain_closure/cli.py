from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json, write_canonical_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .analyzer import analyze, verify
from .errors import PnlExplainClosureError
from .gs_quant_conformance import (
    load_conformance_model,
    run_conformance,
    verify_conformance,
)
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

    conformance_parser = subparsers.add_parser("gs-quant-conformance")
    conformance_parser.add_argument("--model", required=True, type=Path)
    conformance_parser.add_argument("--out", required=True, type=Path)

    conformance_verify_parser = subparsers.add_parser(
        "verify-gs-quant-conformance"
    )
    conformance_verify_parser.add_argument("--model", required=True, type=Path)
    conformance_verify_parser.add_argument("--report", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            problem = load_problem(args.model)
            report = analyze(problem)
            write_canonical_json(args.out, report)
            aggregate = report["aggregate"]
            print(
                f"closed={aggregate['closed_count']} "
                f"partial={aggregate['partial_count']} "
                f"open={aggregate['open_count']}"
            )
        elif args.command == "verify":
            problem = load_problem(args.model)
            verify(problem, load_json(args.report))
            print(f"verified {args.report}")
        elif args.command == "gs-quant-conformance":
            model = load_conformance_model(args.model)
            report = run_conformance(model)
            write_canonical_json(args.out, report)
            print(
                f"verified {model.package_name} {model.distribution_version} "
                f"{model.symbol}"
            )
        else:
            model = load_conformance_model(args.model)
            verify_conformance(model, load_json(args.report))
            print(f"verified {args.report}")
        return 0
    except (PnlExplainClosureError, CanonicalValidationError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
