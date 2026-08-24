from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json

from .errors import ValidationError

SCHEMA = "lfv-certifiable-alpha-interval-v1"
MAX_CHANNELS = 12


@dataclass(frozen=True)
class ModelEstimate:
    id: str
    lower_bps: int
    upper_bps: int


@dataclass(frozen=True)
class Distortion:
    kind: str
    maximum_upward_inflation_bps: int


@dataclass(frozen=True)
class Channel:
    id: str
    cost: int
    detects: tuple[str, ...]


@dataclass(frozen=True)
class DeploymentCosts:
    minimum_bps: int
    maximum_bps: int


@dataclass(frozen=True)
class Problem:
    source: Path
    name: str
    models: tuple[ModelEstimate, ...]
    distortions: tuple[Distortion, ...]
    channels: tuple[Channel, ...]
    deployment_costs: DeploymentCosts
    target_maximum_width_bps: int


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
    return value


def _natural(value: Any, path: str) -> int:
    value = _integer(value, path)
    if value < 0:
        raise ValidationError(f"{path}: expected non-negative integer")
    return value


def load_problem(path: Path) -> Problem:
    raw = _object(load_json(path), "$")
    allowed = {
        "schema_version", "name", "models", "distortions", "channels",
        "deployment_costs", "target_maximum_width_bps",
    }
    unknown = set(raw) - allowed
    if unknown:
        raise ValidationError(f"$: unknown fields: {sorted(unknown)}")
    if raw.get("schema_version") != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")

    models: list[ModelEstimate] = []
    for index, item in enumerate(raw.get("models", [])):
        obj = _object(item, f"$.models[{index}]")
        lower = _integer(obj.get("lower_bps"), f"$.models[{index}].lower_bps")
        upper = _integer(obj.get("upper_bps"), f"$.models[{index}].upper_bps")
        if lower > upper:
            raise ValidationError(f"$.models[{index}]: lower exceeds upper")
        models.append(ModelEstimate(
            id=_string(obj.get("id"), f"$.models[{index}].id"),
            lower_bps=lower,
            upper_bps=upper,
        ))
    if len(models) < 2 or len({model.id for model in models}) != len(models):
        raise ValidationError("$.models: expected at least two unique models")

    distortions: list[Distortion] = []
    for index, item in enumerate(raw.get("distortions", [])):
        obj = _object(item, f"$.distortions[{index}]")
        distortions.append(Distortion(
            kind=_string(obj.get("kind"), f"$.distortions[{index}].kind"),
            maximum_upward_inflation_bps=_natural(
                obj.get("maximum_upward_inflation_bps"),
                f"$.distortions[{index}].maximum_upward_inflation_bps",
            ),
        ))
    distortion_kinds = [distortion.kind for distortion in distortions]
    if not distortions or len(set(distortion_kinds)) != len(distortions):
        raise ValidationError("$.distortions: expected unique non-empty kinds")
    known_distortions = set(distortion_kinds)

    channels: list[Channel] = []
    for index, item in enumerate(raw.get("channels", [])):
        obj = _object(item, f"$.channels[{index}]")
        detects_raw = obj.get("detects")
        if not isinstance(detects_raw, list) or any(
            not isinstance(kind, str) or kind not in known_distortions
            for kind in detects_raw
        ):
            raise ValidationError(
                f"$.channels[{index}].detects: expected known distortion kinds"
            )
        detects = tuple(detects_raw)
        if len(set(detects)) != len(detects):
            raise ValidationError(
                f"$.channels[{index}].detects: duplicates are not allowed"
            )
        channels.append(Channel(
            id=_string(obj.get("id"), f"$.channels[{index}].id"),
            cost=_natural(obj.get("cost"), f"$.channels[{index}].cost"),
            detects=detects,
        ))
    if not channels or len(channels) > MAX_CHANNELS:
        raise ValidationError(
            f"$.channels: expected between 1 and {MAX_CHANNELS} channels"
        )
    if len({channel.id for channel in channels}) != len(channels):
        raise ValidationError("$.channels: ids must be unique")

    costs_raw = _object(raw.get("deployment_costs"), "$.deployment_costs")
    if set(costs_raw) != {"minimum_bps", "maximum_bps"}:
        raise ValidationError("$.deployment_costs: invalid fields")
    minimum_cost = _natural(costs_raw["minimum_bps"], "$.deployment_costs.minimum_bps")
    maximum_cost = _natural(costs_raw["maximum_bps"], "$.deployment_costs.maximum_bps")
    if minimum_cost > maximum_cost:
        raise ValidationError("$.deployment_costs: minimum exceeds maximum")

    return Problem(
        source=path.resolve(),
        name=_string(raw.get("name"), "$.name"),
        models=tuple(models),
        distortions=tuple(distortions),
        channels=tuple(channels),
        deployment_costs=DeploymentCosts(minimum_cost, maximum_cost),
        target_maximum_width_bps=_natural(
            raw.get("target_maximum_width_bps"),
            "$.target_maximum_width_bps",
        ),
    )
