from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json

from .errors import ValidationError

SCHEMA = "lfv-pit-micro-study-v1"


@dataclass(frozen=True)
class Vintage:
    id: str
    revision: int
    first_published_at: int
    supersedes: str | None


@dataclass(frozen=True)
class Asset:
    id: str
    listed_at: int
    delisted_at: int | None

    def eligible(self, as_of: int) -> bool:
        return self.listed_at <= as_of and (
            self.delisted_at is None or as_of < self.delisted_at
        )


@dataclass(frozen=True)
class Price:
    asset: str
    time: int
    available_at: int
    value: int
    vintage: str


@dataclass(frozen=True)
class Snapshot:
    as_of: int
    members: tuple[str, ...]


@dataclass(frozen=True)
class Decision:
    decision_at: int
    as_of: int
    lookback_time: int
    observation_time: int
    vintage: str


@dataclass(frozen=True)
class Action:
    id: str
    asset: str
    announced_at: int
    effective_at: int


@dataclass(frozen=True)
class Adjustment:
    id: str
    generated_at: int
    actions: tuple[str, ...]


@dataclass(frozen=True)
class Evaluation:
    registered_at: int
    benchmark: str
    metric: str
    lookback_periods: int
    cost_bps: int


@dataclass(frozen=True)
class Study:
    source: Path
    name: str
    vintages: tuple[Vintage, ...]
    assets: tuple[Asset, ...]
    prices: tuple[Price, ...]
    snapshots: tuple[Snapshot, ...]
    decisions: tuple[Decision, ...]
    actions: tuple[Action, ...]
    adjustments: tuple[Adjustment, ...]
    evaluation: Evaluation

    @property
    def vintage_by_id(self) -> dict[str, Vintage]:
        return {vintage.id: vintage for vintage in self.vintages}

    @property
    def asset_by_id(self) -> dict[str, Asset]:
        return {asset.id: asset for asset in self.assets}


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected object")
    return value


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return value


def _identifier(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected non-empty string")
    return value


def load_study(path: Path) -> Study:
    raw = _object(load_json(path), "$")
    if raw.get("schema_version") != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")
    vintages = tuple(Vintage(
        id=_identifier(item.get("id"), "$.vintages[].id"),
        revision=_integer(item.get("revision"), "$.vintages[].revision"),
        first_published_at=_integer(item.get("first_published_at"), "$.vintages[].first_published_at"),
        supersedes=item.get("supersedes"),
    ) for item in raw.get("vintages", []))
    if len({item.id for item in vintages}) != len(vintages) or not vintages:
        raise ValidationError("$.vintages: expected unique non-empty vintages")
    vintage_ids = {item.id for item in vintages}
    for item in vintages:
        if item.supersedes is not None and item.supersedes not in vintage_ids:
            raise ValidationError(f"vintage {item.id}: unknown supersedes")
    assets = tuple(Asset(
        id=_identifier(item.get("id"), "$.assets[].id"),
        listed_at=_integer(item.get("listed_at"), "$.assets[].listed_at"),
        delisted_at=(None if item.get("delisted_at") is None else _integer(item.get("delisted_at"), "$.assets[].delisted_at")),
    ) for item in raw.get("assets", []))
    if len({item.id for item in assets}) != len(assets) or not assets:
        raise ValidationError("$.assets: expected unique non-empty assets")
    asset_ids = {item.id for item in assets}
    prices = tuple(Price(
        asset=_identifier(item.get("asset"), "$.prices[].asset"),
        time=_integer(item.get("time"), "$.prices[].time"),
        available_at=_integer(item.get("available_at"), "$.prices[].available_at"),
        value=_integer(item.get("value"), "$.prices[].value"),
        vintage=_identifier(item.get("vintage"), "$.prices[].vintage"),
    ) for item in raw.get("prices", []))
    if any(item.asset not in asset_ids or item.vintage not in vintage_ids or item.value == 0 for item in prices):
        raise ValidationError("$.prices: unknown asset/vintage or zero value")
    snapshots = tuple(Snapshot(
        as_of=_integer(item.get("as_of"), "$.universe_snapshots[].as_of"),
        members=tuple(item.get("members", [])),
    ) for item in raw.get("universe_snapshots", []))
    decisions = tuple(Decision(
        decision_at=_integer(item.get("decision_at"), "$.decisions[].decision_at"),
        as_of=_integer(item.get("as_of"), "$.decisions[].as_of"),
        lookback_time=_integer(item.get("lookback_time"), "$.decisions[].lookback_time"),
        observation_time=_integer(item.get("observation_time"), "$.decisions[].observation_time"),
        vintage=_identifier(item.get("vintage"), "$.decisions[].vintage"),
    ) for item in raw.get("decisions", []))
    actions = tuple(Action(
        id=_identifier(item.get("id"), "$.corporate_actions[].id"),
        asset=_identifier(item.get("asset"), "$.corporate_actions[].asset"),
        announced_at=_integer(item.get("announced_at"), "$.corporate_actions[].announced_at"),
        effective_at=_integer(item.get("effective_at"), "$.corporate_actions[].effective_at"),
    ) for item in raw.get("corporate_actions", []))
    adjustments = tuple(Adjustment(
        id=_identifier(item.get("id"), "$.adjustments[].id"),
        generated_at=_integer(item.get("generated_at"), "$.adjustments[].generated_at"),
        actions=tuple(item.get("actions", [])),
    ) for item in raw.get("adjustments", []))
    evaluation_raw = _object(raw.get("evaluation_contract"), "$.evaluation_contract")
    evaluation = Evaluation(
        registered_at=_integer(evaluation_raw.get("registered_at"), "$.evaluation_contract.registered_at"),
        benchmark=_identifier(evaluation_raw.get("benchmark"), "$.evaluation_contract.benchmark"),
        metric=_identifier(evaluation_raw.get("metric"), "$.evaluation_contract.metric"),
        lookback_periods=_integer(evaluation_raw.get("lookback_periods"), "$.evaluation_contract.lookback_periods"),
        cost_bps=_integer(evaluation_raw.get("cost_bps"), "$.evaluation_contract.cost_bps"),
    )
    name = _identifier(raw.get("name"), "$.name")
    return Study(path.resolve(), name, vintages, assets, prices, snapshots,
        decisions, actions, adjustments, evaluation)
