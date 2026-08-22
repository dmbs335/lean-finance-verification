from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.evidence_synth.canonical import load_json, write_canonical_json, write_pretty_json
from tools.evidence_synth.errors import SynthesisError
from tools.evidence_synth.model import load_model

from .config import load_config
from .solver import solve_taxonomy, verify_report


def _path(value: str) -> Path:
    return Path(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lfv-evidence-taxonomy",
        description=(
            "Classify finite adversarial histories by exact evidence obligations, "
            "subsumption, and marginal evidence debt"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="build a canonical taxonomy report")
    build.add_argument("--model", required=True, type=_path)
    build.add_argument("--config", required=True, type=_path)
    build.add_argument("--out", required=True, type=_path)
    build.add_argument("--pretty", action="store_true")

    verify = subparsers.add_parser("verify", help="recompute and verify a report")
    verify.add_argument("--model", required=True, type=_path)
    verify.add_argument("--config", required=True, type=_path)
    verify.add_argument("--report", required=True, type=_path)
    return parser


def _command_build(args: argparse.Namespace) -> None:
    model = load_model(args.model)
    config = load_config(args.config)
    report = solve_taxonomy(model, config)
    write_canonical_json(args.out, report)
    if args.pretty:
        write_pretty_json(args.out.with_suffix(".pretty.json"), report)
    print(f"wrote {args.out}")
    print(f"classes={len(report['classes'])}")
    print(
        "final_debt="
        + str(report["evidence_debt_trace"][-1]["new_cost"])
    )


def _command_verify(args: argparse.Namespace) -> None:
    model = load_model(args.model)
    config = load_config(args.config)
    report = load_json(args.report)
    verify_report(model, config, report)
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
