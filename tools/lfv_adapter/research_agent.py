from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

SCHEMA = "lfv-proof-carrying-research-agent-v1"
REPORT_SCHEMA = "lfv-proof-carrying-research-agent-report-v1"
MAX_CHANNELS = 16


class ResearchAgentValidationError(ValueError):
    """Raised when a candidate batch or agent report is malformed."""


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ResearchAgentValidationError(f"{path}: expected object")
    return value


def _identifier(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ResearchAgentValidationError(f"{path}: expected non-empty string")
    return value


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ResearchAgentValidationError(f"{path}: expected integer")
    return value


def _natural(value: Any, path: str) -> int:
    result = _integer(value, path)
    if result < 0:
        raise ResearchAgentValidationError(f"{path}: expected non-negative integer")
    return result


@dataclass(frozen=True)
class Obligation:
    id: str
    separators: tuple[str, ...]


@dataclass(frozen=True)
class Candidate:
    id: str
    observed_alpha_bps: int
    cleaned_alpha_bps: int
    uncertainty_bps: int
    market_impact_bps: int
    capacity_haircut_bps: int
    selected_evidence: tuple[str, ...]
    obligations: tuple[Obligation, ...]


@dataclass(frozen=True)
class Batch:
    source: Path
    name: str
    channel_costs: dict[str, int]
    candidates: tuple[Candidate, ...]


def load_batch(path: Path) -> Batch:
    raw = _object(load_json(path), "$")
    expected = {"schema_version", "name", "channel_costs", "candidates"}
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ResearchAgentValidationError("$: fields or schema do not match")

    costs_raw = _object(raw["channel_costs"], "$.channel_costs")
    channel_costs = {
        _identifier(channel, "$.channel_costs key"): _natural(
            cost, f"$.channel_costs.{channel}"
        )
        for channel, cost in costs_raw.items()
    }
    if not channel_costs or len(channel_costs) > MAX_CHANNELS:
        raise ResearchAgentValidationError(
            f"$.channel_costs: expected between 1 and {MAX_CHANNELS} channels"
        )

    candidates: list[Candidate] = []
    for candidate_index, item in enumerate(raw["candidates"]):
        obj = _object(item, f"$.candidates[{candidate_index}]")
        selected = tuple(obj.get("selected_evidence", []))
        if any(not isinstance(value, str) or not value for value in selected):
            raise ResearchAgentValidationError(
                f"$.candidates[{candidate_index}].selected_evidence: expected strings"
            )
        if len(set(selected)) != len(selected):
            raise ResearchAgentValidationError(
                f"$.candidates[{candidate_index}].selected_evidence: duplicates"
            )
        obligations: list[Obligation] = []
        for obligation_index, obligation_raw in enumerate(obj.get("obligations", [])):
            obligation_obj = _object(
                obligation_raw,
                f"$.candidates[{candidate_index}].obligations[{obligation_index}]",
            )
            separators = tuple(obligation_obj.get("separators", []))
            if not separators or any(
                not isinstance(value, str) or not value for value in separators
            ):
                raise ResearchAgentValidationError(
                    f"candidate {candidate_index} obligation {obligation_index}: "
                    "expected non-empty separator list"
                )
            if len(set(separators)) != len(separators):
                raise ResearchAgentValidationError(
                    f"candidate {candidate_index} obligation {obligation_index}: "
                    "duplicate separators"
                )
            obligations.append(
                Obligation(
                    id=_identifier(
                        obligation_obj.get("id"),
                        f"$.candidates[{candidate_index}].obligations[{obligation_index}].id",
                    ),
                    separators=separators,
                )
            )
        if len({obligation.id for obligation in obligations}) != len(obligations):
            raise ResearchAgentValidationError(
                f"$.candidates[{candidate_index}].obligations: duplicate ids"
            )
        candidates.append(
            Candidate(
                id=_identifier(obj.get("id"), f"$.candidates[{candidate_index}].id"),
                observed_alpha_bps=_integer(
                    obj.get("observed_alpha_bps"),
                    f"$.candidates[{candidate_index}].observed_alpha_bps",
                ),
                cleaned_alpha_bps=_integer(
                    obj.get("cleaned_alpha_bps"),
                    f"$.candidates[{candidate_index}].cleaned_alpha_bps",
                ),
                uncertainty_bps=_natural(
                    obj.get("uncertainty_bps"),
                    f"$.candidates[{candidate_index}].uncertainty_bps",
                ),
                market_impact_bps=_natural(
                    obj.get("market_impact_bps"),
                    f"$.candidates[{candidate_index}].market_impact_bps",
                ),
                capacity_haircut_bps=_natural(
                    obj.get("capacity_haircut_bps"),
                    f"$.candidates[{candidate_index}].capacity_haircut_bps",
                ),
                selected_evidence=selected,
                obligations=tuple(obligations),
            )
        )
    if not candidates or len({candidate.id for candidate in candidates}) != len(candidates):
        raise ResearchAgentValidationError(
            "$.candidates: expected unique non-empty candidates"
        )
    return Batch(
        source=path.resolve(),
        name=_identifier(raw["name"], "$.name"),
        channel_costs=channel_costs,
        candidates=tuple(candidates),
    )


def _unresolved(candidate: Candidate, selected: set[str]) -> list[Obligation]:
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
            if any(combined.isdisjoint(obligation.separators) for obligation in unresolved):
                continue
            cost = sum(channel_costs[channel] for channel in subset)
            key = (cost, len(subset), subset)
            if best is None or key < best:
                best = key
        if best is not None and best[1] == size:
            # Larger subsets can still be cheaper when zero-cost channels exist,
            # so stop only after exhausting all subsets with the selected size.
            continue
    if best is None:
        return {
            "status": "impossible",
            "channels": [],
            "cost": None,
            "unresolved_obligations": [
                {
                    "id": obligation.id,
                    "separators": list(obligation.separators),
                }
                for obligation in unresolved
            ],
        }
    return {
        "status": "synthesized",
        "channels": list(best[2]),
        "cost": best[0],
        "unresolved_obligations": [
            {
                "id": obligation.id,
                "separators": list(obligation.separators),
            }
            for obligation in unresolved
        ],
    }


def _evaluate_candidate(
    candidate: Candidate,
    channel_costs: dict[str, int],
) -> dict[str, Any]:
    selected = set(candidate.selected_evidence)
    unresolved = _unresolved(candidate, selected)
    integrity_verified = not unresolved
    repair = _minimum_repair(candidate, channel_costs)
    certifiable_lower = candidate.cleaned_alpha_bps - candidate.uncertainty_bps
    certifiable_upper = candidate.cleaned_alpha_bps + candidate.uncertainty_bps
    deployable_lower = (
        certifiable_lower
        - candidate.market_impact_bps
        - candidate.capacity_haircut_bps
    )

    if not integrity_verified:
        if repair["status"] == "synthesized":
            decision = "repairEvidence"
            rationale = "modeled claim disagreements remain observationally unresolved"
        else:
            decision = "rejectCandidate"
            rationale = "the declared evidence language cannot separate every attack obligation"
    elif deployable_lower <= 0:
        decision = "rejectCandidate"
        rationale = "deployable certifiable alpha lower bound is nonpositive"
    else:
        decision = "advanceToHumanReview"
        rationale = "integrity is verified and deployable lower bound is positive"

    next_steps: list[str]
    if decision == "repairEvidence":
        next_steps = [
            "deploy the synthesized evidence channels",
            "rerun workflow counterexample search",
            "regenerate the proof-carrying certificate",
        ]
    elif decision == "advanceToHumanReview":
        next_steps = [
            "review model, sampling, capacity, and provider assumptions",
            "approve or reject manually; autonomous deployment is forbidden",
        ]
    else:
        next_steps = [
            "archive the counterexample and rejection rationale",
            "revise the strategy or evidence language before resubmission",
        ]

    return {
        "id": candidate.id,
        "decision": decision,
        "rationale": rationale,
        "observed_alpha_bps": candidate.observed_alpha_bps,
        "cleaned_alpha_bps": candidate.cleaned_alpha_bps,
        "certifiable_interval_bps": {
            "lower": certifiable_lower,
            "upper": certifiable_upper,
        },
        "market_impact_bps": candidate.market_impact_bps,
        "capacity_haircut_bps": candidate.capacity_haircut_bps,
        "deployable_lower_bound_bps": deployable_lower,
        "integrity_verified": integrity_verified,
        "selected_evidence": list(candidate.selected_evidence),
        "unresolved_obligations": [
            {
                "id": obligation.id,
                "separators": list(obligation.separators),
            }
            for obligation in unresolved
        ],
        "minimum_repair": repair,
        "human_approval_required": decision == "advanceToHumanReview",
        "next_steps": next_steps,
    }


def evaluate(batch: Batch) -> dict[str, Any]:
    candidates = [
        _evaluate_candidate(candidate, batch.channel_costs)
        for candidate in batch.candidates
    ]
    counts = {
        decision: sum(candidate["decision"] == decision for candidate in candidates)
        for decision in (
            "advanceToHumanReview",
            "repairEvidence",
            "rejectCandidate",
        )
    }
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": batch.name,
        "candidate_count": len(candidates),
        "decision_counts": counts,
        "autonomous_deployment_permitted": False,
        "candidates": candidates,
    }
    report["report_sha256"] = hashlib.sha256(canonical_bytes(report)).hexdigest()
    return report


def verify(batch: Batch, report: Any) -> dict[str, Any]:
    expected = evaluate(batch)
    if report != expected:
        raise ResearchAgentValidationError(
            "research-agent report does not match exact recomputation"
        )
    return expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-proof-carrying-research-agent")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--batch", required=True, type=Path)
    analyze.add_argument("--out", required=True, type=Path)
    check = sub.add_parser("verify")
    check.add_argument("--batch", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        batch = load_batch(args.batch)
        if args.command == "analyze":
            report = evaluate(batch)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(report, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
        else:
            verify(batch, load_json(args.report))
        return 0
    except (ResearchAgentValidationError, OSError) as exc:
        print(f"error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
