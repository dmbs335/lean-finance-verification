from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import build, write_result
from .canonical import canonical_bytes, load_json
from .engine import verify_report
from .errors import CegisError, ValidationError
from .model import load_model


def _path(value: str) -> Path:
    return Path(value)


def _add_outputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--report", required=True, type=_path)
    parser.add_argument("--evidence-model", required=True, type=_path)
    parser.add_argument("--synthesis", required=True, type=_path)
    parser.add_argument("--repair-synthesis", required=True, type=_path)
    parser.add_argument("--workflow-lean", required=True, type=_path)
    parser.add_argument("--evidence-lean", required=True, type=_path)
    parser.add_argument("--bridge-lean", required=True, type=_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lfv-workflow-cegis",
        description=(
            "Generate bounded workflow histories, discover indistinguishable "
            "attacks, synthesize evidence refinements, and emit Lean witnesses"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    synth = subparsers.add_parser("synth", help="run the complete workflow CEGIS cycle")
    synth.add_argument("--model", required=True, type=_path)
    _add_outputs(synth)
    synth.add_argument("--pretty", action="store_true")
    verify = subparsers.add_parser("verify", help="recompute and verify a CEGIS report")
    verify.add_argument("--model", required=True, type=_path)
    verify.add_argument("--report", required=True, type=_path)
    check = subparsers.add_parser(
        "check-generated",
        help="fail when checked-in CEGIS artifacts or generated Lean drift",
    )
    check.add_argument("--model", required=True, type=_path)
    _add_outputs(check)
    return parser


def _command_synth(args: argparse.Namespace) -> None:
    result = build(args.model)
    write_result(
        result,
        report_path=args.report,
        evidence_model_path=args.evidence_model,
        synthesis_path=args.synthesis,
        repair_synthesis_path=args.repair_synthesis,
        workflow_lean_path=args.workflow_lean,
        evidence_lean_path=args.evidence_lean,
        bridge_lean_path=args.bridge_lean,
        pretty=args.pretty,
    )
    print(f"wrote {args.report}")
    print(f"histories={len(result.histories)} channels={len(result.channels)}")
    print("refined=" + ",".join(result.report["refined_selection"]))
    exact = result.report["exact_synthesis"]
    if exact["status"] == "synthesized":
        print(
            "optimal=" + ",".join(exact["selected"]["channels"])
            + f" cost={exact['selected']['weighted_cost']}"
        )
    else:
        witness = exact["impossibility_witness"]
        print(f"impossible={witness['left']}::{witness['right']}")


def _command_verify(args: argparse.Namespace) -> None:
    model = load_model(args.model)
    report = load_json(args.report)
    verify_report(model, report)
    print(f"verified {args.report}")


def _command_check(args: argparse.Namespace) -> None:
    result = build(args.model)
    expected_bytes = {
        args.report: canonical_bytes(result.report),
        args.evidence_model: canonical_bytes(result.report["evidence_model"]),
        args.synthesis: canonical_bytes(result.report["exact_synthesis"]),
        args.repair_synthesis: canonical_bytes(
            result.report["exact_repair_synthesis"]
        ),
    }
    for path, expected in expected_bytes.items():
        if path.read_bytes() != expected:
            raise ValidationError(f"generated JSON drift: regenerate {path}")
    expected_sources = {
        args.workflow_lean: result.workflow_lean,
        args.evidence_lean: result.evidence_lean,
        args.bridge_lean: result.bridge_lean,
    }
    for path, expected in expected_sources.items():
        if path.read_text(encoding="utf-8") != expected:
            raise ValidationError(f"generated Lean drift: regenerate {path}")
    print("generated workflow CEGIS artifacts are reproducible")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "synth":
            _command_synth(args)
        elif args.command == "verify":
            _command_verify(args)
        elif args.command == "check-generated":
            _command_check(args)
        else:
            parser.error(f"unknown command: {args.command}")
        return 0
    except (CegisError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
