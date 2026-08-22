from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.evidence_synth.canonical import CANONICAL_FORMAT, document_digest
from tools.evidence_synth.errors import ValidationError as EvidenceValidationError
from tools.evidence_synth.model import CostVector, EvidenceModel, ZERO_COST
from tools.evidence_synth.solver import build_edges, solve_model

from .errors import ValidationError
from .policy import FaultScenario, RobustEvidencePolicy

CERTIFICATE_SCHEMA = "lfv-robust-evidence-synthesis-v1"
MODEL_DIGEST_SCHEMA = "lfv-robust-evidence-model-digest-v1"
POLICY_DIGEST_SCHEMA = "lfv-robust-evidence-policy-digest-v1"
CERTIFICATE_DIGEST_SCHEMA = "lfv-robust-evidence-certificate-digest-v1"


@dataclass(frozen=True)
class RobustCandidate:
    mask: int
    channels: tuple[str, ...]
    domains: tuple[str, ...]
    cost: CostVector
    weighted_cost: int
    verifies: bool
    failed_fault: str | None
    uncovered_edge: str | None
    surviving_channels: tuple[str, ...] | None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "mask": self.mask,
            "channels": list(self.channels),
            "domains": list(self.domains),
            "cost": self.cost.as_dict(),
            "weighted_cost": self.weighted_cost,
            "verifies": self.verifies,
        }
        if self.failed_fault is not None:
            result["failed_fault"] = self.failed_fault
        if self.uncovered_edge is not None:
            result["uncovered_edge"] = self.uncovered_edge
        if self.surviving_channels is not None:
            result["surviving_channels"] = list(self.surviving_channels)
        return result


def normalized_policy(policy: RobustEvidencePolicy) -> dict[str, Any]:
    return {
        "schema_version": "lfv-robust-evidence-policy-v1",
        "name": policy.name,
        "required_connectivity": policy.required_connectivity,
        "channel_domains": dict(sorted(policy.channel_domains.items())),
        "faults": [
            {
                "id": fault.id,
                "rank": fault.rank,
                "compromised_domains": list(fault.compromised_domains),
                "description": fault.description,
            }
            for fault in policy.faults
        ],
    }


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


def _selected(model: EvidenceModel, mask: int) -> tuple[str, ...]:
    return tuple(
        channel.id
        for index, channel in enumerate(model.channels)
        if mask & (1 << index)
    )


def _selection_cost(model: EvidenceModel, selected: tuple[str, ...]) -> CostVector:
    total = ZERO_COST
    by_id = model.channel_by_id
    for channel_id in selected:
        total = total + by_id[channel_id].cost
    return total


def _survivors(
    selected: tuple[str, ...],
    fault: FaultScenario,
    policy: RobustEvidencePolicy,
) -> tuple[str, ...]:
    compromised = set(fault.compromised_domains)
    return tuple(
        channel_id
        for channel_id in selected
        if policy.channel_domains[channel_id] not in compromised
    )


def _first_failure(
    selected: tuple[str, ...],
    edges: tuple,
    policy: RobustEvidencePolicy,
) -> tuple[str, str, tuple[str, ...]] | None:
    for fault in policy.faults:
        if fault.rank >= policy.required_connectivity:
            continue
        survivors = _survivors(selected, fault, policy)
        survivor_set = set(survivors)
        for edge in edges:
            if survivor_set.isdisjoint(edge.separators):
                return fault.id, edge.id, survivors
    return None


def evaluate_candidates(
    model: EvidenceModel,
    policy: RobustEvidencePolicy,
) -> tuple[RobustCandidate, ...]:
    edges = build_edges(model)
    evaluations: list[RobustCandidate] = []
    for mask in range(1 << len(model.channels)):
        selected = _selected(model, mask)
        failure = _first_failure(selected, edges, policy)
        cost = _selection_cost(model, selected)
        domains = tuple(
            sorted({policy.channel_domains[channel_id] for channel_id in selected})
        )
        evaluations.append(
            RobustCandidate(
                mask=mask,
                channels=selected,
                domains=domains,
                cost=cost,
                weighted_cost=cost.weighted(model.weights),
                verifies=failure is None,
                failed_fault=None if failure is None else failure[0],
                uncovered_edge=None if failure is None else failure[1],
                surviving_channels=None if failure is None else failure[2],
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


def _sort_key(candidate: RobustCandidate) -> tuple[Any, ...]:
    return (
        candidate.weighted_cost,
        len(candidate.channels),
        candidate.channels,
        candidate.mask,
    )


def solve_robust(
    model: EvidenceModel,
    policy: RobustEvidencePolicy,
) -> dict[str, Any]:
    edges = build_edges(model)
    evaluations = evaluate_candidates(model, policy)
    verifying = sorted(
        (candidate for candidate in evaluations if candidate.verifies),
        key=_sort_key,
    )
    if not verifying:
        raise ValidationError(
            "no evidence subset satisfies the requested fault connectivity"
        )
    selected = verifying[0]
    lower_cost_failures = [
        candidate
        for candidate in evaluations
        if candidate.weighted_cost < selected.weighted_cost
    ]
    if any(candidate.verifies for candidate in lower_cost_failures):
        raise AssertionError("selected robust candidate is not minimum cost")
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
    try:
        ordinary = solve_model(model)
    except EvidenceValidationError as exc:
        raise ValidationError(str(exc)) from exc
    core: dict[str, Any] = {
        "schema_version": CERTIFICATE_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "name": policy.name,
        "required_connectivity": policy.required_connectivity,
        "model_digest": document_digest(
            "robustEvidenceModel",
            MODEL_DIGEST_SCHEMA,
            normalized_model(model),
        ),
        "policy_digest": document_digest(
            "robustEvidencePolicy",
            POLICY_DIGEST_SCHEMA,
            normalized_policy(policy),
        ),
        "histories": [
            {"id": history.id, "claim": history.claim}
            for history in model.histories
        ],
        "channels": [
            {
                "id": channel.id,
                "domain": policy.channel_domains[channel.id],
                "cost": channel.cost.as_dict(),
                "weighted_cost": channel.cost.weighted(model.weights),
            }
            for channel in model.channels
        ],
        "faults": [
            {
                "id": fault.id,
                "rank": fault.rank,
                "compromised_domains": list(fault.compromised_domains),
            }
            for fault in policy.faults
        ],
        "disagreement_edges": [edge.as_dict() for edge in edges],
        "candidate_count": len(evaluations),
        "robust_candidate_count": len(verifying),
        "ordinary_optimum": ordinary.get("selected"),
        "selected": selected.as_dict(),
        "optimal_weighted_cost": selected.weighted_cost,
        "optimal_sets": [
            candidate.as_dict()
            for candidate in verifying
            if candidate.weighted_cost == selected.weighted_cost
        ],
        "minimal_robust_sets": [
            candidate.as_dict() for candidate in sorted(minimal, key=_sort_key)
        ],
        "pareto_frontier": [
            candidate.as_dict() for candidate in sorted(pareto, key=_sort_key)
        ],
        "lower_cost_failures": [
            candidate.as_dict()
            for candidate in sorted(lower_cost_failures, key=_sort_key)
        ],
    }
    result = dict(core)
    result["certificate_digest"] = document_digest(
        "robustEvidenceCertificate",
        CERTIFICATE_DIGEST_SCHEMA,
        core,
    )
    return result


def verify_certificate(
    model: EvidenceModel,
    policy: RobustEvidencePolicy,
    certificate: Any,
) -> dict[str, Any]:
    if not isinstance(certificate, dict):
        raise ValidationError("certificate: expected an object")
    expected = solve_robust(model, policy)
    if certificate != expected:
        raise ValidationError(
            "robust evidence certificate does not match exact regeneration"
        )
    return certificate
