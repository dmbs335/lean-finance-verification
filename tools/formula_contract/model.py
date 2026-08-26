from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError

SCHEMA = "lfv-formula-contract-v1"
HEX_256 = re.compile(r"^[0-9a-f]{64}$")
INPUT_ROLES = {"current_risk", "hedge_risk", "risk_percentage"}
RISK_UNITS = {"usd_risk", "eur_risk", "risk_units"}


@dataclass(frozen=True)
class FormulaDefinition:
    id: str
    kind: str
    expression_sha256: str
    implementation_sha256: str
    output_unit: str


@dataclass(frozen=True)
class FormulaInput:
    role: str
    artifact_sha256: str
    available_at: int
    valuation_at: int
    model_id: str
    model_version: str
    unit: str
    value: int


@dataclass(frozen=True)
class ClaimedResult:
    numerator: int
    denominator: int


@dataclass(frozen=True)
class Application:
    id: str
    decision_at: int
    formula_id: str
    expression_sha256: str
    implementation_sha256: str
    inputs: dict[str, FormulaInput]
    claimed_result: ClaimedResult


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    formula: FormulaDefinition
    applications: tuple[Application, ...]


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def _hash(value: Any, path: str) -> str:
    result = _string(value, path)
    if not HEX_256.fullmatch(result):
        raise ValidationError(f"{path}: expected lowercase SHA-256")
    return result


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path}: expected integer")
    return value


def _natural(value: Any, path: str) -> int:
    result = _integer(value, path)
    if result < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return result


def _formula(value: Any) -> FormulaDefinition:
    obj = _object(value, "$.formula")
    expected = {
        "id", "kind", "expression_sha256", "implementation_sha256",
        "output_unit",
    }
    if set(obj) != expected:
        raise ValidationError("$.formula: fields do not match formula schema")
    kind = _string(obj["kind"], "$.formula.kind")
    if kind != "hedge_scale_percent_v1":
        raise ValidationError("$.formula.kind: unsupported formula kind")
    output_unit = _string(obj["output_unit"], "$.formula.output_unit")
    if output_unit != "scalar":
        raise ValidationError("$.formula.output_unit: expected scalar")
    return FormulaDefinition(
        id=_string(obj["id"], "$.formula.id"),
        kind=kind,
        expression_sha256=_hash(
            obj["expression_sha256"], "$.formula.expression_sha256"
        ),
        implementation_sha256=_hash(
            obj["implementation_sha256"],
            "$.formula.implementation_sha256",
        ),
        output_unit=output_unit,
    )


def _input(value: Any, path: str) -> FormulaInput:
    obj = _object(value, path)
    expected = {
        "role", "artifact_sha256", "available_at", "valuation_at",
        "model_id", "model_version", "unit", "value",
    }
    if set(obj) != expected:
        raise ValidationError(f"{path}: fields do not match input schema")
    role = _string(obj["role"], f"{path}.role")
    if role not in INPUT_ROLES:
        raise ValidationError(f"{path}.role: unsupported role {role}")
    return FormulaInput(
        role=role,
        artifact_sha256=_hash(
            obj["artifact_sha256"], f"{path}.artifact_sha256"
        ),
        available_at=_natural(obj["available_at"], f"{path}.available_at"),
        valuation_at=_natural(obj["valuation_at"], f"{path}.valuation_at"),
        model_id=_string(obj["model_id"], f"{path}.model_id"),
        model_version=_string(
            obj["model_version"], f"{path}.model_version"
        ),
        unit=_string(obj["unit"], f"{path}.unit"),
        value=_integer(obj["value"], f"{path}.value"),
    )


def load_problem(path: Path) -> Problem:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    if set(raw) != {"schema_version", "name", "formula", "applications"}:
        raise ValidationError("$: fields do not match formula-contract schema")
    if raw["schema_version"] != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")
    formula = _formula(raw["formula"])

    applications_raw = raw["applications"]
    if not isinstance(applications_raw, list) or not applications_raw:
        raise ValidationError("$.applications: expected non-empty array")
    applications: list[Application] = []
    for index, item in enumerate(applications_raw):
        item_path = f"$.applications[{index}]"
        obj = _object(item, item_path)
        expected = {
            "id", "decision_at", "formula_id", "expression_sha256",
            "implementation_sha256", "inputs", "claimed_result",
        }
        if set(obj) != expected:
            raise ValidationError(
                f"{item_path}: fields do not match application schema"
            )
        inputs_raw = obj["inputs"]
        if not isinstance(inputs_raw, list):
            raise ValidationError(f"{item_path}.inputs: expected array")
        inputs = [
            _input(value, f"{item_path}.inputs[{input_index}]")
            for input_index, value in enumerate(inputs_raw)
        ]
        by_role = {value.role: value for value in inputs}
        if len(inputs) != len(by_role) or set(by_role) != INPUT_ROLES:
            raise ValidationError(
                f"{item_path}.inputs: expected each registered role exactly once"
            )
        result_raw = _object(
            obj["claimed_result"], f"{item_path}.claimed_result"
        )
        if set(result_raw) != {"numerator", "denominator"}:
            raise ValidationError(
                f"{item_path}.claimed_result: fields do not match"
            )
        applications.append(
            Application(
                id=_string(obj["id"], f"{item_path}.id"),
                decision_at=_natural(
                    obj["decision_at"], f"{item_path}.decision_at"
                ),
                formula_id=_string(
                    obj["formula_id"], f"{item_path}.formula_id"
                ),
                expression_sha256=_hash(
                    obj["expression_sha256"],
                    f"{item_path}.expression_sha256",
                ),
                implementation_sha256=_hash(
                    obj["implementation_sha256"],
                    f"{item_path}.implementation_sha256",
                ),
                inputs=by_role,
                claimed_result=ClaimedResult(
                    numerator=_integer(
                        result_raw["numerator"],
                        f"{item_path}.claimed_result.numerator",
                    ),
                    denominator=_integer(
                        result_raw["denominator"],
                        f"{item_path}.claimed_result.denominator",
                    ),
                ),
            )
        )
    if len({item.id for item in applications}) != len(applications):
        raise ValidationError("$.applications: ids must be unique")
    return Problem(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        formula=formula,
        applications=tuple(applications),
    )
