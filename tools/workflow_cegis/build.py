from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import write_canonical_json, write_pretty_json
from .engine import run_cegis
from .explore import ExpandedChannel, History, expand_channels, explore_histories
from .lean import render_bridge_lean, render_evidence_lean, render_workflow_lean
from .model import WorkflowModel, load_model


@dataclass(frozen=True)
class BuildResult:
    model: WorkflowModel
    histories: tuple[History, ...]
    channels: tuple[ExpandedChannel, ...]
    report: dict[str, Any]
    workflow_lean: str
    evidence_lean: str
    bridge_lean: str


def build(model_path: Path) -> BuildResult:
    model = load_model(model_path)
    histories = explore_histories(model)
    channels = expand_channels(model)
    report = run_cegis(model)
    return BuildResult(
        model=model,
        histories=histories,
        channels=channels,
        report=report,
        workflow_lean=render_workflow_lean(model, histories, channels),
        evidence_lean=render_evidence_lean(model, report, histories, channels),
        bridge_lean=render_bridge_lean(model, report, histories, channels),
    )


def write_result(
    result: BuildResult,
    *,
    report_path: Path,
    evidence_model_path: Path,
    synthesis_path: Path,
    repair_synthesis_path: Path,
    workflow_lean_path: Path,
    evidence_lean_path: Path,
    bridge_lean_path: Path,
    pretty: bool = False,
) -> None:
    write_canonical_json(report_path, result.report)
    write_canonical_json(evidence_model_path, result.report["evidence_model"])
    write_canonical_json(synthesis_path, result.report["exact_synthesis"])
    write_canonical_json(
        repair_synthesis_path, result.report["exact_repair_synthesis"]
    )
    if pretty:
        write_pretty_json(report_path.with_suffix(".pretty.json"), result.report)
        write_pretty_json(
            evidence_model_path.with_suffix(".pretty.json"),
            result.report["evidence_model"],
        )
        write_pretty_json(
            synthesis_path.with_suffix(".pretty.json"),
            result.report["exact_synthesis"],
        )
        write_pretty_json(
            repair_synthesis_path.with_suffix(".pretty.json"),
            result.report["exact_repair_synthesis"],
        )
    for path, source in (
        (workflow_lean_path, result.workflow_lean),
        (evidence_lean_path, result.evidence_lean),
        (bridge_lean_path, result.bridge_lean),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
