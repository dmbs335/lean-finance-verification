from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json, write_canonical_json, write_pretty_json
from tools.evidence_synth.errors import SynthesisError

from .model import load_model
from .solver import solve_model, verify_report


def _path(value: str) -> Path:
    return Path(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lfv-semantics-version-space",
        description=(
            "Enumerate finite Boolean action semantics consistent with observed "
            "positive transitions and negative enablement probes"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="build a version-space report")
    build.add_argument("--model", required=True, type=_path)
    build.add_argument("--out", required=True, type=_path)
    build.add_argument("--pretty", action="store_true")
    verify = subparsers.add_parser("verify", help="recompute and verify a report")
    verify.add_argument("--model", required=True, type=_path)
    verify.add_argument("--report", required=True, type=_path)
    return parser


def _command_build(args: argparse.Namespace) -> None:
    report = solve_model(load_model(args.model))
    write_canonical_json(args.out, report)
    if args.pretty:
        write_pretty_json(args.out.with_suffix(".pretty.json"), report)
    print(f"wrote {args.out}")
    print(f"consistent_hypotheses={report['consistent_hypothesis_count']}")
    if report["best_probe"] is not None:
        print(f"best_probe={report['best_probe']['state']}")


def _command_verify(args: argparse.Namespace) -> None:
    model = load_model(args.model)
    report = load_json(args.report)
    verify_report(model, report)
    print(f"verified {args.report}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            _command_build(args)
        elif args.command == "verify":
            _command_verify(args)
        else:
            parser.error(f"unknown command: {args.command}")
        return 0
    except (SynthesisError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
