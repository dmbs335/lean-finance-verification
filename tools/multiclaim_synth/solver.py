from __future__ import annotations

from itertools import combinations
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Problem

REPORT_SCHEMA = "lfv-multiclaim-evidence-report-v1"


def _edges(problem: Problem, claims: tuple[str, ...]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for claim_id in claims:
        for left, right in combinations(problem.worlds, 2):
            if left.claims[claim_id] == right.claims[claim_id]:
                continue
            separators = [
                channel.id for channel in problem.channels
                if problem.observation_key(channel, left)
                != problem.observation_key(channel, right)
            ]
            edges.append({
                "claim": claim_id,
                "left": left.id,
                "right": right.id,
                "separators": separators,
            })
    return edges


def _solve_edges(problem: Problem, edges: list[dict[str, Any]]) -> dict[str, Any]:
    impossible = next((edge for edge in edges if not edge["separators"]), None)
    candidates: list[dict[str, Any]] = []
    for mask in range(1 << len(problem.channels)):
        selected = [
            channel.id for index, channel in enumerate(problem.channels)
            if mask & (1 << index)
        ]
        selected_set = set(selected)
        uncovered = next(
            (edge for edge in edges if selected_set.isdisjoint(edge["separators"])),
            None,
        )
        cost = sum(
            channel.cost for channel in problem.channels
            if channel.id in selected_set
        )
        candidate: dict[str, Any] = {
            "mask": mask,
            "channels": selected,
            "cost": cost,
            "verifies": uncovered is None,
        }
        if uncovered is not None:
            candidate["uncovered"] = uncovered
        candidates.append(candidate)
    if impossible is not None:
        return {
            "status": "impossible",
            "edges": edges,
            "witness": impossible,
            "candidate_count": len(candidates),
        }
    verifying = sorted(
        (candidate for candidate in candidates if candidate["verifies"]),
        key=lambda item: (item["cost"], len(item["channels"]), item["channels"]),
    )
    if not verifying:
        raise ValidationError("no verifying evidence selection")
    selected = verifying[0]
    return {
        "status": "synthesized",
        "edges": edges,
        "candidate_count": len(candidates),
        "selected": selected,
        "optimal_sets": [
            item for item in verifying if item["cost"] == selected["cost"]
        ],
        "lower_cost_failures": [
            item for item in candidates if item["cost"] < selected["cost"]
        ],
    }


def solve(problem: Problem) -> dict[str, Any]:
    per_claim = {
        claim_id: _solve_edges(problem, _edges(problem, (claim_id,)))
        for claim_id in problem.claim_ids
    }
    global_result = _solve_edges(problem, _edges(problem, problem.claim_ids))
    union_ids: list[str] = []
    for channel in problem.channels:
        if any(
            channel.id in per_claim[claim_id].get("selected", {}).get("channels", [])
            for claim_id in problem.claim_ids
        ):
            union_ids.append(channel.id)
    union_cost = sum(
        channel.cost for channel in problem.channels if channel.id in set(union_ids)
    )
    global_cost = global_result.get("selected", {}).get("cost")
    report = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "claims": list(problem.claim_ids),
        "per_claim": per_claim,
        "claim_specific_union": {
            "channels": union_ids,
            "cost": union_cost,
        },
        "global": global_result,
        "synergy_savings": (
            union_cost - global_cost if global_cost is not None else None
        ),
    }
    report["report_sha256"] = __import__("hashlib").sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "multi-claim report does not match exact recomputation"
        )
    return expected
