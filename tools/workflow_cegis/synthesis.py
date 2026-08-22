from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

from .canonical import CANONICAL_FORMAT, document_digest
from .errors import ValidationError
from .explore import ExpandedChannel, History, observation_key
from .model import CostVector, WorkflowModel, ZERO_COST

SYNTHESIS_SCHEMA = "lfv-workflow-evidence-synthesis-v1"
SYNTHESIS_DIGEST_SCHEMA = "lfv-workflow-evidence-synthesis-digest-v1"


@dataclass(frozen=True)
class Edge:
    id: str
    left: str
    right: str
    separators: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "left": self.left,
            "right": self.right,
            "separators": list(self.separators),
        }


@dataclass(frozen=True)
class Candidate:
    mask: int
    channels: tuple[str, ...]
    cost: CostVector
    weighted_cost: int
    verifies: bool
    uncovered_edge: str | None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "mask": self.mask,
            "channels": list(self.channels),
            "cost": self.cost.as_dict(),
            "weighted_cost": self.weighted_cost,
            "verifies": self.verifies,
        }
        if self.uncovered_edge is not None:
            result["uncovered_edge"] = self.uncovered_edge
        return result


def build_edges(
    histories: tuple[History, ...], channels: tuple[ExpandedChannel, ...]
) -> tuple[Edge, ...]:
    edges: list[Edge] = []
    for left, right in combinations(histories, 2):
        if left.claim == right.claim:
            continue
        separators = tuple(
            channel.id
            for channel in channels
            if observation_key(channel, left) != observation_key(channel, right)
        )
        edges.append(
            Edge(
                id=f"edge{len(edges)}",
                left=left.id,
                right=right.id,
                separators=separators,
            )
        )
    if not edges:
        raise ValidationError("generated histories contain no claim-disagreement edge")
    return tuple(edges)


def _selection(channels: tuple[ExpandedChannel, ...], mask: int) -> tuple[str, ...]:
    return tuple(
        channel.id
        for index, channel in enumerate(channels)
        if mask & (1 << index)
    )


def _cost(
    model: WorkflowModel,
    channels: tuple[ExpandedChannel, ...],
    selected: tuple[str, ...],
) -> CostVector:
    by_id = {channel.id: channel for channel in channels}
    total = ZERO_COST
    for channel_id in selected:
        total = total + by_id[channel_id].cost
    return total


def evaluate_candidates(
    model: WorkflowModel,
    channels: tuple[ExpandedChannel, ...],
    edges: tuple[Edge, ...],
) -> tuple[Candidate, ...]:
    evaluations: list[Candidate] = []
    for mask in range(1 << len(channels)):
        selected = _selection(channels, mask)
        selected_set = set(selected)
        uncovered = next(
            (edge.id for edge in edges if selected_set.isdisjoint(edge.separators)),
            None,
        )
        cost = _cost(model, channels, selected)
        evaluations.append(
            Candidate(
                mask=mask,
                channels=selected,
                cost=cost,
                weighted_cost=cost.weighted(model.cost_weights),
                verifies=uncovered is None,
                uncovered_edge=uncovered,
            )
        )
    return tuple(evaluations)


def _proper_subset(left: int, right: int) -> bool:
    return left != right and (left & right) == left


def _dominates(left: CostVector, right: CostVector) -> bool:
    left_values = (left.operational, left.privacy, left.trust)
    right_values = (right.operational, right.privacy, right.trust)
    return all(a <= b for a, b in zip(left_values, right_values)) and any(
        a < b for a, b in zip(left_values, right_values)
    )


def _sort_key(candidate: Candidate) -> tuple[Any, ...]:
    return (
        candidate.weighted_cost,
        len(candidate.channels),
        candidate.channels,
        candidate.mask,
    )


def exact_synthesis(
    model: WorkflowModel,
    histories: tuple[History, ...],
    channels: tuple[ExpandedChannel, ...],
) -> dict[str, Any]:
    edges = build_edges(histories, channels)
    evaluations = evaluate_candidates(model, channels, edges)
    impossible = [edge for edge in edges if not edge.separators]
    core: dict[str, Any] = {
        "schema_version": SYNTHESIS_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "history_count": len(histories),
        "channel_count": len(channels),
        "candidate_count": len(evaluations),
        "disagreement_edges": [edge.as_dict() for edge in edges],
        "verifying_candidate_count": sum(
            1 for candidate in evaluations if candidate.verifies
        ),
    }
    if impossible:
        core.update(
            {
                "status": "impossible",
                "impossibility_witness": impossible[0].as_dict(),
                "all_channels_mask": (1 << len(channels)) - 1,
            }
        )
    else:
        verifying = sorted(
            (candidate for candidate in evaluations if candidate.verifies),
            key=_sort_key,
        )
        selected = verifying[0]
        minimal = [
            candidate
            for candidate in verifying
            if not any(
                other.verifies and _proper_subset(other.mask, candidate.mask)
                for other in evaluations
            )
        ]
        pareto = [
            candidate
            for candidate in verifying
            if not any(
                other.mask != candidate.mask
                and _dominates(other.cost, candidate.cost)
                for other in verifying
            )
        ]
        lower = [
            candidate
            for candidate in evaluations
            if candidate.weighted_cost < selected.weighted_cost
        ]
        if any(candidate.verifies for candidate in lower):
            raise AssertionError("exact enumeration selected a nonoptimal candidate")
        core.update(
            {
                "status": "synthesized",
                "selected": selected.as_dict(),
                "optimal_weighted_cost": selected.weighted_cost,
                "optimal_sets": [
                    candidate.as_dict()
                    for candidate in verifying
                    if candidate.weighted_cost == selected.weighted_cost
                ],
                "minimal_verifying_sets": [
                    candidate.as_dict() for candidate in sorted(minimal, key=_sort_key)
                ],
                "pareto_frontier": [
                    candidate.as_dict() for candidate in sorted(pareto, key=_sort_key)
                ],
                "lower_cost_failures": [
                    candidate.as_dict() for candidate in sorted(lower, key=_sort_key)
                ],
            }
        )
    result = dict(core)
    result["synthesis_digest"] = document_digest(
        "workflowEvidenceSynthesis", SYNTHESIS_DIGEST_SCHEMA, core
    )
    return result
