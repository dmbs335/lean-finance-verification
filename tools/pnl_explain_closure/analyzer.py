from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Binding, Case, Factor, Problem

REPORT_SCHEMA = "lfv-pnl-explain-closure-report-v1"


def _binding_dict(binding: Binding) -> dict[str, Any]:
    return asdict(binding)


def _factor_result(factor: Factor, case: Case) -> dict[str, Any]:
    expected_first = factor.first_sensitivity * factor.market_move
    expected_second = (
        factor.half_second_sensitivity
        * factor.market_move
        * factor.market_move
    )
    formula_valid = (
        factor.claimed_first_order_pnl == expected_first
        and factor.claimed_second_order_pnl == expected_second
    )
    temporal_valid = (
        factor.available_at <= case.decision_at
        and factor.binding.valuation_before
        <= factor.binding.valuation_after
        <= case.decision_at
    )
    binding_valid = factor.binding == case.pipeline_binding
    return {
        "id": factor.id,
        "base_value_units": factor.base_value_units,
        "market_move": factor.market_move,
        "expected_first_order_pnl": expected_first,
        "expected_second_order_pnl": expected_second,
        "claimed_first_order_pnl": factor.claimed_first_order_pnl,
        "claimed_second_order_pnl": factor.claimed_second_order_pnl,
        "claimed_explained_pnl": (
            factor.claimed_first_order_pnl
            + factor.claimed_second_order_pnl
        ),
        "modeled_after_value_units": (
            factor.base_value_units + expected_first + expected_second
        ),
        "formula_valid": formula_valid,
        "temporal_valid": temporal_valid,
        "binding_valid": binding_valid,
        "available_at": factor.available_at,
        "binding": _binding_dict(factor.binding),
    }


def _analyze_case(case: Case) -> dict[str, Any]:
    factors = [_factor_result(factor, case) for factor in case.factors]
    market_explained = sum(
        factor["claimed_explained_pnl"] for factor in factors
    )
    non_market = case.non_market
    non_market_total = (
        non_market.carry
        + non_market.trades
        + non_market.cashflows
        - non_market.transaction_cost
        + non_market.model_revision
    )
    reconstructed = market_explained + non_market_total
    residual = case.result.realized_pnl - reconstructed
    formulas_valid = all(factor["formula_valid"] for factor in factors)
    factors_temporal = all(factor["temporal_valid"] for factor in factors)
    factor_bindings = all(factor["binding_valid"] for factor in factors)
    result_binding = case.result.binding == case.pipeline_binding
    result_temporal = case.result.generated_at <= case.decision_at
    local_and_binding_valid = (
        formulas_valid
        and factors_temporal
        and factor_bindings
        and result_binding
        and result_temporal
    )
    residual_within = abs(residual) <= case.tolerance_units
    if not local_and_binding_valid:
        status = "OPEN"
    elif residual_within:
        status = "CLOSED"
    else:
        status = "PARTIAL"

    reasons: list[str] = []
    invalid_formulas = [
        factor["id"] for factor in factors if not factor["formula_valid"]
    ]
    unavailable = [
        factor["id"] for factor in factors if not factor["temporal_valid"]
    ]
    mismatched = [
        factor["id"] for factor in factors if not factor["binding_valid"]
    ]
    if invalid_formulas:
        reasons.append(f"formula mismatch: {invalid_formulas}")
    if unavailable:
        reasons.append(f"temporal mismatch: {unavailable}")
    if mismatched:
        reasons.append(f"factor binding mismatch: {mismatched}")
    if not result_binding:
        reasons.append("realized result binding mismatch")
    if not result_temporal:
        reasons.append("realized result generated after decision")
    if local_and_binding_valid and not residual_within:
        reasons.append(
            f"material residual {residual} exceeds tolerance "
            f"{case.tolerance_units}"
        )
    if status != case.expected_status:
        raise ValidationError(
            f"case {case.id}: expected {case.expected_status}, computed {status}"
        )

    return {
        "id": case.id,
        "status": status,
        "expected_status": case.expected_status,
        "decision_at": case.decision_at,
        "tolerance_units": case.tolerance_units,
        "pipeline_binding": _binding_dict(case.pipeline_binding),
        "factors": factors,
        "non_market": asdict(non_market),
        "non_market_total_pnl": non_market_total,
        "market_explained_pnl": market_explained,
        "reconstructed_pnl": reconstructed,
        "realized_pnl": case.result.realized_pnl,
        "residual": residual,
        "residual_abs": abs(residual),
        "residual_within_tolerance": residual_within,
        "local_formulas_valid": formulas_valid,
        "factors_temporally_valid": factors_temporal,
        "factor_bindings_valid": factor_bindings,
        "result_binding_valid": result_binding,
        "result_temporally_valid": result_temporal,
        "local_and_binding_valid": local_and_binding_valid,
        "reasons": reasons,
        "constructive_binding_counterexample": (
            {
                "locally_valid_factor_ids": [
                    factor["id"]
                    for factor in factors
                    if factor["formula_valid"]
                ],
                "mismatched_factor_ids": mismatched,
                "expected_binding": _binding_dict(case.pipeline_binding),
            }
            if mismatched and formulas_valid
            else None
        ),
    }


def analyze(problem: Problem) -> dict[str, Any]:
    cases = [_analyze_case(case) for case in problem.cases]
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": problem.name,
        "pnl_unit": problem.pnl_unit,
        "upstream_reference": asdict(problem.upstream_reference),
        "case_count": len(cases),
        "cases": cases,
        "aggregate": {
            "closed_count": sum(case["status"] == "CLOSED" for case in cases),
            "partial_count": sum(case["status"] == "PARTIAL" for case in cases),
            "open_count": sum(case["status"] == "OPEN" for case in cases),
            "formula_failure_count": sum(
                not case["local_formulas_valid"] for case in cases
            ),
            "binding_failure_count": sum(
                not case["factor_bindings_valid"]
                or not case["result_binding_valid"]
                for case in cases
            ),
            "temporal_failure_count": sum(
                not case["factors_temporally_valid"]
                or not case["result_temporally_valid"]
                for case in cases
            ),
            "material_residual_count": sum(
                case["local_and_binding_valid"]
                and not case["residual_within_tolerance"]
                for case in cases
            ),
        },
        "assurance": {
            "lean": (
                "exact arithmetic of the declared local quadratic model and "
                "closure-certificate consequences"
            ),
            "python": (
                "exact finite recomputation of formula, time, binding, and "
                "residual gates"
            ),
            "upstream": (
                "static review and theory mapping only; the GS Quant runtime "
                "is not directly executed by this fixture"
            ),
        },
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(problem: Problem, report: Any) -> dict[str, Any]:
    expected = analyze(problem)
    if report != expected:
        raise ValidationError(
            "PnL-explain closure report does not match exact recomputation"
        )
    return expected
