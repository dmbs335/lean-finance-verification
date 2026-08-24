from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

from .errors import ValidationError

SCHEMA = "lfv-proof-carrying-research-plan-v3"


@dataclass(frozen=True)
class AnalysisPaths:
    fake_alpha_benchmark: Path
    certifiable_alpha_interval: Path
    evidence_portfolio: Path
    certifiability_crowding: Path
    epistemic_liquidation: Path
    epistemic_event_study: Path


@dataclass(frozen=True)
class Gates:
    require_exact_alpha_recovery: bool
    maximum_certifiable_interval_width_bps: int
    require_positive_certifiable_lower_bound: bool
    minimum_adjusted_portfolio_gain: int
    require_all_crowding_laws: bool
    minimum_crowding_paradox_count: int
    minimum_hidden_common_risk_pairs: int
    require_event_study_acceptance: bool
    minimum_event_study_average_did_bps: int


@dataclass(frozen=True)
class Plan:
    source: Path
    repository_root: Path
    research_id: str
    hypothesis: str
    analyses: AnalysisPaths
    gates: Gates
    raw: dict[str, Any]

    @property
    def digest(self) -> str:
        return __import__("hashlib").sha256(canonical_bytes(self.raw)).hexdigest()


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def _natural(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return value


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path}: expected boolean")
    return value


def _repository_path(
    repository_root: Path, value: Any, path: str
) -> Path:
    relative = _string(value, path)
    candidate_relative = Path(relative)
    if candidate_relative.is_absolute() or ".." in candidate_relative.parts:
        raise ValidationError(f"{path}: path must stay inside repository root")
    candidate = (repository_root / candidate_relative).resolve()
    try:
        candidate.relative_to(repository_root)
    except ValueError as exc:
        raise ValidationError(f"{path}: path escapes repository root") from exc
    if not candidate.is_file():
        raise ValidationError(f"{path}: missing analysis input {relative}")
    return candidate


def load_plan(path: Path, repository_root: Path) -> Plan:
    repository_root = repository_root.resolve()
    raw = _object(load_json(path), "$")
    allowed = {
        "schema_version", "research_id", "hypothesis", "analyses", "gates"
    }
    unknown = set(raw) - allowed
    if unknown:
        raise ValidationError(f"$: unknown fields: {sorted(unknown)}")
    if raw.get("schema_version") != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")

    analyses_raw = _object(raw.get("analyses"), "$.analyses")
    analysis_fields = {
        "fake_alpha_benchmark", "certifiable_alpha_interval",
        "evidence_portfolio", "certifiability_crowding",
        "epistemic_liquidation", "epistemic_event_study",
    }
    if set(analyses_raw) != analysis_fields:
        raise ValidationError("$.analyses: fields do not match analysis schema")
    analyses = AnalysisPaths(**{
        field: _repository_path(
            repository_root, analyses_raw[field], f"$.analyses.{field}"
        )
        for field in analysis_fields
    })

    gates_raw = _object(raw.get("gates"), "$.gates")
    gate_fields = {
        "require_exact_alpha_recovery",
        "maximum_certifiable_interval_width_bps",
        "require_positive_certifiable_lower_bound",
        "minimum_adjusted_portfolio_gain", "require_all_crowding_laws",
        "minimum_crowding_paradox_count", "minimum_hidden_common_risk_pairs",
        "require_event_study_acceptance",
        "minimum_event_study_average_did_bps",
    }
    if set(gates_raw) != gate_fields:
        raise ValidationError("$.gates: fields do not match gate schema")
    gates = Gates(
        require_exact_alpha_recovery=_boolean(
            gates_raw["require_exact_alpha_recovery"],
            "$.gates.require_exact_alpha_recovery",
        ),
        maximum_certifiable_interval_width_bps=_natural(
            gates_raw["maximum_certifiable_interval_width_bps"],
            "$.gates.maximum_certifiable_interval_width_bps",
        ),
        require_positive_certifiable_lower_bound=_boolean(
            gates_raw["require_positive_certifiable_lower_bound"],
            "$.gates.require_positive_certifiable_lower_bound",
        ),
        minimum_adjusted_portfolio_gain=_natural(
            gates_raw["minimum_adjusted_portfolio_gain"],
            "$.gates.minimum_adjusted_portfolio_gain",
        ),
        require_all_crowding_laws=_boolean(
            gates_raw["require_all_crowding_laws"],
            "$.gates.require_all_crowding_laws",
        ),
        minimum_crowding_paradox_count=_natural(
            gates_raw["minimum_crowding_paradox_count"],
            "$.gates.minimum_crowding_paradox_count",
        ),
        minimum_hidden_common_risk_pairs=_natural(
            gates_raw["minimum_hidden_common_risk_pairs"],
            "$.gates.minimum_hidden_common_risk_pairs",
        ),
        require_event_study_acceptance=_boolean(
            gates_raw["require_event_study_acceptance"],
            "$.gates.require_event_study_acceptance",
        ),
        minimum_event_study_average_did_bps=_natural(
            gates_raw["minimum_event_study_average_did_bps"],
            "$.gates.minimum_event_study_average_did_bps",
        ),
    )
    return Plan(
        source=path.resolve(),
        repository_root=repository_root,
        research_id=_string(raw.get("research_id"), "$.research_id"),
        hypothesis=_string(raw.get("hypothesis"), "$.hypothesis"),
        analyses=analyses,
        gates=gates,
        raw=raw,
    )
