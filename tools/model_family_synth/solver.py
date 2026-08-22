from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import FamilyProblem

REPORT_SCHEMA = "lfv-model-family-evidence-report-v1"


@dataclass(frozen=True)
class Edge:
    left: str
    right: str
    separators: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "left": self.left,
            "right": self.right,
            "separators": list(self.separators),
        }


def _edges(problem: FamilyProblem, worlds) -> tuple[Edge, ...]:
    result: list[Edge] = []
    for left, right in combinations(worlds, 2):
        if left.claim == right.claim:
            continue
        separators = tuple(
            channel.id for channel in problem.channels
            if problem.observation_key(channel.id, left.id)
            != problem.observation_key(channel.id, right.id)
        )
        result.append(Edge(left.id, right.id, separators))
    return tuple(result)


def _candidate(problem: FamilyProblem, edges: tuple[Edge, ...], mask: int) -> dict[str, Any]:
    selected = tuple(
        channel.id for index, channel in enumerate(problem.channels)
        if mask & (1 << index)
    )
    selected_set = set(selected)
    uncovered = next(
        (edge for edge in edges if selected_set.isdisjoint(edge.separators)), None
    )
    cost = sum(
        channel.cost for channel in problem.channels if channel.id in selected_set
    )
    result: dict[str, Any] = {
        "mask": mask,
        "channels": list(selected),
        "cost": cost,
        "verifies": uncovered is None,
    }
    if uncovered is not None:
        result["uncovered"] = uncovered.as_dict()
    return result


def _optimum(problem: FamilyProblem, worlds) -> dict[str, Any]:
    edges = _edges(problem, worlds)
    impossible = next((edge for edge in edges if not edge.separators), None)
    candidates = tuple(
        _candidate(problem, edges, mask)
        for mask in range(1 << len(problem.channels))
    )
    if impossible is not None:
        return {
            "status": "impossible",
            "edges": [edge.as_dict() for edge in edges],
            "witness": impossible.as_dict(),
            "candidate_count": len(candidates),
        }
    verifying = sorted(
        (candidate for candidate in candidates if candidate["verifies"]),
        key=lambda candidate: (
            candidate["cost"], len(candidate["channels"]), candidate["channels"]
        ),
    )
    if not verifying:
        raise ValidationError("no verifying family candidate")
    selected = verifying[0]
    return {
        "status": "synthesized",
        "edges": [edge.as_dict() for edge in edges],
        "candidate_count": len(candidates),
        "selected": selected,
        "optimal_sets": [
            candidate for candidate in verifying
            if candidate["cost"] == selected["cost"]
        ],
        "lower_cost_failures": [
            candidate for candidate in candidates
            if candidate["cost"] < selected["cost"]
        ],
    }


def solve(problem: FamilyProblem) -> dict[str, Any]:
    point_worlds = tuple(
        world for world in problem.allowed_worlds
        if world.model == problem.chosen_model
    )
    if not point_worlds:
        raise ValidationError("chosen model has no admissible worlds")
    point = _optimum(problem, point_worlds)
    family = _optimum(problem, problem.allowed_worlds)
    if point["status"] != "synthesized" or family["status"] != "synthesized":
        gap = None
    else:
        gap = family["selected"]["cost"] - point["selected"]["cost"]
    report = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "chosen_model": problem.chosen_model,
        "consistent_models": [
            model.id for model in problem.models if model.consistent
        ],
        "allowed_worlds": [world.id for world in problem.allowed_worlds],
        "point_optimum": point,
        "family_optimum": family,
        "underestimation_gap": gap,
        "cross_model_disagreement_edges": [
            edge for edge in family["edges"]
            if problem.world_by_id[edge["left"]].model
            != problem.world_by_id[edge["right"]].model
        ],
    }
    report["report_sha256"] = __import__("hashlib").sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: FamilyProblem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "model-family synthesis report does not match exact recomputation"
        )
    return expected
