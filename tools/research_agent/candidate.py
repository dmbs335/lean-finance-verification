from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

from .errors import ValidationError

SCHEMA = "lfv-research-candidate-batch-v1"
REPORT_SCHEMA = "lfv-research-candidate-report-v1"
MAX_CHANNELS = 16


@dataclass(frozen=True)
class Obligation:
    id: str
    separators: tuple[str, ...]


@dataclass(frozen=True)
class Candidate:
    id: str
    observed_alpha_bps: int
    attack_cleaned_alpha_bps: int
    residual_uncertainty_bps: int
    market_impact_bps: int
    capacity_haircut_bps: int
    selected_evidence: tuple[str, ...]
    obligations: tuple[Obligation, ...]


@dataclass(frozen=True)
class CandidateBatch:
    source: Path
    name: str
    channel_costs: dict[str, int]
    candidates: tuple[Candidate, ...]


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path}: expected integer")
    return value


def _natural(value: Any, path: str) -> int:
    result = _integer(value, path)
    if result < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return result


def load_candidate_batch(path: Path) -> CandidateBatch:
    raw = _object(load_json(path), "$")
    expected = {"schema_version", "name", "channel_costs", "candidates"}
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match candidate batch")

    costs_raw = _object(raw["channel_costs"], "$.channel_costs")
    channel_costs = {
        _string(channel, "$.channel_costs key"): _natural(
            cost, f"$.channel_costs.{channel}"
        )
        for channel, cost in costs_raw.items()
    }
    if not channel_costs or len(channel_costs) > MAX_CHANNELS:
        raise ValidationError(
            f"$.channel_costs: expected between 1 and {MAX_CHANNELS} channels"
        )

    candidates_raw = raw["candidates"]
    if not isinstance(candidates_raw, list) or not candidates_raw:
        raise ValidationError("$.candidates: expected non-empty array")
    candidates: list[Candidate] = []
    for candidate_index, item in enumerate(candidates_raw):
        candidate_path = f"$.candidates[{candidate_index}]"
        obj = _object(item, candidate_path)
        expected_candidate = {
            "id",
            "observed_alpha_bps",
            "attack_cleaned_alpha_bps",
            "residual_uncertainty_bps",
            "market_impact_bps",
            "capacity_haircut_bps",
            "selected_evidence",
            "obligations",
        }
        if set(obj) != expected_candidate:
            raise ValidationError(
                f"{candidate_path}: fields do not match candidate schema"
            )
        selected_raw = obj["selected_evidence"]
        if not isinstance(selected_raw, list) or any(
            not isinstance(channel, str) or not channel
            for channel in selected_raw
        ):
            raise ValidationError(
                f"{candidate_path}.selected_evidence: expected string array"
            )
        selected = tuple(selected_raw)
        if len(set(selected)) != len(selected):
            raise ValidationError(
                f"{candidate_path}.selected_evidence: duplicates are not allowed"
            )
        unknown_selected = set(selected) - set(channel_costs)
        if unknown_selected:
            raise ValidationError(
                f"{candidate_path}.selected_evidence: unknown channels "
                f"{sorted(unknown_selected)}"
            )

        obligations_raw = obj["obligations"]
        if not isinstance(obligations_raw, list):
            raise ValidationError(
                f"{candidate_path}.obligations: expected array"
            )
        obligations: list[Obligation] = []
        for obligation_index, obligation_item in enumerate(obligations_raw):
            obligation_path = (
                f"{candidate_path}.obligations[{obligation_index}]"
            )
            obligation_obj = _object(obligation_item, obligation_path)
            if set(obligation_obj) != {"id", "separators"}:
                raise ValidationError(
                    f"{obligation_path}: fields do not match obligation schema"
                )
            separators_raw = obligation_obj["separators"]
            if not isinstance(separators_raw, list) or not separators_raw or any(
                not isinstance(channel, str) or not channel
                for channel in separators_raw
            ):
                raise ValidationError(
                    f"{obligation_path}.separators: expected non-empty strings"
                )
            separators = tuple(separators_raw)
            if len(set(separators)) != len(separators):
                raise ValidationError(
                    f"{obligation_path}.separators: duplicates are not allowed"
                )
            obligations.append(
                Obligation(
                    id=_string(obligation_obj["id"], f"{obligation_path}.id"),
                    separators=separators,
                )
            )
        if len({obligation.id for obligation in obligations}) != len(obligations):
            raise ValidationError(
                f"{candidate_path}.obligations: ids must be unique"
            )
        candidates.append(
            Candidate(
                id=_string(obj["id"], f"{candidate_path}.id"),
                observed_alpha_bps=_integer(
                    obj["observed_alpha_bps"],
                    f"{candidate_path}.observed_alpha_bps",
                ),
                attack_cleaned_alpha_bps=_integer(
                    obj["attack_cleaned_alpha_bps"],
                    f"{candidate_path}.attack_cleaned_alpha_bps",
                ),
                residual_uncertainty_bps=_natural(
                    obj["residual_uncertainty_bps"],
                    f"{candidate_path}.residual_uncertainty_bps",
                ),
                market_impact_bps=_natural(
                    obj["market_impact_bps"],
                    f"{candidate_path}.market_impact_bps",
                ),
                capacity_haircut_bps=_natural(
                    obj["capacity_haircut_bps"],
                    f"{candidate_path}.capacity_haircut_bps",
                ),
                selected_evidence=selected,
                obligations=tuple(obligations),
            )
        )
    if len({candidate.id for candidate in candidates}) != len(candidates):
        raise ValidationError("$.candidates: ids must be unique")
    return CandidateBatch(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        channel_costs=channel_costs,
        candidates=tuple(candidates),
    )


def _unresolved(
    candidate: Candidate, selected: set[str]
) -> list[Obligation]:
    return [
        obligation
        for obligation in candidate.obligations
        if selected.isdisjoint(obligation.separators)
    ]


def _minimum_repair(
    candidate: Candidate,
    channel_costs: dict[str, int],
) -> dict[str, Any]:
    selected = set(candidate.selected_evidence)
    unresolved = _unresolved(candidate, selected)
    if not unresolved:
        return {
            "status": "notNeeded",
            "channels": [],
            "cost": 0,
            "unresolved_obligations": [],
        }

    optional = sorted(set(channel_costs) - selected)
    best: tuple[int, int, tuple[str, ...]] | None = None
    for size in range(len(optional) + 1):
        for subset in itertools.combinations(optional, size):
            combined = selected | set(subset)
            if any(
                combined.isdisjoint(obligation.separators)
                for obligation in unresolved
            ):
                continue
            cost = sum(channel_costs[channel] for channel in subset)
            key = (cost, len(subset), subset)
            if best is None or key < best:
                best = key

    witnesses = [
        {"id": obligation.id, "separators": list(obligation.separators)}
        for obligation in unresolved
    ]
    if best is None:
        return {
            "status": "impossible",
            "channels": [],
            "cost": None,
            "unresolved_obligations": witnesses,
        }
    return {
        "status": "synthesized",
        "channels": list(best[2]),
        "cost": best[0],
        "unresolved_obligations": witnesses,
    }


def _evaluate_candidate(
    candidate: Candidate,
    channel_costs: dict[str, int],
) -> dict[str, Any]:
    selected = set(candidate.selected_evidence)
    unresolved = _unresolved(candidate, selected)
    integrity_verified = not unresolved
    repair = _minimum_repair(candidate, channel_costs)
    certifiable_lower = (
        candidate.attack_cleaned_alpha_bps
        - candidate.residual_uncertainty_bps
    )
    certifiable_upper = (
        candidate.attack_cleaned_alpha_bps
        + candidate.residual_uncertainty_bps
    )
    deployable_lower = (
        certifiable_lower
        - candidate.market_impact_bps
        - candidate.capacity_haircut_bps
    )

    if integrity_verified and deployable_lower > 0:
        decision = "advanceToHumanReview"
        rationale = (
            "integrity obligations are covered and the deployable lower bound "
            "is positive"
        )
    elif not integrity_verified and repair["status"] == "synthesized":
        decision = "repairEvidence"
        rationale = (
            "modeled claim disagreements remain unresolved but the declared "
            "channel language contains an exact repair"
        )
    else:
        decision = "rejectCandidate"
        rationale = (
            "the evidence gap is impossible in the declared channel language"
            if not integrity_verified
            else "the deployable certifiable-alpha lower bound is nonpositive"
        )

    return {
        "id": candidate.id,
        "decision": decision,
        "rationale": rationale,
        "observed_alpha_bps": candidate.observed_alpha_bps,
        "attack_cleaned_alpha_bps": candidate.attack_cleaned_alpha_bps,
        "certifiable_interval_bps": [certifiable_lower, certifiable_upper],
        "market_impact_bps": candidate.market_impact_bps,
        "capacity_haircut_bps": candidate.capacity_haircut_bps,
        "deployable_lower_bound_bps": deployable_lower,
        "integrity_verified": integrity_verified,
        "selected_evidence": list(candidate.selected_evidence),
        "unresolved_obligations": [
            {"id": obligation.id, "separators": list(obligation.separators)}
            for obligation in unresolved
        ],
        "minimum_repair": repair,
        "human_approval_required": decision == "advanceToHumanReview",
    }


def evaluate_candidate_batch(batch: CandidateBatch) -> dict[str, Any]:
    candidates = [
        _evaluate_candidate(candidate, batch.channel_costs)
        for candidate in batch.candidates
    ]
    decisions = (
        "advanceToHumanReview",
        "repairEvidence",
        "rejectCandidate",
    )
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": batch.name,
        "candidate_count": len(candidates),
        "decision_counts": {
            decision: sum(
                candidate["decision"] == decision
                for candidate in candidates
            )
            for decision in decisions
        },
        "autonomous_deployment_permitted": False,
        "candidates": candidates,
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify_candidate_batch(
    batch: CandidateBatch, report: Any
) -> dict[str, Any]:
    expected = evaluate_candidate_batch(batch)
    if report != expected:
        raise ValidationError(
            "research-candidate report does not match exact recomputation"
        )
    return expected
