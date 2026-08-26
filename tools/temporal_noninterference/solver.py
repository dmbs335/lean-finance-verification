from __future__ import annotations

import hashlib
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .engine import evaluate_once, run_trace
from .errors import ValidationError
from .model import Pipeline, Problem

REPORT_SCHEMA = "lfv-temporal-noninterference-report-v1"


def _observable(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "time": output["time"],
        "value": output["value"],
        "position": output["position"],
    }


def _differences(
    left: list[dict[str, Any]], right: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for before, after in zip(left, right, strict=True):
        if _observable(before) != _observable(after):
            result.append(
                {
                    "time": before["time"],
                    "left": _observable(before),
                    "right": _observable(after),
                }
            )
    return result


def _pipeline_result(problem: Problem, pipeline: Pipeline) -> dict[str, Any]:
    base = run_trace(problem.base_history, pipeline, problem.query_times)
    extended = run_trace(
        problem.extended_history, pipeline, problem.query_times
    )
    future_differences = _differences(base["outputs"], extended["outputs"])

    availability_differences: list[dict[str, Any]] = []
    for query in problem.query_times:
        full = evaluate_once(problem.extended_history, pipeline, query)
        projected_history = tuple(
            item
            for item in problem.extended_history
            if item.available_at <= query
        )
        projected = evaluate_once(projected_history, pipeline, query)
        if _observable(full) != _observable(projected):
            availability_differences.append(
                {
                    "time": query,
                    "full_history": _observable(full),
                    "available_prefix": _observable(projected),
                }
            )

    temporal_safe = not future_differences and not availability_differences
    source_immutable = not (
        base["source_mutated"] or extended["source_mutated"]
    )
    first_divergence = None
    candidates: list[dict[str, Any]] = []
    if future_differences:
        candidates.append(
            {
                "kind": "future_extension",
                **future_differences[0],
            }
        )
    if availability_differences:
        candidates.append(
            {
                "kind": "availability_projection",
                **availability_differences[0],
            }
        )
    if candidates:
        first_divergence = min(
            candidates, key=lambda item: (item["time"], item["kind"])
        )

    result: dict[str, Any] = {
        "pipeline": pipeline.id,
        "operation": pipeline.operation,
        "threshold": pipeline.threshold,
        "window": pipeline.window,
        "base_trace": base,
        "extended_trace": extended,
        "future_extension_differences": future_differences,
        "availability_projection_differences": availability_differences,
        "temporal_noninterference": temporal_safe,
        "source_immutable": source_immutable,
        "causal_and_pure": temporal_safe and source_immutable,
        "first_divergence": first_divergence,
    }
    if result["causal_and_pure"]:
        result["certificate"] = {
            "claim": "temporal-noninterference-and-source-immutability",
            "cutoff": problem.cutoff,
            "query_times": list(problem.query_times),
            "pipeline": pipeline.id,
        }
    else:
        result["certificate"] = None
    return result


def solve(problem: Problem) -> dict[str, Any]:
    pipelines = [
        _pipeline_result(problem, pipeline)
        for pipeline in problem.pipelines
    ]
    unsafe = [item for item in pipelines if not item["causal_and_pure"]]
    append_tail = next(
        (
            item for item in pipelines
            if item["operation"] == "append_tail_forward_fill"
        ),
        None,
    )
    if append_tail is None:
        raise ValidationError(
            "controlled benchmark requires append_tail_forward_fill"
        )
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "cutoff": problem.cutoff,
        "query_times": list(problem.query_times),
        "base_observation_count": len(problem.base_history),
        "extended_observation_count": len(problem.extended_history),
        "future_extension_count": (
            len(problem.extended_history) - len(problem.base_history)
        ),
        "pipelines": pipelines,
        "aggregate": {
            "pipeline_count": len(pipelines),
            "temporal_safe_count": sum(
                1 for item in pipelines
                if item["temporal_noninterference"]
            ),
            "source_immutable_count": sum(
                1 for item in pipelines if item["source_immutable"]
            ),
            "causal_and_pure_count": sum(
                1 for item in pipelines if item["causal_and_pure"]
            ),
            "unsafe_pipeline_count": len(unsafe),
        },
        "gs_quant_generic_data_source_regression": {
            "public_issue": "goldmansachs/gs-quant#375",
            "modeled_operation": append_tail["operation"],
            "first_divergence": append_tail["first_divergence"],
            "source_mutated": not append_tail["source_immutable"],
            "interpretation": (
                "a missing date appended after a complete date-indexed series "
                "can inherit the end-of-series value and reverse a past decision"
            ),
        },
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "temporal-noninterference report does not match exact recomputation"
        )
    return expected
