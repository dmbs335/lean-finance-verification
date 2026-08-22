from __future__ import annotations

from pathlib import Path

from tools.workflow_cegis.canonical import write_canonical_json, write_pretty_json

from .refine import RefinementResult, build_refinement


def build(model_path: Path, trace_path: Path) -> RefinementResult:
    return build_refinement(model_path, trace_path)


def write_result(
    result: RefinementResult,
    *,
    refined_model_path: Path,
    refinement_report_path: Path,
    workflow_report_path: Path,
    evidence_model_path: Path,
    synthesis_path: Path,
    repair_synthesis_path: Path,
    workflow_lean_path: Path,
    evidence_lean_path: Path,
    bridge_lean_path: Path,
    trace_lean_path: Path,
    pretty: bool = False,
) -> None:
    write_canonical_json(refined_model_path, result.refined_model_raw)
    write_canonical_json(refinement_report_path, result.report)
    write_canonical_json(workflow_report_path, result.workflow.report)
    write_canonical_json(
        evidence_model_path, result.workflow.report["evidence_model"]
    )
    write_canonical_json(
        synthesis_path, result.workflow.report["exact_synthesis"]
    )
    write_canonical_json(
        repair_synthesis_path,
        result.workflow.report["exact_repair_synthesis"],
    )
    if pretty:
        for path, payload in (
            (refined_model_path, result.refined_model_raw),
            (refinement_report_path, result.report),
            (workflow_report_path, result.workflow.report),
            (evidence_model_path, result.workflow.report["evidence_model"]),
            (synthesis_path, result.workflow.report["exact_synthesis"]),
            (
                repair_synthesis_path,
                result.workflow.report["exact_repair_synthesis"],
            ),
        ):
            write_pretty_json(path.with_suffix(".pretty.json"), payload)
    for path, source in (
        (workflow_lean_path, result.workflow.workflow_lean),
        (evidence_lean_path, result.workflow.evidence_lean),
        (bridge_lean_path, result.workflow.bridge_lean),
        (trace_lean_path, result.trace_lean),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
