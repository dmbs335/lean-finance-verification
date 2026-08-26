from __future__ import annotations

import hashlib
import math
from fractions import Fraction
from itertools import combinations
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Problem

REPORT_SCHEMA = "lfv-research-version-space-report-v1"


def _active_dimensions(problem: Problem, mask: int) -> tuple[str, ...]:
    return tuple(
        dimension.id
        for index, dimension in enumerate(problem.dimensions)
        if mask & (1 << index)
    )


def _metric(problem: Problem, mask: int) -> int:
    active = set(_active_dimensions(problem, mask))
    total = problem.base_metric
    for dimension in problem.dimensions:
        if dimension.id in active:
            total += dimension.alternative_effect
    for interaction in problem.interactions:
        if set(interaction.requires).issubset(active):
            total += interaction.effect
    return total


def _world(problem: Problem, mask: int) -> dict[str, Any]:
    active = _active_dimensions(problem, mask)
    active_set = set(active)
    return {
        "mask": mask,
        "active_alternatives": list(active),
        "states": {
            dimension.id: (
                dimension.alternative
                if dimension.id in active_set
                else dimension.baseline
            )
            for dimension in problem.dimensions
        },
        "metric": _metric(problem, mask),
    }


def _all_worlds(problem: Problem) -> list[dict[str, Any]]:
    return [
        _world(problem, mask)
        for mask in range(1 << len(problem.dimensions))
    ]


def _candidate(
    problem: Problem,
    worlds: list[dict[str, Any]],
    channel_mask: int,
) -> dict[str, Any]:
    selected = [
        channel
        for index, channel in enumerate(problem.channels)
        if channel_mask & (1 << index)
    ]
    restricted = {
        dimension
        for channel in selected
        for dimension in channel.restricts
    }
    admissible = [
        world
        for world in worlds
        if restricted.isdisjoint(world["active_alternatives"])
    ]
    if not admissible:
        raise ValidationError("evidence selection eliminated every world")
    lower_world = min(
        admissible,
        key=lambda world: (world["metric"], world["active_alternatives"]),
    )
    upper_world = min(
        admissible,
        key=lambda world: (-world["metric"], world["active_alternatives"]),
    )
    lower = lower_world["metric"]
    upper = upper_world["metric"]
    width = upper - lower
    result: dict[str, Any] = {
        "mask": channel_mask,
        "channels": [channel.id for channel in selected],
        "cost": sum(channel.cost for channel in selected),
        "restricted_dimensions": sorted(restricted),
        "admissible_world_count": len(admissible),
        "range": [lower, upper],
        "width": width,
        "meets_target": width <= problem.target_maximum_width,
    }
    if not result["meets_target"]:
        result["width_counterexample"] = {
            "lower_world": lower_world,
            "upper_world": upper_world,
            "differing_dimensions": sorted(
                set(lower_world["active_alternatives"])
                ^ set(upper_world["active_alternatives"])
            ),
        }
    return result


def _fraction(value: Fraction) -> dict[str, int]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
    }


def _shapley(problem: Problem) -> dict[str, Any]:
    count = len(problem.dimensions)
    denominator = math.factorial(count)
    values: list[dict[str, Any]] = []
    total = Fraction(0)
    for index, dimension in enumerate(problem.dimensions):
        bit = 1 << index
        contribution = Fraction(0)
        for mask in range(1 << count):
            if mask & bit:
                continue
            size = mask.bit_count()
            weight = Fraction(
                math.factorial(size)
                * math.factorial(count - size - 1),
                denominator,
            )
            contribution += weight * (
                _metric(problem, mask | bit) - _metric(problem, mask)
            )
        total += contribution
        values.append({
            "dimension": dimension.id,
            "contribution": _fraction(contribution),
        })
    all_mask = (1 << count) - 1
    total_difference = _metric(problem, all_mask) - _metric(problem, 0)
    if total != total_difference:
        raise AssertionError("Shapley contributions do not sum to total change")
    return {
        "baseline_metric": _metric(problem, 0),
        "all_alternative_metric": _metric(problem, all_mask),
        "total_difference": total_difference,
        "contributions": values,
        "sum": _fraction(total),
    }


def _flip_effects(problem: Problem) -> list[dict[str, Any]]:
    count = len(problem.dimensions)
    results: list[dict[str, Any]] = []
    for index, dimension in enumerate(problem.dimensions):
        bit = 1 << index
        effects: list[tuple[int, int]] = []
        for mask in range(1 << count):
            if mask & bit:
                continue
            effects.append((
                _metric(problem, mask | bit) - _metric(problem, mask),
                mask,
            ))
        minimum, minimum_mask = min(
            effects,
            key=lambda item: (item[0], _active_dimensions(problem, item[1])),
        )
        maximum, maximum_mask = min(
            effects,
            key=lambda item: (-item[0], _active_dimensions(problem, item[1])),
        )
        results.append({
            "dimension": dimension.id,
            "minimum_effect": minimum,
            "maximum_effect": maximum,
            "context_sensitive": minimum != maximum,
            "minimum_context": list(
                _active_dimensions(problem, minimum_mask)
            ),
            "maximum_context": list(
                _active_dimensions(problem, maximum_mask)
            ),
        })
    return results


def _refinement_checks(
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    pair_count = 0
    violations: list[dict[str, Any]] = []
    for weaker in candidates:
        weaker_set = set(weaker["channels"])
        for stronger in candidates:
            stronger_set = set(stronger["channels"])
            if not weaker_set.issubset(stronger_set):
                continue
            pair_count += 1
            nested = (
                weaker["range"][0] <= stronger["range"][0]
                and stronger["range"][1] <= weaker["range"][1]
            )
            if not nested:
                violations.append({
                    "weaker": weaker["channels"],
                    "stronger": stronger["channels"],
                    "weaker_range": weaker["range"],
                    "stronger_range": stronger["range"],
                })
    return {
        "checked_pair_count": pair_count,
        "all_ranges_nested": not violations,
        "violations": violations,
    }


def solve(problem: Problem) -> dict[str, Any]:
    worlds = _all_worlds(problem)
    candidates = [
        _candidate(problem, worlds, mask)
        for mask in range(1 << len(problem.channels))
    ]
    feasible = sorted(
        (candidate for candidate in candidates if candidate["meets_target"]),
        key=lambda candidate: (
            candidate["cost"],
            len(candidate["channels"]),
            candidate["channels"],
        ),
    )
    if not feasible:
        raise ValidationError("no evidence selection meets the target width")
    selected = feasible[0]
    lower_cost_failures = sorted(
        (
            candidate for candidate in candidates
            if candidate["cost"] < selected["cost"]
        ),
        key=lambda candidate: (
            candidate["cost"],
            len(candidate["channels"]),
            candidate["channels"],
        ),
    )
    if any(candidate["meets_target"] for candidate in lower_cost_failures):
        raise AssertionError("selected evidence is not minimum cost")
    point_identifying = sorted(
        (candidate for candidate in candidates if candidate["width"] == 0),
        key=lambda candidate: (
            candidate["cost"],
            len(candidate["channels"]),
            candidate["channels"],
        ),
    )
    if not point_identifying:
        raise ValidationError("declared channels cannot identify a point world")

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "dimension_count": len(problem.dimensions),
        "world_count": len(worlds),
        "channel_count": len(problem.channels),
        "candidate_count": len(candidates),
        "target_maximum_width": problem.target_maximum_width,
        "dimensions": [
            {
                "id": dimension.id,
                "baseline": dimension.baseline,
                "alternative": dimension.alternative,
                "alternative_effect": dimension.alternative_effect,
            }
            for dimension in problem.dimensions
        ],
        "interactions": [
            {
                "requires": list(interaction.requires),
                "effect": interaction.effect,
            }
            for interaction in problem.interactions
        ],
        "worlds": worlds,
        "no_evidence": candidates[0],
        "synthesis": {
            "selected": selected,
            "optimal_sets": [
                candidate for candidate in feasible
                if candidate["cost"] == selected["cost"]
            ],
            "lower_cost_failures": lower_cost_failures,
        },
        "minimum_point_identification": point_identifying[0],
        "shapley_revision_attribution": _shapley(problem),
        "dimension_flip_effects": _flip_effects(problem),
        "refinement_checks": _refinement_checks(candidates),
        "interpretation": {
            "version_space": (
                "all data, model, search, execution, and universe worlds "
                "not excluded by selected evidence"
            ),
            "certifiable_range": (
                "minimum and maximum metric across the admissible world family"
            ),
            "shapley": (
                "order-independent attribution of the baseline-to-all-"
                "alternative metric change, including declared interactions"
            ),
        },
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "research-version-space report does not match exact recomputation"
        )
    return expected
