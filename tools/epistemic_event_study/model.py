from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json

from .errors import ValidationError

SCHEMA = "lfv-epistemic-event-study-v1"
DISTANCE_KEYS = ("return", "factor", "holdings", "liquidity")


@dataclass(frozen=True)
class StrategyWindow:
    id: str
    evidence_domains: tuple[str, ...]
    baseline_outflow_bps: int
    pre_event_outflow_bps: int
    post_event_outflow_bps: int


@dataclass(frozen=True)
class MatchedPair:
    id: str
    treated: StrategyWindow
    control: StrategyWindow
    conventional_distance_bps: dict[str, int]


@dataclass(frozen=True)
class Plan:
    source: Path
    name: str
    failed_domain: str
    preregistered_at: int
    event_time: int
    maximum_match_distance_bps: int
    maximum_absolute_pretrend_did_bps: int
    minimum_average_event_did_bps: int
    pairs: tuple[MatchedPair, ...]
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


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path}: expected integer")
    if not -10000 <= value <= 10000:
        raise ValidationError(f"{path}: expected basis points in [-10000, 10000]")
    return value


def _natural(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return value


def _window(value: Any, path: str) -> StrategyWindow:
    obj = _object(value, path)
    expected = {
        "id", "evidence_domains", "baseline_outflow_bps",
        "pre_event_outflow_bps", "post_event_outflow_bps",
    }
    if set(obj) != expected:
        raise ValidationError(f"{path}: fields do not match strategy-window schema")
    domains_raw = obj["evidence_domains"]
    if not isinstance(domains_raw, list) or not domains_raw or any(
        not isinstance(domain, str) or not domain for domain in domains_raw
    ):
        raise ValidationError(f"{path}.evidence_domains: expected non-empty strings")
    domains = tuple(domains_raw)
    if len(set(domains)) != len(domains):
        raise ValidationError(f"{path}.evidence_domains: duplicates are not allowed")
    return StrategyWindow(
        id=_string(obj["id"], f"{path}.id"),
        evidence_domains=domains,
        baseline_outflow_bps=_integer(
            obj["baseline_outflow_bps"], f"{path}.baseline_outflow_bps"
        ),
        pre_event_outflow_bps=_integer(
            obj["pre_event_outflow_bps"], f"{path}.pre_event_outflow_bps"
        ),
        post_event_outflow_bps=_integer(
            obj["post_event_outflow_bps"], f"{path}.post_event_outflow_bps"
        ),
    )


def load_plan(path: Path) -> Plan:
    raw = _object(load_json(path), "$")
    allowed = {
        "schema_version", "name", "failed_domain", "preregistered_at",
        "event_time", "maximum_match_distance_bps",
        "maximum_absolute_pretrend_did_bps",
        "minimum_average_event_did_bps", "pairs",
    }
    unknown = set(raw) - allowed
    if unknown:
        raise ValidationError(f"$: unknown fields: {sorted(unknown)}")
    if raw.get("schema_version") != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")

    pairs_raw = raw.get("pairs")
    if not isinstance(pairs_raw, list) or not pairs_raw:
        raise ValidationError("$.pairs: expected non-empty array")
    pairs: list[MatchedPair] = []
    strategy_ids: set[str] = set()
    for index, item in enumerate(pairs_raw):
        pair_path = f"$.pairs[{index}]"
        obj = _object(item, pair_path)
        expected = {
            "id", "treated", "control", "conventional_distance_bps"
        }
        if set(obj) != expected:
            raise ValidationError(f"{pair_path}: fields do not match pair schema")
        treated = _window(obj["treated"], f"{pair_path}.treated")
        control = _window(obj["control"], f"{pair_path}.control")
        if treated.id == control.id:
            raise ValidationError(f"{pair_path}: treated and control must differ")
        for strategy_id in (treated.id, control.id):
            if strategy_id in strategy_ids:
                raise ValidationError(f"{pair_path}: strategy ids must be globally unique")
            strategy_ids.add(strategy_id)
        distance_raw = _object(
            obj["conventional_distance_bps"],
            f"{pair_path}.conventional_distance_bps",
        )
        if set(distance_raw) != set(DISTANCE_KEYS):
            raise ValidationError(
                f"{pair_path}.conventional_distance_bps: keys must be {DISTANCE_KEYS}"
            )
        distances = {
            key: _natural(
                distance_raw[key],
                f"{pair_path}.conventional_distance_bps.{key}",
            )
            for key in DISTANCE_KEYS
        }
        if any(value > 10000 for value in distances.values()):
            raise ValidationError(f"{pair_path}: distance exceeds 10000 bps")
        pairs.append(MatchedPair(
            id=_string(obj["id"], f"{pair_path}.id"),
            treated=treated,
            control=control,
            conventional_distance_bps=distances,
        ))
    if len({pair.id for pair in pairs}) != len(pairs):
        raise ValidationError("$.pairs: pair ids must be unique")

    plan = Plan(
        source=path.resolve(),
        name=_string(raw.get("name"), "$.name"),
        failed_domain=_string(raw.get("failed_domain"), "$.failed_domain"),
        preregistered_at=_natural(raw.get("preregistered_at"), "$.preregistered_at"),
        event_time=_natural(raw.get("event_time"), "$.event_time"),
        maximum_match_distance_bps=_natural(
            raw.get("maximum_match_distance_bps"),
            "$.maximum_match_distance_bps",
        ),
        maximum_absolute_pretrend_did_bps=_natural(
            raw.get("maximum_absolute_pretrend_did_bps"),
            "$.maximum_absolute_pretrend_did_bps",
        ),
        minimum_average_event_did_bps=_natural(
            raw.get("minimum_average_event_did_bps"),
            "$.minimum_average_event_did_bps",
        ),
        pairs=tuple(pairs),
        raw=raw,
    )
    return plan
