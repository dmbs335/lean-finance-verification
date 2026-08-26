from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-pnl-explain-closure-v1"
STATUSES = {"CLOSED", "PARTIAL", "OPEN"}


@dataclass(frozen=True)
class UpstreamReference:
    repository: str
    branch: str
    commit: str
    release: str
    module: str
    symbol: str
    coverage_status: str


@dataclass(frozen=True)
class Binding:
    portfolio_hash: str
    market_data_before_hash: str
    market_data_after_hash: str
    model_id: str
    model_version: str
    valuation_before: int
    valuation_after: int


@dataclass(frozen=True)
class Factor:
    id: str
    base_value_units: int
    first_sensitivity: int
    half_second_sensitivity: int
    market_move: int
    claimed_first_order_pnl: int
    claimed_second_order_pnl: int
    available_at: int
    binding: Binding


@dataclass(frozen=True)
class NonMarket:
    carry: int
    trades: int
    cashflows: int
    transaction_cost: int
    model_revision: int


@dataclass(frozen=True)
class Result:
    realized_pnl: int
    generated_at: int
    binding: Binding


@dataclass(frozen=True)
class Case:
    id: str
    decision_at: int
    tolerance_units: int
    expected_status: str
    pipeline_binding: Binding
    factors: tuple[Factor, ...]
    non_market: NonMarket
    result: Result


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    pnl_unit: str
    upstream_reference: UpstreamReference
    cases: tuple[Case, ...]


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
    if not -(10**15) <= value <= 10**15:
        raise ValidationError(f"{path}: integer outside controlled range")
    return value


def _natural(value: Any, path: str) -> int:
    result = _integer(value, path)
    if result < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return result


def _binding(value: Any, path: str) -> Binding:
    obj = _object(value, path)
    expected = {
        "portfolio_hash", "market_data_before_hash", "market_data_after_hash",
        "model_id", "model_version", "valuation_before", "valuation_after",
    }
    if set(obj) != expected:
        raise ValidationError(f"{path}: fields do not match binding schema")
    before = _natural(obj["valuation_before"], f"{path}.valuation_before")
    after = _natural(obj["valuation_after"], f"{path}.valuation_after")
    if before > after:
        raise ValidationError(f"{path}: valuation interval is reversed")
    return Binding(
        portfolio_hash=_string(obj["portfolio_hash"], f"{path}.portfolio_hash"),
        market_data_before_hash=_string(
            obj["market_data_before_hash"],
            f"{path}.market_data_before_hash",
        ),
        market_data_after_hash=_string(
            obj["market_data_after_hash"],
            f"{path}.market_data_after_hash",
        ),
        model_id=_string(obj["model_id"], f"{path}.model_id"),
        model_version=_string(
            obj["model_version"], f"{path}.model_version"
        ),
        valuation_before=before,
        valuation_after=after,
    )


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    expected = {
        "schema_version", "name", "pnl_unit", "upstream_reference", "cases"
    }
    if set(raw) != expected or raw["schema_version"] != SCHEMA:
        raise ValidationError("$: fields or schema do not match")

    upstream_raw = _object(raw["upstream_reference"], "$.upstream_reference")
    upstream_fields = {
        "repository", "branch", "commit", "release", "module", "symbol",
        "coverage_status",
    }
    if set(upstream_raw) != upstream_fields:
        raise ValidationError("$.upstream_reference: fields do not match")
    coverage_status = _string(
        upstream_raw["coverage_status"],
        "$.upstream_reference.coverage_status",
    )
    if coverage_status != "STATIC_REVIEW_THEORY_MAPPED":
        raise ValidationError(
            "$.upstream_reference.coverage_status must not overclaim execution"
        )
    upstream = UpstreamReference(
        repository=_string(
            upstream_raw["repository"], "$.upstream_reference.repository"
        ),
        branch=_string(upstream_raw["branch"], "$.upstream_reference.branch"),
        commit=_string(upstream_raw["commit"], "$.upstream_reference.commit"),
        release=_string(upstream_raw["release"], "$.upstream_reference.release"),
        module=_string(upstream_raw["module"], "$.upstream_reference.module"),
        symbol=_string(upstream_raw["symbol"], "$.upstream_reference.symbol"),
        coverage_status=coverage_status,
    )

    cases_raw = raw["cases"]
    if not isinstance(cases_raw, list) or not cases_raw:
        raise ValidationError("$.cases: expected non-empty array")
    cases: list[Case] = []
    for case_index, item in enumerate(cases_raw):
        case_path = f"$.cases[{case_index}]"
        obj = _object(item, case_path)
        expected_case = {
            "id", "decision_at", "tolerance_units", "expected_status",
            "pipeline_binding", "factors", "non_market", "result",
        }
        if set(obj) != expected_case:
            raise ValidationError(f"{case_path}: fields do not match case schema")
        factors_raw = obj["factors"]
        if not isinstance(factors_raw, list) or not factors_raw:
            raise ValidationError(f"{case_path}.factors: expected non-empty array")
        factors: list[Factor] = []
        for factor_index, factor_item in enumerate(factors_raw):
            factor_path = f"{case_path}.factors[{factor_index}]"
            factor_obj = _object(factor_item, factor_path)
            expected_factor = {
                "id", "base_value_units", "first_sensitivity",
                "half_second_sensitivity", "market_move",
                "claimed_first_order_pnl", "claimed_second_order_pnl",
                "available_at", "binding",
            }
            if set(factor_obj) != expected_factor:
                raise ValidationError(
                    f"{factor_path}: fields do not match factor schema"
                )
            factors.append(Factor(
                id=_string(factor_obj["id"], f"{factor_path}.id"),
                base_value_units=_integer(
                    factor_obj["base_value_units"],
                    f"{factor_path}.base_value_units",
                ),
                first_sensitivity=_integer(
                    factor_obj["first_sensitivity"],
                    f"{factor_path}.first_sensitivity",
                ),
                half_second_sensitivity=_integer(
                    factor_obj["half_second_sensitivity"],
                    f"{factor_path}.half_second_sensitivity",
                ),
                market_move=_integer(
                    factor_obj["market_move"],
                    f"{factor_path}.market_move",
                ),
                claimed_first_order_pnl=_integer(
                    factor_obj["claimed_first_order_pnl"],
                    f"{factor_path}.claimed_first_order_pnl",
                ),
                claimed_second_order_pnl=_integer(
                    factor_obj["claimed_second_order_pnl"],
                    f"{factor_path}.claimed_second_order_pnl",
                ),
                available_at=_natural(
                    factor_obj["available_at"],
                    f"{factor_path}.available_at",
                ),
                binding=_binding(factor_obj["binding"], f"{factor_path}.binding"),
            ))
        factor_ids = [factor.id for factor in factors]
        if len(set(factor_ids)) != len(factor_ids):
            raise ValidationError(f"{case_path}.factors: ids must be unique")

        non_market_obj = _object(obj["non_market"], f"{case_path}.non_market")
        non_market_fields = {
            "carry", "trades", "cashflows", "transaction_cost", "model_revision"
        }
        if set(non_market_obj) != non_market_fields:
            raise ValidationError(
                f"{case_path}.non_market: fields do not match"
            )
        non_market = NonMarket(**{
            field: _integer(
                non_market_obj[field], f"{case_path}.non_market.{field}"
            )
            for field in non_market_fields
        })

        result_obj = _object(obj["result"], f"{case_path}.result")
        if set(result_obj) != {"realized_pnl", "generated_at", "binding"}:
            raise ValidationError(f"{case_path}.result: fields do not match")
        status = _string(obj["expected_status"], f"{case_path}.expected_status")
        if status not in STATUSES:
            raise ValidationError(f"{case_path}.expected_status: unsupported status")
        cases.append(Case(
            id=_string(obj["id"], f"{case_path}.id"),
            decision_at=_natural(obj["decision_at"], f"{case_path}.decision_at"),
            tolerance_units=_natural(
                obj["tolerance_units"], f"{case_path}.tolerance_units"
            ),
            expected_status=status,
            pipeline_binding=_binding(
                obj["pipeline_binding"], f"{case_path}.pipeline_binding"
            ),
            factors=tuple(factors),
            non_market=non_market,
            result=Result(
                realized_pnl=_integer(
                    result_obj["realized_pnl"],
                    f"{case_path}.result.realized_pnl",
                ),
                generated_at=_natural(
                    result_obj["generated_at"],
                    f"{case_path}.result.generated_at",
                ),
                binding=_binding(
                    result_obj["binding"], f"{case_path}.result.binding"
                ),
            ),
        ))
    case_ids = [case.id for case in cases]
    if len(set(case_ids)) != len(case_ids):
        raise ValidationError("$.cases: ids must be unique")
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        pnl_unit=_string(raw["pnl_unit"], "$.pnl_unit"),
        upstream_reference=upstream,
        cases=tuple(cases),
    )
