from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.workflow_cegis.canonical import canonical_bytes, load_json

from .build import build, write_result
from .errors import TraceRefinementError, ValidationError
from .refine import verify_refinement_report


def _path(value: str) -> Path:
    return Path(value)


def _add_outputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--refined-model", required=True, type=_path)
    parser.add_argument("--refinement-report", required=True, type=_path)
    parser.add_argument("--workflow-report", required=True, type=_path)
    parser.add_argument("--evidence-model", required=True, type=_path)
    parser.add_argument("--synthesis", required=True, type=_path)
    parser.add_argument("--repair-synthesis", required=True, type=_path)
    parser.add_argument("--workflow-lean", required=True, type=_path)
    parser.add_argument("--evidence-lean", required=True, type=_path)
    parser.add_argument("--bridge-lean", required=True, type=_path)
    parser.add_argument("--trace-lean", required=True, type=_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lfv-trace-refinement",
        description=(
            "Ingest an observed attack trace, synthesize missing finite-workflow "
            "action semantics, and rerun proof-carrying evidence synthesis"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    refine = subparsers.add_parser(
        "refine", help="refine a workflow model and emit all synthesis artifacts"
    )
    refine.add_argument("--model", required=True, type=_path)
    refine.add_argument("--trace", required=True, type=_path)
    _add_outputs(refine)
    refine.add_argument("--pretty", action="store_true")

    verify = subparsers.add_parser(
        "verify", help="recompute and verify one refinement report"
    )
    verify.add_argument("--model", required=True, type=_path)
    verify.add_argument("--trace", required=True, type=_path)
    verify.add_argument("--report", required=True, type=_path)

    check = subparsers.add_parser(
        "check-generated",
        help="fail when checked-in refined models, reports, or Lean files drift",
    )
    check.add_argument("--model", required=True, type=_path)
    check.add_argument("--trace", required=True, type=_path)
    _add_outputs(check)
    return parser


def _command_refine(args: argparse.Namespace) -> None:
    result = build(args.model, args.trace)
    write_result(
        result,
        refined_model_path=args.refined_model,
        refinement_report_path=args.refinement_report,
        workflow_report_path=args.workflow_report,
        evidence_model_path=args.evidence_model,
        synthesis_path=args.synthesis,
        repair_synthesis_path=args.repair_synthesis,
        workflow_lean_path=args.workflow_lean,
        evidence_lean_path=args.evidence_lean,
        bridge_lean_path=args.bridge_lean,
        trace_lean_path=args.trace_lean,
        pretty=args.pretty,
    )
    print(f"wrote {args.refined_model}")
    print(f"wrote {args.refinement_report}")
    print(
        "added_actions="
        + ",".join(
            iteration["event"]
            for iteration in result.report["refinement_iterations"]
        )
    )
    print(
        "separator_basis="
        + ",".join(
            result.report["separator_analysis"]["separator_basis"]
        )
    )


def _command_verify(args: argparse.Namespace) -> None:
    verify_refinement_report(
        args.model,
        args.trace,
        load_json(args.report),
    )
    print(f"verified {args.report}")


def _command_check(args: argparse.Namespace) -> None:
    result = build(args.model, args.trace)
    expected_json = {
        args.refined_model: result.refined_model_raw,
        args.refinement_report: result.report,
        args.workflow_report: result.workflow.report,
        args.evidence_model: result.workflow.report["evidence_model"],
        args.synthesis: result.workflow.report["exact_synthesis"],
        args.repair_synthesis: result.workflow.report[
            "exact_repair_synthesis"
        ],
    }
    for path, payload in expected_json.items():
        if path.read_bytes() != canonical_bytes(payload):
            raise ValidationError(f"generated JSON drift: regenerate {path}")
    expected_lean = {
        args.workflow_lean: result.workflow.workflow_lean,
        args.evidence_lean: result.workflow.evidence_lean,
        args.bridge_lean: result.workflow.bridge_lean,
        args.trace_lean: result.trace_lean,
    }
    for path, source in expected_lean.items():
        if path.read_text(encoding="utf-8") != source:
            raise ValidationError(f"generated Lean drift: regenerate {path}")
    print("generated attack-trace refinement artifacts are reproducible")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "refine":
            _command_refine(args)
        elif args.command == "verify":
            _command_verify(args)
        elif args.command == "check-generated":
            _command_check(args)
        else:
            parser.error(f"unknown command: {args.command}")
        return 0
    except (TraceRefinementError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
