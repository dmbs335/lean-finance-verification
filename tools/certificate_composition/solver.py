from __future__ import annotations

import hashlib
from itertools import combinations
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Problem, World

REPORT_SCHEMA = "lfv-certificate-composition-report-v1"


def _disagreement_edges(problem: Problem) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for left, right in combinations(problem.worlds, 2):
        if left.global_claim == right.global_claim:
            continue
        separators = [
            channel.id
            for channel in problem.channels
            if problem.observation(left, channel.id)
            != problem.observation(right, channel.id)
        ]
        if not separators:
            raise ValidationError(
                "current channel language cannot separate global claim "
                f"disagreement {left.id}/{right.id}"
            )
        edges.append(
            {
                "left": left.id,
                "right": right.id,
                "left_claim": left.global_claim,
                "right_claim": right.global_claim,
                "separators": separators,
            }
        )
    if not edges:
        raise ValidationError("problem has no global claim-disagreement edges")
    return edges


def _candidate(
    problem: Problem,
    mask: int,
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = [
        channel.id
        for index, channel in enumerate(problem.channels)
        if mask & (1 << index)
    ]
    selected_set = set(selected)
    uncovered = next(
        (
            edge
            for edge in edges
            if selected_set.isdisjoint(edge["separators"])
        ),
        None,
    )
    candidate: dict[str, Any] = {
        "mask": mask,
        "channels": selected,
        "cost": sum(
            problem.channel_by_id[channel_id].cost
            for channel_id in selected
        ),
        "verifies": uncovered is None,
    }
    if uncovered is not None:
        candidate["uncovered"] = {
            "left": uncovered["left"],
            "right": uncovered["right"],
            "separators": uncovered["separators"],
        }
    return candidate


def _candidate_by_channels(
    candidates: list[dict[str, Any]],
    channels: list[str],
) -> dict[str, Any]:
    return next(
        candidate
        for candidate in candidates
        if candidate["channels"] == channels
    )


def solve(problem: Problem) -> dict[str, Any]:
    edges = _disagreement_edges(problem)
    candidates = [
        _candidate(problem, mask, edges)
        for mask in range(1 << len(problem.channels))
    ]
    verifying = sorted(
        (candidate for candidate in candidates if candidate["verifies"]),
        key=lambda candidate: (
            candidate["cost"],
            len(candidate["channels"]),
            candidate["channels"],
        ),
    )
    if not verifying:
        raise ValidationError("no selected channel set verifies the global claim")
    selected = verifying[0]
    binding_channels = [binding.channel_id for binding in problem.bindings]
    local_summary_only = _candidate_by_channels(
        candidates, [problem.local_summary_channel.id]
    )
    bridge_receipts_only = _candidate_by_channels(
        candidates, binding_channels
    )
    global_bundle_only = _candidate_by_channels(
        candidates, [problem.global_bundle_channel.id]
    )
    lower_cost_failures = sorted(
        (
            candidate
            for candidate in candidates
            if candidate["cost"] < selected["cost"]
        ),
        key=lambda candidate: (
            candidate["cost"],
            len(candidate["channels"]),
            candidate["channels"],
        ),
    )
    if any(candidate["verifies"] for candidate in lower_cost_failures):
        raise AssertionError("selected architecture is not minimum cost")

    local_observations = {
        tuple(
            world.local_claims[component.id]
            for component in problem.components
        )
        for world in problem.worlds
    }
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "component_count": len(problem.components),
        "binding_count": len(problem.bindings),
        "world_count": len(problem.worlds),
        "channel_count": len(problem.channels),
        "candidate_count": len(candidates),
        "components": [component.id for component in problem.components],
        "bindings": [
            {
                "id": binding.id,
                "left": binding.left,
                "right": binding.right,
                "channel_id": binding.channel_id,
                "cost": binding.cost,
            }
            for binding in problem.bindings
        ],
        "local_certificates_all_valid_across_worlds": all(
            all(world.local_claims.values())
            for world in problem.worlds
        ),
        "local_summary_constant_across_worlds": len(local_observations) == 1,
        "disagreement_edges": edges,
        "local_summary_only": local_summary_only,
        "bridge_receipts_only": bridge_receipts_only,
        "global_bundle_only": global_bundle_only,
        "synthesis": {
            "selected": selected,
            "optimal_sets": [
                candidate
                for candidate in verifying
                if candidate["cost"] == selected["cost"]
            ],
            "lower_cost_failures": lower_cost_failures,
        },
        "interpretation": {
            "local_passes": (
                "every local certificate is valid in every world, so local "
                "pass/fail summaries cannot establish cross-object identity"
            ),
            "bridge_obligation": (
                "the global pipeline claim requires evidence that binds the "
                "dataset to the decision and the decision to the result"
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
            "certificate-composition report does not match exact recomputation"
        )
    return expected
