from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

from tools.evidence_synth.canonical import CANONICAL_FORMAT, document_digest
from tools.evidence_synth.errors import ValidationError

from .model import CostVector, RobustEvidenceModel, ZERO_COST

CERTIFICATE_SCHEMA = "lfv-robust-evidence-certificate-v1"
MODEL_DIGEST_SCHEMA = "lfv-robust-evidence-model-digest-v1"
CERTIFICATE_DIGEST_SCHEMA = "lfv-robust-evidence-certificate-digest-v1"


@dataclass(frozen=True)
class Edge:
    id: str
    left: str
    right: str
    separators: tuple[str, ...]
    separator_domains: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "left": self.left,
            "right": self.right,
            "separators": list(self.separators),
            "separator_domains": list(self.separator_domains),
        }


@dataclass(frozen=True)
class Candidate:
    mask: int
    channels: tuple[str, ...]
    domains: tuple[str, ...]
    cost: CostVector
    weighted_cost: int
    robust: bool
    failed_fault: tuple[str, ...] | None
    uncovered_edge: str | None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "mask": self.mask,
            "channels": list(self.channels),
            "domains": list(self.domains),
            "cost": self.cost.as_dict(),
            "weighted_cost": self.weighted_cost,
            "robust": self.robust,
        }
        if self.failed_fault is not None:
            result["failed_fault"] = list(self.failed_fault)
        if self.uncovered_edge is not None:
            result["uncovered_edge"] = self.uncovered_edge
        return result


def normalized_model(model: RobustEvidenceModel) -> dict[str, Any]:
    return {
        "schema_version": "lfv-robust-evidence-model-v1",
        "name": model.name,
        "namespace": model.namespace,
        "claim_name": model.claim_name,
        "required_connectivity": model.required_connectivity,
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
                "domain": channel.domain,
                "cost": channel.cost.as_dict(),
                "observations": channel.observations,
                "description": channel.description,
            }
            for channel in model.channels
        ],
    }


def build_edges(model: RobustEvidenceModel) -> tuple[Edge, ...]:
    edges: list[Edge] = []
    for left, right in combinations(model.histories, 2):
        if left.claim == right.claim:
            continue
        separators = tuple(
            channel.id
            for channel in model.channels
            if model.observation_key(channel.id, left.id)
            != model.observation_key(channel.id, right.id)
        )
        domains: list[str] = []
        for channel_id in separators:
            domain = model.channel_by_id[channel_id].domain
            if domain not in domains:
                domains.append(domain)
        edges.append(
            Edge(
                id=f"edge-{len(edges)}",
                left=left.id,
                right=right.id,
                separators=separators,
                separator_domains=tuple(domains),
            )
        )
    if not edges:
        raise ValidationError("model contains no claim-disagreement pair")
    return tuple(edges)


def enumerate_faults(model: RobustEvidenceModel) -> tuple[tuple[str, ...], ...]:
    faults: list[tuple[str, ...]] = []
    for size in range(model.required_connectivity):
        faults.extend(combinations(model.domains, size))
    return tuple(faults)


def _selection(model: RobustEvidenceModel, mask: int) -> tuple[str, ...]:
    return tuple(
        channel.id
        for index, channel in enumerate(model.channels)
        if mask & (1 << index)
    )


def _selection_domains(
    model: RobustEvidenceModel, selected: tuple[str, ...]
) -> tuple[str, ...]:
    result: list[str] = []
    for channel_id in selected:
        domain = model.channel_by_id[channel_id].domain
        if domain not in result:
            result.append(domain)
    return tuple(result)


def _selection_cost(
    model: RobustEvidenceModel, selected: tuple[str, ...]
) -> CostVector:
    result = ZERO_COST
    for channel_id in selected:
        result = result + model.channel_by_id[channel_id].cost
    return result


def _failure(
    model: RobustEvidenceModel,
    selected: tuple[str, ...],
    edges: tuple[Edge, ...],
    faults: tuple[tuple[str, ...], ...],
) -> tuple[tuple[str, ...] | None, str | None]:
    for failed_domains in faults:
        failed = set(failed_domains)
        live_selected = {
            channel_id
            for channel_id in selected
            if model.channel_by_id[channel_id].domain not in failed
        }
        for edge in edges:
            if live_selected.isdisjoint(edge.separators):
                return failed_domains, edge.id
    return None, None


def evaluate_candidates(
    model: RobustEvidenceModel,
    edges: tuple[Edge, ...],
    faults: tuple[tuple[str, ...], ...],
) -> tuple[Candidate, ...]:
    candidates: list[Candidate] = []
    for mask in range(1 << len(model.channels)):
        selected = _selection(model, mask)
        failed_fault, uncovered_edge = _failure(
            model, selected, edges, faults
        )
        cost = _selection_cost(model, selected)
        candidates.append(
            Candidate(
                mask=mask,
                channels=selected,
                domains=_selection_domains(model, selected),
                cost=cost,
                weighted_cost=cost.weighted(model.weights),
                robust=failed_fault is None,
                failed_fault=failed_fault,
                uncovered_edge=uncovered_edge,
            )
        )
    return tuple(candidates)


def _proper_subset(left: int, right: int) -> bool:
    return left != right and (left & right) == left


def _sort_key(candidate: Candidate) -> tuple[Any, ...]:
    return (
        candidate.weighted_cost,
        len(candidate.channels),
        candidate.channels,
        candidate.mask,
    )


def solve_model(model: RobustEvidenceModel) -> dict[str, Any]:
    edges = build_edges(model)
    faults = enumerate_faults(model)
    candidates = evaluate_candidates(model, edges, faults)
    impossible_edges = [
        edge
        for edge in edges
        if len(edge.separator_domains) < model.required_connectivity
    ]
    model_core = normalized_model(model)
    core: dict[str, Any] = {
        "schema_version": CERTIFICATE_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "name": model.name,
        "namespace": model.namespace,
        "claim_name": model.claim_name,
        "required_connectivity": model.required_connectivity,
        "model_digest": document_digest(
            "robustEvidenceModel", MODEL_DIGEST_SCHEMA, model_core
        ),
        "domains": list(model.domains),
        "faults": [list(fault) for fault in faults],
        "histories": [
            {"id": history.id, "claim": history.claim}
            for history in model.histories
        ],
        "channels": [
            {
                "id": channel.id,
                "domain": channel.domain,
                "cost": channel.cost.as_dict(),
                "weighted_cost": channel.cost.weighted(model.weights),
            }
            for channel in model.channels
        ],
        "disagreement_edges": [edge.as_dict() for edge in edges],
        "candidate_count": len(candidates),
        "robust_candidate_count": sum(
            1 for candidate in candidates if candidate.robust
        ),
    }
    if impossible_edges:
        core.update(
            {
                "status": "impossible",
                "impossibility_witness": impossible_edges[0].as_dict(),
            }
        )
    else:
        robust = sorted(
            (candidate for candidate in candidates if candidate.robust),
            key=_sort_key,
        )
        if not robust:
            raise AssertionError(
                "sufficient domain multiplicity should admit the all-channel set"
            )
        selected = robust[0]
        lower_failures = [
            candidate
            for candidate in candidates
            if candidate.weighted_cost < selected.weighted_cost
        ]
        if any(candidate.robust for candidate in lower_failures):
            raise AssertionError("selected robust portfolio is not cost minimal")
        minimal = [
            candidate
            for candidate in robust
            if not any(
                other.robust and _proper_subset(other.mask, candidate.mask)
                for other in candidates
            )
        ]
        core.update(
            {
                "status": "synthesized",
                "selected": selected.as_dict(),
                "optimal_weighted_cost": selected.weighted_cost,
                "optimal_sets": [
                    candidate.as_dict()
                    for candidate in robust
                    if candidate.weighted_cost == selected.weighted_cost
                ],
                "minimal_robust_sets": [
                    candidate.as_dict()
                    for candidate in sorted(minimal, key=_sort_key)
                ],
                "lower_cost_failures": [
                    candidate.as_dict()
                    for candidate in sorted(lower_failures, key=_sort_key)
                ],
            }
        )
    certificate = dict(core)
    certificate["certificate_digest"] = document_digest(
        "robustEvidenceCertificate", CERTIFICATE_DIGEST_SCHEMA, core
    )
    return certificate


def verify_certificate(
    model: RobustEvidenceModel, certificate: Any
) -> dict[str, Any]:
    if not isinstance(certificate, dict):
        raise ValidationError("certificate: expected an object")
    expected = solve_model(model)
    if certificate != expected:
        raise ValidationError(
            "robust evidence certificate does not match exact recomputation"
        )
    return certificate
