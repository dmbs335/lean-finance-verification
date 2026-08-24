from __future__ import annotations

import hashlib
from itertools import combinations
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Problem, Strategy

REPORT_SCHEMA = "lfv-evidence-adjusted-portfolio-report-v1"


def _shared_domains(
    selected: tuple[Strategy, ...],
) -> tuple[list[dict[str, Any]], int]:
    pairs: list[dict[str, Any]] = []
    concentration = 0
    for left, right in combinations(selected, 2):
        shared = sorted(set(left.domains) & set(right.domains))
        concentration += len(shared)
        pairs.append({
            "left": left.id,
            "right": right.id,
            "shared_domains": shared,
        })
    return pairs, concentration


def _candidate(problem: Problem, selected: tuple[Strategy, ...]) -> dict[str, Any]:
    selected = tuple(sorted(selected, key=lambda strategy: strategy.id))
    pairs, concentration = _shared_domains(selected)
    observed_alpha = sum(strategy.observed_alpha_bps for strategy in selected)
    certifiable_alpha = sum(
        strategy.certifiable_lower_bps for strategy in selected
    )
    risk = sum(strategy.risk_units for strategy in selected)
    debt = sum(strategy.evidence_debt for strategy in selected)
    robustness = sum(strategy.robustness for strategy in selected)
    objective = problem.objective
    raw_risk_penalty = objective.raw_risk_penalty * risk
    adjusted_risk_penalty = objective.risk_penalty * risk
    debt_penalty = objective.debt_penalty * debt
    robustness_reward = objective.robustness_reward * robustness
    dependency_penalty = objective.dependency_penalty * concentration
    raw_score = observed_alpha - raw_risk_penalty
    adjusted_score = (
        certifiable_alpha
        - adjusted_risk_penalty
        - debt_penalty
        + robustness_reward
        - dependency_penalty
    )
    return {
        "strategies": [strategy.id for strategy in selected],
        "domains": sorted({
            domain for strategy in selected for domain in strategy.domains
        }),
        "dependency_pairs": pairs,
        "dependency_concentration": concentration,
        "observed_alpha_bps": observed_alpha,
        "certifiable_lower_bps": certifiable_alpha,
        "certifiability_haircut_bps": observed_alpha - certifiable_alpha,
        "risk_units": risk,
        "evidence_debt": debt,
        "robustness": robustness,
        "raw": {
            "alpha_component": observed_alpha,
            "risk_penalty": raw_risk_penalty,
            "score": raw_score,
        },
        "evidence_adjusted": {
            "alpha_component": certifiable_alpha,
            "risk_penalty": adjusted_risk_penalty,
            "debt_penalty": debt_penalty,
            "robustness_reward": robustness_reward,
            "dependency_penalty": dependency_penalty,
            "score": adjusted_score,
        },
    }


def solve(problem: Problem) -> dict[str, Any]:
    candidates = [
        _candidate(problem, selected)
        for selected in combinations(problem.strategies, problem.selection_size)
    ]
    raw_order = sorted(
        candidates,
        key=lambda item: (
            -item["raw"]["score"],
            item["dependency_concentration"],
            item["strategies"],
        ),
    )
    adjusted_order = sorted(
        candidates,
        key=lambda item: (
            -item["evidence_adjusted"]["score"],
            item["evidence_debt"],
            item["dependency_concentration"],
            item["strategies"],
        ),
    )
    raw_selected = raw_order[0]
    adjusted_selected = adjusted_order[0]
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "selection_size": problem.selection_size,
        "candidate_count": len(candidates),
        "objective": {
            "raw_risk_penalty": problem.objective.raw_risk_penalty,
            "risk_penalty": problem.objective.risk_penalty,
            "debt_penalty": problem.objective.debt_penalty,
            "robustness_reward": problem.objective.robustness_reward,
            "dependency_penalty": problem.objective.dependency_penalty,
        },
        "raw_optimum": raw_selected,
        "evidence_adjusted_optimum": adjusted_selected,
        "selection_changed": (
            raw_selected["strategies"] != adjusted_selected["strategies"]
        ),
        "raw_optimum_adjusted_score": raw_selected["evidence_adjusted"]["score"],
        "adjusted_optimum_score_gain": (
            adjusted_selected["evidence_adjusted"]["score"]
            - raw_selected["evidence_adjusted"]["score"]
        ),
        "candidates": sorted(candidates, key=lambda item: item["strategies"]),
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "evidence-adjusted portfolio report does not match exact recomputation"
        )
    return expected
