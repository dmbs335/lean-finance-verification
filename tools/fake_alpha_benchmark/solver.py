from __future__ import annotations

import hashlib
from itertools import combinations
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Benchmark, Experiment

REPORT_SCHEMA = "lfv-fake-alpha-benchmark-report-v1"


def _detected_kinds(benchmark: Benchmark, selected: tuple[str, ...]) -> set[str]:
    selected_set = set(selected)
    result: set[str] = set()
    for channel in benchmark.channels:
        if channel.id in selected_set:
            result.update(channel.detects)
    return result


def _evaluate_experiment(
    experiment: Experiment,
    detected_kinds: set[str],
) -> dict[str, Any]:
    detected = [
        distortion for distortion in experiment.distortions
        if distortion.kind in detected_kinds
    ]
    unresolved = [
        distortion for distortion in experiment.distortions
        if distortion.kind not in detected_kinds
    ]
    detected_inflation = sum(item.inflation_bps for item in detected)
    unresolved_inflation = sum(item.inflation_bps for item in unresolved)
    corrected = experiment.observed_alpha_bps - detected_inflation
    return {
        "experiment": experiment.id,
        "clean_alpha_bps": experiment.clean_alpha_bps,
        "observed_alpha_bps": experiment.observed_alpha_bps,
        "detected_distortions": [item.kind for item in detected],
        "unresolved_distortions": [item.kind for item in unresolved],
        "detected_inflation_bps": detected_inflation,
        "residual_inflation_bps": unresolved_inflation,
        "certifiable_interval_bps": [
            experiment.clean_alpha_bps,
            corrected,
        ],
        "interval_width_bps": unresolved_inflation,
        "exact_recovery": not unresolved,
    }


def _ranking(values: dict[str, int]) -> list[str]:
    return [
        experiment_id
        for experiment_id, _value in sorted(
            values.items(), key=lambda item: (-item[1], item[0])
        )
    ]


def _discordant_pairs(left: list[str], right: list[str]) -> int:
    left_index = {value: index for index, value in enumerate(left)}
    right_index = {value: index for index, value in enumerate(right)}
    values = sorted(left_index)
    return sum(
        1
        for first, second in combinations(values, 2)
        if (left_index[first] < left_index[second])
        != (right_index[first] < right_index[second])
    )


def _candidate(
    benchmark: Benchmark,
    mask: int,
    clean_ranking: list[str],
) -> dict[str, Any]:
    selected = tuple(
        channel.id
        for index, channel in enumerate(benchmark.channels)
        if mask & (1 << index)
    )
    selected_set = set(selected)
    cost = sum(
        channel.cost for channel in benchmark.channels
        if channel.id in selected_set
    )
    detected_kinds = _detected_kinds(benchmark, selected)
    evaluations = [
        _evaluate_experiment(experiment, detected_kinds)
        for experiment in benchmark.experiments
    ]
    unresolved = next(
        (
            evaluation
            for evaluation in evaluations
            if not evaluation["exact_recovery"]
        ),
        None,
    )
    corrected_values = {
        evaluation["experiment"]: evaluation["certifiable_interval_bps"][1]
        for evaluation in evaluations
    }
    corrected_ranking = _ranking(corrected_values)
    candidate: dict[str, Any] = {
        "mask": mask,
        "channels": list(selected),
        "cost": cost,
        "detected_kinds": sorted(detected_kinds),
        "verifies": unresolved is None,
        "corrected_ranking": corrected_ranking,
        "ranking_discordance": _discordant_pairs(
            clean_ranking, corrected_ranking
        ),
        "evaluations": evaluations,
    }
    if unresolved is not None:
        candidate["uncovered"] = {
            "experiment": unresolved["experiment"],
            "unresolved_distortions": unresolved[
                "unresolved_distortions"
            ],
            "residual_inflation_bps": unresolved[
                "residual_inflation_bps"
            ],
        }
    return candidate


def solve(benchmark: Benchmark) -> dict[str, Any]:
    clean_values = {
        experiment.id: experiment.clean_alpha_bps
        for experiment in benchmark.experiments
    }
    observed_values = {
        experiment.id: experiment.observed_alpha_bps
        for experiment in benchmark.experiments
    }
    clean_ranking = _ranking(clean_values)
    observed_ranking = _ranking(observed_values)
    candidates = [
        _candidate(benchmark, mask, clean_ranking)
        for mask in range(1 << len(benchmark.channels))
    ]
    verifying = sorted(
        (candidate for candidate in candidates if candidate["verifies"]),
        key=lambda item: (
            item["cost"], len(item["channels"]), item["channels"]
        ),
    )
    if not verifying:
        raise ValidationError(
            "no evidence selection detects every declared distortion"
        )
    selected = verifying[0]
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": benchmark.name,
        "experiment_count": len(benchmark.experiments),
        "channel_count": len(benchmark.channels),
        "ground_truth": {
            "clean_ranking": clean_ranking,
            "observed_ranking": observed_ranking,
            "clean_top": clean_ranking[0],
            "observed_top": observed_ranking[0],
            "observed_ranking_discordance": _discordant_pairs(
                clean_ranking, observed_ranking
            ),
        },
        "synthesis": {
            "candidate_count": len(candidates),
            "selected": selected,
            "optimal_sets": [
                candidate
                for candidate in verifying
                if candidate["cost"] == selected["cost"]
            ],
            "lower_cost_failures": [
                candidate
                for candidate in candidates
                if candidate["cost"] < selected["cost"]
            ],
        },
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(benchmark: Benchmark, report: Any) -> dict[str, Any]:
    expected = solve(benchmark)
    if report != expected:
        raise ValidationError(
            "fake-alpha report does not match exact recomputation"
        )
    return expected
