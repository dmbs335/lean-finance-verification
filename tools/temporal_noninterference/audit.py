from __future__ import annotations

import hashlib
from fractions import Fraction
from itertools import combinations
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .engine import (
    apply_operations,
    availability_violations,
    causal_prefix,
    evaluate_engine,
    operation_to_json,
    point_to_json,
)
from .errors import ValidationError
from .model import EngineSpec, Mutation, Operation, Problem

REPORT_SCHEMA = "lfv-temporal-noninterference-report-v1"


def _fraction_from_json(value: dict[str, int] | None) -> Fraction | None:
    if value is None:
        return None
    return Fraction(value["numerator"], value["denominator"])


def _fraction_to_json(value: Fraction) -> dict[str, int]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
    }


def _prefix_equivalence(
    problem: Problem,
    mutated_points,
) -> list[dict[str, Any]]:
    return [
        {
            "decision_time": decision_time,
            "equivalent": (
                causal_prefix(problem.points, decision_time)
                == causal_prefix(mutated_points, decision_time)
            ),
        }
        for decision_time in problem.decision_times
    ]


def _output_distance(
    baseline: list[dict[str, Any]],
    mutated: list[dict[str, Any]],
) -> dict[str, Any]:
    changed = 0
    missing_mismatch = 0
    position_l1 = 0
    mark_l1 = Fraction(0)
    for left, right in zip(baseline, mutated, strict=True):
        if left != right:
            changed += 1
        if (left["status"] == "missing") != (right["status"] == "missing"):
            missing_mismatch += 1
        left_position = left["position"]
        right_position = right["position"]
        if left_position is not None and right_position is not None:
            position_l1 += abs(left_position - right_position)
        left_mark = _fraction_from_json(left["mark"])
        right_mark = _fraction_from_json(right["mark"])
        if left_mark is not None and right_mark is not None:
            mark_l1 += abs(left_mark - right_mark)
    return {
        "changed_decision_count": changed,
        "missing_status_mismatch_count": missing_mismatch,
        "position_l1": position_l1,
        "mark_l1": _fraction_to_json(mark_l1),
    }


def _first_divergence(
    baseline: list[dict[str, Any]],
    mutated: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for left, right in zip(baseline, mutated, strict=True):
        if left != right:
            return {
                "decision_time": left["decision_time"],
                "baseline": left,
                "mutated": right,
            }
    return None


def _mutation_result(
    problem: Problem,
    engine: EngineSpec,
    baseline_outputs: list[dict[str, Any]],
    mutation: Mutation,
    operations: tuple[Operation, ...] | None = None,
) -> dict[str, Any]:
    applied_operations = mutation.operations if operations is None else operations
    mutated_points = apply_operations(problem.points, applied_operations)
    outputs, source_mutated, final_points = evaluate_engine(
        engine, mutated_points, problem.decision_times
    )
    prefix_by_decision = _prefix_equivalence(problem, mutated_points)
    prefix_equivalent = all(
        item["equivalent"] for item in prefix_by_decision
    )
    outputs_equal = outputs == baseline_outputs
    return {
        "mutation": mutation.id,
        "description": mutation.description,
        "operations": [
            operation_to_json(operation)
            for operation in applied_operations
        ],
        "causal_prefix_equivalence": prefix_by_decision,
        "causal_prefix_equivalent_through_cutoff": prefix_equivalent,
        "outputs": outputs,
        "outputs_equal_through_cutoff": outputs_equal,
        "temporal_noninterference_violation": (
            prefix_equivalent and not outputs_equal
        ),
        "distance": _output_distance(baseline_outputs, outputs),
        "first_divergence": _first_divergence(
            baseline_outputs, outputs
        ),
        "availability_violations": availability_violations(
            outputs, final_points
        ),
        "source_mutated": source_mutated,
        "mutated_source_order": [
            point.id for point in final_points
        ],
    }


def _minimal_violation_witness(
    problem: Problem,
    engine: EngineSpec,
    baseline_outputs: list[dict[str, Any]],
    mutation: Mutation,
) -> dict[str, Any] | None:
    operation_count = len(mutation.operations)
    for size in range(1, operation_count + 1):
        for indexes in combinations(range(operation_count), size):
            subset = tuple(mutation.operations[index] for index in indexes)
            result = _mutation_result(
                problem, engine, baseline_outputs, mutation, subset
            )
            if result["temporal_noninterference_violation"]:
                return {
                    "operation_indexes": list(indexes),
                    "operations": [
                        operation_to_json(operation)
                        for operation in subset
                    ],
                    "first_divergence": result["first_divergence"],
                }
    return None


def _audit_engine(
    problem: Problem,
    engine: EngineSpec,
) -> dict[str, Any]:
    baseline_outputs, baseline_source_mutated, baseline_final_points = (
        evaluate_engine(engine, problem.points, problem.decision_times)
    )
    baseline_availability = availability_violations(
        baseline_outputs, baseline_final_points
    )
    mutation_results: list[dict[str, Any]] = []
    for mutation in problem.mutations:
        result = _mutation_result(
            problem, engine, baseline_outputs, mutation
        )
        result["minimal_violation_witness"] = (
            _minimal_violation_witness(
                problem, engine, baseline_outputs, mutation
            )
            if result["temporal_noninterference_violation"]
            else None
        )
        mutation_results.append(result)

    temporal_violations = [
        result
        for result in mutation_results
        if result["temporal_noninterference_violation"]
    ]
    source_mutation_observed = (
        baseline_source_mutated
        or any(result["source_mutated"] for result in mutation_results)
    )
    contract_passes = (
        not temporal_violations
        and not baseline_availability
        and not source_mutation_observed
    )
    return {
        "engine": engine.id,
        "semantics": engine.semantics,
        "threshold": engine.threshold,
        "baseline": {
            "source_order": [point.id for point in problem.points],
            "final_source_order": [
                point.id for point in baseline_final_points
            ],
            "source_mutated": baseline_source_mutated,
            "outputs": baseline_outputs,
            "availability_violations": baseline_availability,
        },
        "mutations": mutation_results,
        "summary": {
            "temporal_noninterference_violation_count": len(
                temporal_violations
            ),
            "availability_violation_count": len(
                baseline_availability
            ),
            "source_mutation_observed": source_mutation_observed,
            "contract_passes": contract_passes,
        },
    }


def audit(problem: Problem) -> dict[str, Any]:
    engine_audits = [
        _audit_engine(problem, engine)
        for engine in problem.engines
    ]
    safe_engines = [
        audit["engine"]
        for audit in engine_audits
        if audit["summary"]["contract_passes"]
    ]
    unsafe_engines = [
        audit["engine"]
        for audit in engine_audits
        if not audit["summary"]["contract_passes"]
    ]
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "cutoff_time": problem.cutoff_time,
        "decision_times": list(problem.decision_times),
        "base_points": [
            point_to_json(point)
            for point in problem.points
        ],
        "causal_prefixes": [
            {
                "decision_time": decision_time,
                "point_ids": [
                    item[0]
                    for item in causal_prefix(
                        problem.points, decision_time
                    )
                ],
            }
            for decision_time in problem.decision_times
        ],
        "engine_count": len(problem.engines),
        "mutation_count": len(problem.mutations),
        "engine_audits": engine_audits,
        "aggregate": {
            "safe_engines": safe_engines,
            "unsafe_engines": unsafe_engines,
            "temporal_violation_engine_count": sum(
                audit["summary"][
                    "temporal_noninterference_violation_count"
                ] > 0
                for audit in engine_audits
            ),
            "availability_violation_engine_count": sum(
                audit["summary"]["availability_violation_count"] > 0
                for audit in engine_audits
            ),
            "source_mutation_engine_count": sum(
                audit["summary"]["source_mutation_observed"]
                for audit in engine_audits
            ),
        },
        "contracts": {
            "temporal_noninterference": (
                "equal causal prefixes at every decision imply equal "
                "output prefixes through the cutoff"
            ),
            "strict_availability": (
                "every selected observation and availability timestamp "
                "is at or before the decision"
            ),
            "source_immutability": (
                "evaluating the engine does not mutate the supplied "
                "point sequence"
            ),
        },
        "interpretation": (
            "controlled semantic benchmark; a violation proves one "
            "engine implementation is sensitive to causally unavailable "
            "or representation-only changes under this finite model, "
            "not that every external backtest using a similar API fails"
        ),
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = audit(problem)
    if report != expected:
        raise ValidationError(
            "temporal-noninterference report does not match exact "
            "recomputation"
        )
    return expected
