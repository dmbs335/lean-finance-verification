from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import load_json

from .errors import ValidationError

SCHEMA = "lfv-fake-alpha-benchmark-v1"
MAX_CHANNELS = 12
DISTORTION_KINDS = {
    "futureInformation",
    "survivorshipBias",
    "parameterMining",
    "costMutation",
    "benchmarkSwitching",
}


@dataclass(frozen=True)
class Channel:
    id: str
    cost: int
    detects: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class Distortion:
    kind: str
    inflation_bps: int


@dataclass(frozen=True)
class Experiment:
    id: str
    clean_alpha_bps: int
    distortions: tuple[Distortion, ...]
    description: str

    @property
    def observed_alpha_bps(self) -> int:
        return self.clean_alpha_bps + sum(
            distortion.inflation_bps for distortion in self.distortions
        )


@dataclass(frozen=True)
class Benchmark:
    source: Path
    name: str
    channels: tuple[Channel, ...]
    experiments: tuple[Experiment, ...]

    @property
    def channel_by_id(self) -> dict[str, Channel]:
        return {channel.id: channel for channel in self.channels}


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


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path}: expected integer")
    return value


def load_benchmark(path: Path) -> Benchmark:
    raw = _object(load_json(path), "$")
    allowed = {"schema_version", "name", "channels", "experiments"}
    unknown = set(raw) - allowed
    if unknown:
        raise ValidationError(f"$: unknown fields: {sorted(unknown)}")
    if raw.get("schema_version") != SCHEMA:
        raise ValidationError(f"$.schema_version: expected {SCHEMA}")

    channels: list[Channel] = []
    for index, item in enumerate(raw.get("channels", [])):
        obj = _object(item, f"$.channels[{index}]")
        channel_id = _string(obj.get("id"), f"$.channels[{index}].id")
        detects_raw = obj.get("detects")
        if not isinstance(detects_raw, list) or any(
            not isinstance(kind, str) or kind not in DISTORTION_KINDS
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
        channels.append(
            Channel(
                id=channel_id,
                cost=_natural(obj.get("cost"), f"$.channels[{index}].cost"),
                detects=detects,
                description=_string(
                    obj.get("description", channel_id),
                    f"$.channels[{index}].description",
                ),
            )
        )
    if not channels or len(channels) > MAX_CHANNELS:
        raise ValidationError(
            f"$.channels: expected between 1 and {MAX_CHANNELS} channels"
        )
    if len({channel.id for channel in channels}) != len(channels):
        raise ValidationError("$.channels: ids must be unique")

    experiments: list[Experiment] = []
    for index, item in enumerate(raw.get("experiments", [])):
        obj = _object(item, f"$.experiments[{index}]")
        experiment_id = _string(
            obj.get("id"), f"$.experiments[{index}].id"
        )
        distortions: list[Distortion] = []
        distortions_raw = obj.get("distortions", [])
        if not isinstance(distortions_raw, list):
            raise ValidationError(
                f"$.experiments[{index}].distortions: expected array"
            )
        for distortion_index, distortion_item in enumerate(distortions_raw):
            distortion_obj = _object(
                distortion_item,
                f"$.experiments[{index}].distortions[{distortion_index}]",
            )
            kind = distortion_obj.get("kind")
            if kind not in DISTORTION_KINDS:
                raise ValidationError(
                    f"$.experiments[{index}].distortions[{distortion_index}].kind: "
                    "unknown distortion"
                )
            distortions.append(
                Distortion(
                    kind=kind,
                    inflation_bps=_natural(
                        distortion_obj.get("inflation_bps"),
                        f"$.experiments[{index}].distortions[{distortion_index}]"
                        ".inflation_bps",
                    ),
                )
            )
        kinds = [distortion.kind for distortion in distortions]
        if len(set(kinds)) != len(kinds):
            raise ValidationError(
                f"$.experiments[{index}].distortions: kinds must be unique"
            )
        experiment = Experiment(
            id=experiment_id,
            clean_alpha_bps=_integer(
                obj.get("clean_alpha_bps"),
                f"$.experiments[{index}].clean_alpha_bps",
            ),
            distortions=tuple(distortions),
            description=_string(
                obj.get("description", experiment_id),
                f"$.experiments[{index}].description",
            ),
        )
        declared_observed = obj.get("observed_alpha_bps")
        if declared_observed is not None and (
            _integer(
                declared_observed,
                f"$.experiments[{index}].observed_alpha_bps",
            )
            != experiment.observed_alpha_bps
        ):
            raise ValidationError(
                f"$.experiments[{index}].observed_alpha_bps does not equal "
                "clean alpha plus declared inflation"
            )
        experiments.append(experiment)
    if len(experiments) < 2:
        raise ValidationError("$.experiments: expected at least two experiments")
    if len({experiment.id for experiment in experiments}) != len(experiments):
        raise ValidationError("$.experiments: ids must be unique")

    return Benchmark(
        source=path.resolve(),
        name=_string(raw.get("name"), "$.name"),
        channels=tuple(channels),
        experiments=tuple(experiments),
    )
