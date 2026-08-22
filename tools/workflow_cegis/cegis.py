from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import CANONICAL_FORMAT, document_digest
from .errors import ValidationError
from .explore import ExpandedChannel, History, observation_key
from .model import CostVector, WorkflowModel, ZERO_COST
from .synthesis import Edge, build_edges, exact_synthesis

CEGIS_SCHEMA = "lfv-workflow-evidence-cegis-v1"
CEGIS_DIGEST_SCHEMA = "lfv-workflow-evidence-cegis-digest-v1"
REPAIR_SCHEMA = "lfv-workflow-evidence-repair-synthesis-v1"
REPAIR_DIGEST_SCHEMA = "lfv-workflow-evidence-repair-synthesis-digest-v1"


@dataclass(frozen=True)
class RepairCandidate:
    mask: int
    optional_channels: tuple[str, ...]
    selected_channels: tuple[str, ...]
    incremental_cost: CostVector
    incremental_weighted_cost: int
    total_cost: CostVector
    total_weighted_cost: int
    verifies: bool
    uncovered_edge: str | None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "mask": self.mask,
            "optional_channels": list(self.optional_channels),
            "selected_channels": list(self.selected_channels),
            "incremental_cost": self.incremental_cost.as_dict(),
            "incremental_weighted_cost": self.incremental_weighted_cost,
            "total_cost": self.total_cost.as_dict(),
            "total_weighted_cost": self.total_weighted_cost,
            "verifies": self.verifies,
        }
        if self.uncovered_edge is not None:
            result["uncovered_edge"] = self.uncovered_edge
        return result


def _cost(
    model: WorkflowModel,
    by_id: dict[str, ExpandedChannel],
    selected: tuple[str, ...],
) -> CostVector:
    total = ZERO_COST
    for channel_id in selected:
        total = total + by_id[channel_id].cost
    return total


def _proper_subset(left_mask: int, right_mask: int) -> bool:
    return left_mask != right_mask and (left_mask & right_mask) == left_mask


def _dominates(left: CostVector, right: CostVector) -> bool:
    left_values = (left.operational, left.privacy, left.trust)
    right_values = (right.operational, right.privacy, right.trust)
    return all(a <= b for a, b in zip(left_values, right_values)) and any(
        a < b for a, b in zip(left_values, right_values)
    )


def _sort_key(candidate: RepairCandidate) -> tuple[Any, ...]:
    return (
        candidate.incremental_weighted_cost,
        len(candidate.optional_channels),
        candidate.optional_channels,
        candidate.mask,
    )


def evaluate_repairs(
    model: WorkflowModel,
    channels: tuple[ExpandedChannel, ...],
    edges: tuple[Edge, ...],
) -> tuple[RepairCandidate, ...]:
    mandatory = tuple(channel.id for channel in channels if channel.deployed)
    optional = tuple(channel.id for channel in channels if not channel.deployed)
    by_id = {channel.id: channel for channel in channels}
    mandatory_cost = _cost(model, by_id, mandatory)
    evaluations: list[RepairCandidate] = []
    for mask in range(1 << len(optional)):
        optional_selected = tuple(
            channel_id
            for index, channel_id in enumerate(optional)
            if mask & (1 << index)
        )
        selected = mandatory + optional_selected
        selected_set = set(selected)
        uncovered = next(
            (edge.id for edge in edges if selected_set.isdisjoint(edge.separators)),
            None,
        )
        incremental = _cost(model, by_id, optional_selected)
        total = mandatory_cost + incremental
        evaluations.append(
            RepairCandidate(
                mask=mask,
                optional_channels=optional_selected,
                selected_channels=selected,
                incremental_cost=incremental,
                incremental_weighted_cost=incremental.weighted(model.cost_weights),
                total_cost=total,
                total_weighted_cost=total.weighted(model.cost_weights),
                verifies=uncovered is None,
                uncovered_edge=uncovered,
            )
        )
    return tuple(evaluations)


def exact_repair_synthesis(
    model: WorkflowModel,
    histories: tuple[History, ...],
    channels: tuple[ExpandedChannel, ...],
) -> dict[str, Any]:
    edges = build_edges(histories, channels)
    evaluations = evaluate_repairs(model, channels, edges)
    mandatory = [channel.id for channel in channels if channel.deployed]
    optional = [channel.id for channel in channels if not channel.deployed]
    impossible = [edge for edge in edges if not edge.separators]
    core: dict[str, Any] = {
        "schema_version": REPAIR_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "mandatory_channels": mandatory,
        "optional_channels": optional,
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
                "all_optional_mask": (1 << len(optional)) - 1,
            }
        )
    else:
        verifying = sorted(
            (candidate for candidate in evaluations if candidate.verifies),
            key=_sort_key,
        )
        if not verifying:
            raise AssertionError("declared separator edges should admit all channels")
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
                and _dominates(other.incremental_cost, candidate.incremental_cost)
                for other in verifying
            )
        ]
        lower = [
            candidate
            for candidate in evaluations
            if candidate.incremental_weighted_cost < selected.incremental_weighted_cost
        ]
        if any(candidate.verifies for candidate in lower):
            raise AssertionError("exact repair selected a nonoptimal candidate")
        core.update(
            {
                "status": "synthesized",
                "selected": selected.as_dict(),
                "optimal_incremental_weighted_cost": selected.incremental_weighted_cost,
                "optimal_repairs": [
                    candidate.as_dict()
                    for candidate in verifying
                    if candidate.incremental_weighted_cost
                    == selected.incremental_weighted_cost
                ],
                "minimal_repairs": [
                    candidate.as_dict()
                    for candidate in sorted(minimal, key=_sort_key)
                ],
                "pareto_frontier": [
                    candidate.as_dict()
                    for candidate in sorted(pareto, key=_sort_key)
                ],
                "lower_cost_failures": [
                    candidate.as_dict()
                    for candidate in sorted(lower, key=_sort_key)
                ],
            }
        )
    result = dict(core)
    result["repair_digest"] = document_digest(
        "workflowEvidenceRepairSynthesis", REPAIR_DIGEST_SCHEMA, core
    )
    return result


def _best_for_discovered_edges(
    model: WorkflowModel,
    channels: tuple[ExpandedChannel, ...],
    discovered_edges: tuple[Edge, ...],
) -> RepairCandidate:
    candidates = evaluate_repairs(model, channels, discovered_edges)
    verifying = sorted(
        (candidate for candidate in candidates if candidate.verifies),
        key=_sort_key,
    )
    if not verifying:
        raise ValidationError(
            "discovered evidence constraints cannot be satisfied by the candidate language"
        )
    return verifying[0]


def _edge_sort_key(edge: Edge) -> tuple[int, str, str, str]:
    pair = sorted((edge.left, edge.right))
    return (len(edge.separators), pair[0], pair[1], edge.id)


def _find_uncovered_edge(
    edges: tuple[Edge, ...], selected: tuple[str, ...]
) -> Edge | None:
    selected_set = set(selected)
    uncovered = [
        edge for edge in edges if selected_set.isdisjoint(edge.separators)
    ]
    return min(uncovered, key=_edge_sort_key) if uncovered else None


def _primitive_suggestions(
    model: WorkflowModel,
    histories: tuple[History, ...],
    edge: Edge,
) -> list[dict[str, Any]]:
    by_id = {history.id: history for history in histories}
    left = by_id[edge.left]
    right = by_id[edge.right]
    suggestions: list[dict[str, Any]] = []
    for action in model.actions:
        left_projection = [item for item in left.trace if item == action.id]
        right_projection = [item for item in right.trace if item == action.id]
        if left_projection != right_projection:
            suggestions.append(
                {
                    "kind": "action_receipt",
                    "target": action.id,
                    "reason": "the action occurrence projection differs",
                }
            )
    for variable in model.variables:
        if left.final_state[variable.id] != right.final_state[variable.id]:
            suggestions.append(
                {
                    "kind": "state_attestation",
                    "target": variable.id,
                    "reason": "the terminal state bit differs",
                }
            )
    return suggestions


def _proposal_list(
    edge: Edge,
    channels: tuple[ExpandedChannel, ...],
    current: tuple[str, ...],
    model: WorkflowModel,
) -> list[dict[str, Any]]:
    current_set = set(current)
    by_id = {channel.id: channel for channel in channels}
    proposals = [
        by_id[channel_id]
        for channel_id in edge.separators
        if channel_id not in current_set
    ]
    proposals.sort(
        key=lambda channel: (
            channel.weighted_cost(model.cost_weights),
            channel.id,
        )
    )
    return [channel.as_dict(model.cost_weights) for channel in proposals]


def run_cegis(
    model: WorkflowModel,
    histories: tuple[History, ...],
    channels: tuple[ExpandedChannel, ...],
) -> dict[str, Any]:
    edges = build_edges(histories, channels)
    exact_global = exact_synthesis(model, histories, channels)
    exact_repair = exact_repair_synthesis(model, histories, channels)
    discovered: list[Edge] = []
    rounds: list[dict[str, Any]] = []
    status = "synthesized"
    unresolved_gap: dict[str, Any] | None = None

    for iteration in range(model.max_refinements + 1):
        candidate = _best_for_discovered_edges(
            model, channels, tuple(discovered)
        )
        uncovered = _find_uncovered_edge(edges, candidate.selected_channels)
        if uncovered is None:
            rounds.append(
                {
                    "iteration": iteration,
                    "status": "verified",
                    "candidate": candidate.as_dict(),
                    "discovered_edges": [edge.id for edge in discovered],
                }
            )
            break
        proposals = _proposal_list(
            uncovered, channels, candidate.selected_channels, model
        )
        if iteration >= model.max_refinements or not proposals:
            status = "unresolved"
            unresolved_gap = {
                "counterexample": uncovered.as_dict(),
                "available_channel_proposals": proposals,
                "primitive_sensor_suggestions": _primitive_suggestions(
                    model, histories, uncovered
                ),
                "reason": (
                    "refinement budget exhausted"
                    if iteration >= model.max_refinements
                    else "candidate channel language contains no separator"
                ),
            }
            rounds.append(
                {
                    "iteration": iteration,
                    "status": "unresolved",
                    "candidate": candidate.as_dict(),
                    "counterexample": uncovered.as_dict(),
                    "available_channel_proposals": proposals,
                    "discovered_edges": [edge.id for edge in discovered],
                }
            )
            break
        discovered.append(uncovered)
        after = _best_for_discovered_edges(model, channels, tuple(discovered))
        newly_added = [
            channel_id
            for channel_id in after.selected_channels
            if channel_id not in set(candidate.selected_channels)
        ]
        rounds.append(
            {
                "iteration": iteration,
                "status": "counterexample",
                "candidate": candidate.as_dict(),
                "counterexample": uncovered.as_dict(),
                "available_channel_proposals": proposals,
                "after_candidate": after.as_dict(),
                "newly_added_channels": newly_added,
                "discovered_edges": [edge.id for edge in discovered],
            }
        )
    else:
        raise AssertionError("bounded refinement loop must terminate")

    if status == "synthesized":
        final_selection = rounds[-1]["candidate"]
        if exact_repair["status"] != "synthesized":
            raise AssertionError("CEGIS verified despite impossible exact repair")
        if final_selection["mask"] != exact_repair["selected"]["mask"]:
            raise AssertionError(
                "counterexample-guided master did not converge to exact repair optimum"
            )
        newly_required = exact_repair["selected"]["optional_channels"]
    else:
        final_selection = rounds[-1]["candidate"]
        newly_required = final_selection["optional_channels"]

    core: dict[str, Any] = {
        "schema_version": CEGIS_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "status": status,
        "rounds": rounds,
        "final_selection": final_selection,
        "newly_required_channels": newly_required,
        "exact_global_synthesis": exact_global,
        "exact_repair_synthesis": exact_repair,
    }
    if unresolved_gap is not None:
        core["unresolved_gap"] = unresolved_gap
    result = dict(core)
    result["cegis_digest"] = document_digest(
        "workflowEvidenceCEGIS", CEGIS_DIGEST_SCHEMA, core
    )
    return result
