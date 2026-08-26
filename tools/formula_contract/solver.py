from __future__ import annotations

import hashlib
from fractions import Fraction
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Problem, RISK_UNITS

REPORT_SCHEMA = "lfv-formula-contract-report-v1"


def _fraction(value: Fraction | None) -> list[int] | None:
    if value is None:
        return None
    return [value.numerator, value.denominator]


def _application(problem: Problem, application) -> dict[str, Any]:
    current = application.inputs["current_risk"]
    hedge = application.inputs["hedge_risk"]
    percentage = application.inputs["risk_percentage"]

    definition_matched = (
        application.formula_id == problem.formula.id
        and application.expression_sha256 == problem.formula.expression_sha256
        and application.implementation_sha256
        == problem.formula.implementation_sha256
    )
    definition_available = (
        problem.formula.registered_at <= application.decision_at
    )
    inputs_available = all(
        value.available_at <= application.decision_at
        for value in application.inputs.values()
    )
    valuations_not_future = all(
        value.valuation_at <= application.decision_at
        for value in application.inputs.values()
    )
    output_available = (
        application.output_generated_at <= application.decision_at
    )
    units_valid = (
        current.unit == hedge.unit
        and current.unit in RISK_UNITS
        and percentage.unit == "percent"
    )
    valuation_aligned = current.valuation_at == hedge.valuation_at
    model_aligned = (
        current.model_id == hedge.model_id
        and current.model_version == hedge.model_version
    )
    domain_valid = (
        hedge.value != 0 and application.claimed_result.denominator != 0
    )

    computed = None
    if hedge.value != 0:
        computed = Fraction(
            -current.value * percentage.value,
            hedge.value * 100,
        )
    claimed = None
    if application.claimed_result.denominator != 0:
        claimed = Fraction(
            application.claimed_result.numerator,
            application.claimed_result.denominator,
        )
    result_bound = computed is not None and claimed == computed
    checks = {
        "definition_matched": definition_matched,
        "definition_available": definition_available,
        "inputs_available": inputs_available,
        "valuations_not_future": valuations_not_future,
        "output_available": output_available,
        "units_valid": units_valid,
        "valuation_aligned": valuation_aligned,
        "model_aligned": model_aligned,
        "domain_valid": domain_valid,
        "artifacts_bound": True,
        "result_bound": result_bound,
    }
    passed = all(checks.values())
    failed = [name for name, value in checks.items() if not value]
    row: dict[str, Any] = {
        "application": application.id,
        "decision_at": application.decision_at,
        "checks": checks,
        "failed_obligations": failed,
        "computed_result": _fraction(computed),
        "claimed_result": _fraction(claimed),
        "passes": passed,
        "formula_correct_but_application_invalid": (
            definition_matched and result_bound and not passed
        ),
        "input_artifacts": {
            role: value.artifact_sha256
            for role, value in sorted(application.inputs.items())
        },
        "output_artifact_sha256": application.output_artifact_sha256,
    }
    row["certificate"] = (
        {
            "formula_id": problem.formula.id,
            "expression_sha256": problem.formula.expression_sha256,
            "implementation_sha256": problem.formula.implementation_sha256,
            "registered_at": problem.formula.registered_at,
            "application_id": application.id,
            "decision_at": application.decision_at,
            "input_artifacts": row["input_artifacts"],
            "output_artifact_sha256": application.output_artifact_sha256,
            "exact_result": row["computed_result"],
            "output_unit": problem.formula.output_unit,
        }
        if passed
        else None
    )
    return row


def solve(problem: Problem) -> dict[str, Any]:
    applications = [
        _application(problem, application)
        for application in problem.applications
    ]
    check_names = (
        "definition_matched",
        "definition_available",
        "inputs_available",
        "valuations_not_future",
        "output_available",
        "units_valid",
        "valuation_aligned",
        "model_aligned",
        "domain_valid",
        "artifacts_bound",
        "result_bound",
    )
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "formula": {
            "id": problem.formula.id,
            "kind": problem.formula.kind,
            "expression_sha256": problem.formula.expression_sha256,
            "implementation_sha256": problem.formula.implementation_sha256,
            "registered_at": problem.formula.registered_at,
            "output_unit": problem.formula.output_unit,
        },
        "application_count": len(applications),
        "applications": applications,
        "aggregate": {
            "valid_application_count": sum(
                1 for item in applications if item["passes"]
            ),
            "invalid_application_count": sum(
                1 for item in applications if not item["passes"]
            ),
            "definition_only_false_positive_count": sum(
                1 for item in applications
                if item["formula_correct_but_application_invalid"]
            ),
            "failure_counts": {
                name: sum(
                    1 for item in applications
                    if name in item["failed_obligations"]
                )
                for name in check_names
            },
        },
        "interpretation": (
            "an algebraically correct formula result is not a valid financial "
            "application unless preregistration, temporal, unit, valuation, "
            "model, domain, implementation, artifact, and result-binding "
            "obligations also hold"
        ),
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = solve(problem)
    if report != expected:
        raise ValidationError(
            "formula-contract report does not match exact recomputation"
        )
    return expected
