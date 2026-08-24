from __future__ import annotations

import hashlib
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Problem

REPORT_SCHEMA = "lfv-certifiable-alpha-interval-report-v1"


def _candidate(problem: Problem, mask: int) -> dict[str, Any]:
    selected = tuple(
        channel.id for index, channel in enumerate(problem.channels)
        if mask & (1 << index)
    )
    selected_set = set(selected)
    detected: set[str] = set()
    cost = 0
    for channel in problem.channels:
        if channel.id in selected_set:
            cost += channel.cost
            detected.update(channel.detects)
    unresolved = [
        distortion for distortion in problem.distortions
        if distortion.kind not in detected
    ]
    unresolved_inflation = sum(
        distortion.maximum_upward_inflation_bps for distortion in unresolved
    )
    model_lower = min(model.lower_bps for model in problem.models)
    model_upper = max(model.upper_bps for model in problem.models)
    lower = (
        model_lower
        - unresolved_inflation
        - problem.deployment_costs.maximum_bps
    )
    upper = model_upper - problem.deployment_costs.minimum_bps
    width = upper - lower
    return {
        "mask": mask,
        "channels": list(selected),
        "cost": cost,
        "detected_distortions": sorted(detected),
        "unresolved_distortions": [
            {
                "kind": distortion.kind,
                "maximum_upward_inflation_bps": (
                    distortion.maximum_upward_inflation_bps
                ),
            }
            for distortion in unresolved
        ],
        "unresolved_inflation_bps": unresolved_inflation,
        "interval_bps": [lower, upper],
        "interval_width_bps": width,
        "meets_target": width <= problem.target_maximum_width_bps,
    }


def solve(problem: Problem) -> dict[str, Any]:
    model_lower = min(model.lower_bps for model in problem.models)
    model_upper = max(model.upper_bps for model in problem.models)
    candidates = [
        _candidate(problem, mask)
        for mask in range(1 << len(problem.channels))
    ]
    feasible = sorted(
        (candidate for candidate in candidates if candidate["meets_target"]),
        key=lambda candidate: (
            candidate["cost"], len(candidate["channels"]), candidate["channels"]
        ),
    )
    if not feasible:
        raise ValidationError(
            "no evidence selection meets the target certifiable interval width"
        )
    selected = feasible[0]
    no_evidence = candidates[0]
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "model_envelope_bps": [model_lower, model_upper],
        "model_intervals": [
            {"model": model.id, "interval_bps": [model.lower_bps, model.upper_bps]}
            for model in problem.models
        ],
        "deployment_costs_bps": {
            "minimum": problem.deployment_costs.minimum_bps,
            "maximum": problem.deployment_costs.maximum_bps,
        },
        "target_maximum_width_bps": problem.target_maximum_width_bps,
        "candidate_count": len(candidates),
        "no_evidence": no_evidence,
        "selected": selected,
        "optimal_sets": [
            candidate for candidate in feasible
            if candidate["cost"] == selected["cost"]
        ],
        "lower_cost_failures": [
            candidate for candidate in candidates
            if candidate["cost"] < selected["cost"]
        ],
        "attack_uncertainty_removed_bps": (
            no_evidence["unresolved_inflation_bps"]
            - selected["unresolved_inflation_bps"]
        ),
        "residual_width_after_declared_attack_remediation_bps": (
            selected["interval_width_bps"]
        ),
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "certifiable-alpha interval report does not match exact recomputation"
        )
    return expected
