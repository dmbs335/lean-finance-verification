from __future__ import annotations

import hashlib
from itertools import combinations
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import ARTIFACT_IDS, BINDINGS, Channel, Problem

REPORT_SCHEMA = "lfv-autonomous-pipeline-composition-report-v1"


def _worlds() -> list[dict[str, Any]]:
    matched = {binding: True for binding in BINDINGS}
    worlds = [{"id": "matched", "bindings": matched, "global_claim": True}]
    for binding in BINDINGS:
        values = dict(matched)
        values[binding] = False
        worlds.append({
            "id": f"broken:{binding}",
            "bindings": values,
            "global_claim": False,
        })
    worlds.append({
        "id": "allBindingsBroken",
        "bindings": {binding: False for binding in BINDINGS},
        "global_claim": False,
    })
    return worlds


def _observation(
    problem: Problem,
    channel: Channel,
    world: dict[str, Any],
) -> tuple[bool, ...]:
    if channel.kind == "local-summary":
        return tuple(
            problem.artifacts[artifact_id].local_valid
            for artifact_id in ARTIFACT_IDS
        )
    if channel.kind == "bridge":
        return tuple(world["bindings"][binding] for binding in channel.covers)
    return (world["global_claim"],)


def _edges(problem: Problem, worlds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for left, right in combinations(worlds, 2):
        if left["global_claim"] == right["global_claim"]:
            continue
        separators = [
            channel.id for channel in problem.channels
            if _observation(problem, channel, left)
            != _observation(problem, channel, right)
        ]
        if not separators:
            raise ValidationError(
                f"channel language cannot separate {left['id']}/{right['id']}"
            )
        edges.append({
            "left": left["id"],
            "right": right["id"],
            "separators": separators,
        })
    return edges


def _candidate(problem: Problem, mask: int, edges: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [
        channel.id for index, channel in enumerate(problem.channels)
        if mask & (1 << index)
    ]
    selected_set = set(selected)
    uncovered = next(
        (edge for edge in edges if selected_set.isdisjoint(edge["separators"])),
        None,
    )
    result: dict[str, Any] = {
        "mask": mask,
        "channels": selected,
        "cost": sum(problem.channel_by_id[channel].cost for channel in selected),
        "verifies": uncovered is None,
    }
    if uncovered is not None:
        result["uncovered"] = uncovered
    return result


def solve(problem: Problem) -> dict[str, Any]:
    worlds = _worlds()
    edges = _edges(problem, worlds)
    candidates = [
        _candidate(problem, mask, edges)
        for mask in range(1 << len(problem.channels))
    ]
    verifying = sorted(
        (candidate for candidate in candidates if candidate["verifies"]),
        key=lambda candidate: (
            candidate["cost"], len(candidate["channels"]), candidate["channels"]
        ),
    )
    if not verifying:
        raise ValidationError("no verifying autonomous-pipeline architecture")
    selected = verifying[0]
    lower_cost = sorted(
        (candidate for candidate in candidates if candidate["cost"] < selected["cost"]),
        key=lambda candidate: (
            candidate["cost"], len(candidate["channels"]), candidate["channels"]
        ),
    )
    if any(candidate["verifies"] for candidate in lower_cost):
        raise AssertionError("selected architecture is not minimum cost")
    local = next(channel for channel in problem.channels if channel.kind == "local-summary")
    global_bundle = next(channel for channel in problem.channels if channel.kind == "global-bundle")
    bridge_ids = [channel.id for channel in problem.channels if channel.kind == "bridge"]
    by_channels = {tuple(candidate["channels"]): candidate for candidate in candidates}
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "artifacts": [
            {
                "id": artifact_id,
                "sha256": problem.artifacts[artifact_id].sha256,
                "input_sha256": list(problem.artifacts[artifact_id].input_sha256),
                "local_valid": problem.artifacts[artifact_id].local_valid,
            }
            for artifact_id in ARTIFACT_IDS
        ],
        "binding_requirements": [
            {"id": binding, "left": left, "right": right}
            for binding, (left, right) in BINDINGS.items()
        ],
        "worlds": worlds,
        "disagreement_edges": edges,
        "candidate_count": len(candidates),
        "local_summary_only": by_channels[(local.id,)],
        "all_bridge_receipts": by_channels[tuple(bridge_ids)],
        "global_bundle_only": by_channels[(global_bundle.id,)],
        "synthesis": {
            "selected": selected,
            "optimal_sets": [
                candidate for candidate in verifying
                if candidate["cost"] == selected["cost"]
            ],
            "lower_cost_failures": lower_cost,
        },
        "controlled_claims": {
            "all_local_certificates_valid": all(
                artifact.local_valid for artifact in problem.artifacts.values()
            ),
            "local_summary_cannot_verify_global_pipeline": not by_channels[(local.id,)]["verifies"],
            "minimum_architecture_exact": True,
        },
        "residual_boundaries": [
            "local certificate semantics and artifact digests are controlled inputs",
            "binding receipts are not independently authenticated",
            "finite substitution worlds do not exhaust real attacks",
            "no autonomous trading or profitability claim",
        ],
    }
    report["report_sha256"] = hashlib.sha256(canonical_bytes(report)).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "autonomous-pipeline report does not match exact recomputation"
        )
    return expected
