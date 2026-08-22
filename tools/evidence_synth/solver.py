from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

from .canonical import CANONICAL_FORMAT, document_digest
from .errors import ValidationError
from .model import CostVector, EvidenceModel, ZERO_COST

CERTIFICATE_SCHEMA = "lfv-evidence-synthesis-certificate-v1"
MODEL_DIGEST_SCHEMA = "lfv-evidence-synthesis-model-digest-v1"
CERTIFICATE_DIGEST_SCHEMA = "lfv-evidence-synthesis-certificate-digest-v1"


@dataclass(frozen=True)
class DisagreementEdge:
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
class CandidateEvaluation:
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


def normalized_model(model: EvidenceModel) -> dict[str, Any]:
    return {
        "schema_version": "lfv-evidence-synthesis-model-v1",
        "name": model.name,
        "namespace": model.namespace,
        "claim_name": model.claim_name,
        "cost_weights": model.weights.as_dict(),
        "histories": [
            {
                "id": history.id,
                "claim": history.claim,
                "description": history.description,
            }
            for history in model.histories
        ],
        "channels": [
            {
                "id": channel.id,
                "cost": channel.cost.as_dict(),
                "observations": channel.observations,
                "description": channel.description,
            }
            for channel in model.channels
        ],
    }


def build_edges(model: EvidenceModel) -> tuple[DisagreementEdge, ...]:
    edges: list[DisagreementEdge] = []
    for left, right in combinations(model.histories, 2):
        if left.claim == right.claim:
            continue
        separators = tuple(
            channel.id
            for channel in model.channels
            if model.observation_key(channel.id, left.id)
            != model.observation_key(channel.id, right.id)
        )
        edges.append(
            DisagreementEdge(
                id=f"edge-{len(edges)}",
                left=left.id,
                right=right.id,
                separators=separators,
            )
        )
    if not edges:
        raise ValidationError("model contains no claim-disagreement pair")
    return tuple(edges)


def _selection(model: EvidenceModel, mask: int) -> tuple[str, ...]:
    return tuple(
        channel.id
        for index, channel in enumerate(model.channels)
        if mask & (1 << index)
    )


def _selection_cost(model: EvidenceModel, selected: tuple[str, ...]) -> CostVector:
    total = ZERO_COST
    for channel_id in selected:
        total = total + model.channel_by_id[channel_id].cost
    return total


def evaluate_candidates(
    model: EvidenceModel, edges: tuple[DisagreementEdge, ...]
) -> tuple[CandidateEvaluation, ...]:
    evaluations: list[CandidateEvaluation] = []
    for mask in range(1 << len(model.channels)):
        selected = _selection(model, mask)
        selected_set = set(selected)
        uncovered = next(
            (
                edge.id
                for edge in edges
                if selected_set.isdisjoint(edge.separators)
            ),
            None,
        )
        cost = _selection_cost(model, selected)
        evaluations.append(
            CandidateEvaluation(
                mask=mask,
                channels=selected,
                cost=cost,
                weighted_cost=cost.weighted(model.weights),
                verifies=uncovered is None,
                uncovered_edge=uncovered,
            )
        )
    return tuple(evaluations)


def _proper_subset(left_mask: int, right_mask: int) -> bool:
    return left_mask != right_mask and (left_mask & right_mask) == left_mask


def _minimal_verifying(
    evaluations: tuple[CandidateEvaluation, ...]
) -> tuple[CandidateEvaluation, ...]:
    verifying = [candidate for candidate in evaluations if candidate.verifies]
    return tuple(
        candidate
        for candidate in verifying
        if not any(
            other.verifies and _proper_subset(other.mask, candidate.mask)
            for other in evaluations
        )
    )


def _dominates(left: CostVector, right: CostVector) -> bool:
    left_values = (left.operational, left.privacy, left.trust)
    right_values = (right.operational, right.privacy, right.trust)
    return all(a <= b for a, b in zip(left_values, right_values)) and any(
        a < b for a, b in zip(left_values, right_values)
    )


def _pareto_frontier(
    evaluations: tuple[CandidateEvaluation, ...]
) -> tuple[CandidateEvaluation, ...]:
    verifying = [candidate for candidate in evaluations if candidate.verifies]
    return tuple(
        candidate
        for candidate in verifying
        if not any(
            other.mask != candidate.mask and _dominates(other.cost, candidate.cost)
            for other in verifying
        )
    )


def _sort_key(candidate: CandidateEvaluation) -> tuple[Any, ...]:
    return (
        candidate.weighted_cost,
        len(candidate.channels),
        candidate.channels,
        candidate.mask,
    )


def solve_model(model: EvidenceModel) -> dict[str, Any]:
    edges = build_edges(model)
    evaluations = evaluate_candidates(model, edges)
    model_core = normalized_model(model)
    model_digest = document_digest(
        "evidenceSynthesisModel", MODEL_DIGEST_SCHEMA, model_core
    )
    impossible_edges = [edge for edge in edges if not edge.separators]

    core: dict[str, Any] = {
        "schema_version": CERTIFICATE_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "name": model.name,
        "namespace": model.namespace,
        "claim_name": model.claim_name,
        "model_digest": model_digest,
        "cost_weights": model.weights.as_dict(),
        "histories": [
            {"id": history.id, "claim": history.claim}
            for history in model.histories
        ],
        "channels": [
            {
                "id": channel.id,
                "cost": channel.cost.as_dict(),
                "weighted_cost": channel.cost.weighted(model.weights),
            }
            for channel in model.channels
        ],
        "disagreement_edges": [edge.as_dict() for edge in edges],
        "candidate_count": len(evaluations),
        "verifying_candidate_count": sum(
            1 for candidate in evaluations if candidate.verifies
        ),
    }

    if impossible_edges:
        witness = impossible_edges[0]
        core.update(
            {
                "status": "impossible",
                "impossibility_witness": witness.as_dict(),
                "all_channels_mask": (1 << len(model.channels)) - 1,
            }
        )
    else:
        verifying = sorted(
            (candidate for candidate in evaluations if candidate.verifies),
            key=_sort_key,
        )
        if not verifying:
            raise AssertionError("nonempty separator edges should admit the all-channel set")
        selected = verifying[0]
        optimal_weight = selected.weighted_cost
        optimal_sets = [
            candidate
            for candidate in verifying
            if candidate.weighted_cost == optimal_weight
        ]
        lower_cost_failures = [
            candidate
            for candidate in evaluations
            if candidate.weighted_cost < optimal_weight
        ]
        if any(candidate.verifies for candidate in lower_cost_failures):
            raise AssertionError("selected candidate is not minimum weighted cost")
        core.update(
            {
                "status": "synthesized",
                "selected": selected.as_dict(),
                "optimal_weighted_cost": optimal_weight,
                "optimal_sets": [candidate.as_dict() for candidate in optimal_sets],
                "minimal_verifying_sets": [
                    candidate.as_dict()
                    for candidate in sorted(_minimal_verifying(evaluations), key=_sort_key)
                ],
                "pareto_frontier": [
                    candidate.as_dict()
                    for candidate in sorted(_pareto_frontier(evaluations), key=_sort_key)
                ],
                "lower_cost_failures": [
                    candidate.as_dict()
                    for candidate in sorted(lower_cost_failures, key=_sort_key)
                ],
            }
        )

    certificate = dict(core)
    certificate["certificate_digest"] = document_digest(
        "evidenceSynthesisCertificate",
        CERTIFICATE_DIGEST_SCHEMA,
        core,
    )
    return certificate


def verify_certificate(model: EvidenceModel, certificate: Any) -> dict[str, Any]:
    if not isinstance(certificate, dict):
        raise ValidationError("certificate: expected an object")
    expected = solve_model(model)
    if certificate != expected:
        raise ValidationError(
            "synthesis certificate does not match exact recomputation of the model"
        )
    return certificate
