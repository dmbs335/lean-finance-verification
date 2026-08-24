from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json
from tools.pit_study.errors import ValidationError

CONFIG_SCHEMA = "lfv-alfred-revision-study-v2"
PACKAGE_SCHEMA = "lfv-alfred-vintage-package-v2"
RELEASE_CALENDAR_SCHEMA = "lfv-release-calendar-v1"
REPORT_SCHEMA = "lfv-alfred-revision-leakage-report-v2"
FRED_OBSERVATIONS_ENDPOINT = (
    "https://api.stlouisfed.org/fred/series/observations"
)
API_KEY_PATTERN = re.compile(r"^[a-z0-9]{32}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class DecisionSpec:
    decision_at: str
    as_of_date: str
    realized_return_bps: int


@dataclass(frozen=True)
class StudyConfig:
    source: Path
    name: str
    series_id: str
    observation_start: str
    latest_vintage_date: str
    value_scale: int
    signal_threshold_scaled: int
    turnover_cost_bps: int
    decisions: tuple[DecisionSpec, ...]


@dataclass(frozen=True)
class SnapshotRef:
    kind: str
    as_of_date: str
    vintage_date: str
    relative_path: str
    sha256: str
    path: Path


@dataclass(frozen=True)
class ReleaseCalendarRef:
    relative_path: str
    sha256: str
    path: Path


@dataclass(frozen=True)
class VintagePackage:
    source: Path
    series_id: str
    latest_vintage_date: str
    release_calendar: ReleaseCalendarRef
    release_at_by_observation: dict[str, str]
    responses: tuple[SnapshotRef, ...]

    @property
    def by_key(self) -> dict[tuple[str, str], SnapshotRef]:
        return {
            (item.kind, item.as_of_date): item
            for item in self.responses
        }


@dataclass(frozen=True)
class Observation:
    observation_date: str
    value_scaled: int
    release_at: str


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


def _natural(value: Any, path: str, *, positive: bool = False) -> int:
    result = _integer(value, path)
    if result < 0 or (positive and result == 0):
        qualifier = "positive" if positive else "non-negative"
        raise ValidationError(f"{path}: expected {qualifier} integer")
    return result


def _iso_date(value: Any, path: str) -> str:
    text = _string(value, path)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(f"{path}: expected ISO date") from exc
    return text


def _parse_instant(value: str, path: str) -> datetime:
    if not value.endswith("Z"):
        raise ValidationError(
            f"{path}: expected UTC ISO timestamp ending in Z"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValidationError(f"{path}: expected UTC ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValidationError(f"{path}: timestamp must use UTC")
    return parsed


def _iso_instant(value: Any, path: str) -> str:
    text = _string(value, path)
    _parse_instant(text, path)
    return text


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config(path: Path) -> StudyConfig:
    raw = _object(load_json(path), "$")
    expected = {
        "schema_version",
        "name",
        "series_id",
        "observation_start",
        "latest_vintage_date",
        "value_scale",
        "signal_threshold_scaled",
        "turnover_cost_bps",
        "decisions",
    }
    if set(raw) != expected or raw["schema_version"] != CONFIG_SCHEMA:
        raise ValidationError("$: fields or schema do not match study config")

    decisions_raw = raw["decisions"]
    if not isinstance(decisions_raw, list) or not decisions_raw:
        raise ValidationError("$.decisions: expected non-empty array")
    decisions: list[DecisionSpec] = []
    for index, item in enumerate(decisions_raw):
        item_path = f"$.decisions[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {
            "decision_at",
            "as_of_date",
            "realized_return_bps",
        }:
            raise ValidationError(
                f"{item_path}: fields do not match decision schema"
            )
        decision_at = _iso_instant(
            obj["decision_at"], f"{item_path}.decision_at"
        )
        as_of_date = _iso_date(
            obj["as_of_date"], f"{item_path}.as_of_date"
        )
        if decision_at[:10] != as_of_date:
            raise ValidationError(
                f"{item_path}: as_of_date must equal UTC decision date"
            )
        decisions.append(
            DecisionSpec(
                decision_at=decision_at,
                as_of_date=as_of_date,
                realized_return_bps=_integer(
                    obj["realized_return_bps"],
                    f"{item_path}.realized_return_bps",
                ),
            )
        )
    decision_instants = [
        _parse_instant(item.decision_at, "decision_at")
        for item in decisions
    ]
    if decision_instants != sorted(decision_instants):
        raise ValidationError("$.decisions: decision_at values must be sorted")
    as_of_dates = [item.as_of_date for item in decisions]
    if len(set(as_of_dates)) != len(as_of_dates):
        raise ValidationError("$.decisions: as_of_date values must be unique")

    latest_vintage_date = _iso_date(
        raw["latest_vintage_date"], "$.latest_vintage_date"
    )
    if any(
        latest_vintage_date <= decision.as_of_date
        for decision in decisions
    ):
        raise ValidationError(
            "$.latest_vintage_date must be later than every as_of_date"
        )
    return StudyConfig(
        source=path.resolve(),
        name=_string(raw["name"], "$.name"),
        series_id=_string(raw["series_id"], "$.series_id"),
        observation_start=_iso_date(
            raw["observation_start"], "$.observation_start"
        ),
        latest_vintage_date=latest_vintage_date,
        value_scale=_natural(raw["value_scale"], "$.value_scale", positive=True),
        signal_threshold_scaled=_integer(
            raw["signal_threshold_scaled"], "$.signal_threshold_scaled"
        ),
        turnover_cost_bps=_natural(
            raw["turnover_cost_bps"], "$.turnover_cost_bps"
        ),
        decisions=tuple(decisions),
    )


def _safe_package_path(root: Path, relative: str, path: str) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValidationError(f"{path}: unsafe relative path")
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValidationError(f"{path}: path escapes package root") from exc
    if not candidate.is_file():
        raise ValidationError(f"{path}: missing package file {relative}")
    return candidate


def _load_release_calendar(
    path: Path,
    config: StudyConfig,
) -> dict[str, str]:
    raw = _object(load_json(path), str(path))
    if set(raw) != {"schema_version", "series_id", "releases"}:
        raise ValidationError(f"{path}: release-calendar fields do not match")
    if raw["schema_version"] != RELEASE_CALENDAR_SCHEMA:
        raise ValidationError(f"{path}: unsupported release-calendar schema")
    if raw["series_id"] != config.series_id:
        raise ValidationError(f"{path}: release calendar binds another series")
    releases_raw = raw["releases"]
    if not isinstance(releases_raw, list) or not releases_raw:
        raise ValidationError(f"{path}: releases must be a non-empty array")
    releases: dict[str, str] = {}
    for index, item in enumerate(releases_raw):
        item_path = f"{path}.releases[{index}]"
        obj = _object(item, item_path)
        if set(obj) != {"observation_date", "release_at"}:
            raise ValidationError(
                f"{item_path}: fields do not match release schema"
            )
        observation_date = _iso_date(
            obj["observation_date"], f"{item_path}.observation_date"
        )
        release_at = _iso_instant(
            obj["release_at"], f"{item_path}.release_at"
        )
        if release_at[:10] < observation_date:
            raise ValidationError(
                f"{item_path}: release cannot precede observation date"
            )
        if observation_date in releases:
            raise ValidationError(
                f"{path}: duplicate release for {observation_date}"
            )
        releases[observation_date] = release_at
    return releases


def load_package(path: Path, config: StudyConfig) -> VintagePackage:
    raw = _object(load_json(path), "$")
    expected = {
        "schema_version",
        "series_id",
        "latest_vintage_date",
        "release_calendar",
        "responses",
    }
    if set(raw) != expected or raw["schema_version"] != PACKAGE_SCHEMA:
        raise ValidationError("$: fields or schema do not match vintage package")
    if raw["series_id"] != config.series_id:
        raise ValidationError("$.series_id does not match study config")
    if raw["latest_vintage_date"] != config.latest_vintage_date:
        raise ValidationError("$.latest_vintage_date does not match study config")

    root = path.resolve().parent
    release_obj = _object(raw["release_calendar"], "$.release_calendar")
    if set(release_obj) != {"relative_path", "sha256"}:
        raise ValidationError("$.release_calendar: fields do not match")
    release_relative = _string(
        release_obj["relative_path"], "$.release_calendar.relative_path"
    )
    release_path = _safe_package_path(
        root, release_relative, "$.release_calendar.relative_path"
    )
    release_digest = _string(
        release_obj["sha256"], "$.release_calendar.sha256"
    )
    if not SHA256_PATTERN.fullmatch(release_digest):
        raise ValidationError(
            "$.release_calendar.sha256: expected lowercase SHA-256"
        )
    if _sha256(release_path) != release_digest:
        raise ValidationError("$.release_calendar: digest mismatch")
    release_calendar = ReleaseCalendarRef(
        relative_path=release_relative,
        sha256=release_digest,
        path=release_path,
    )
    release_at_by_observation = _load_release_calendar(
        release_path, config
    )

    responses_raw = raw["responses"]
    if not isinstance(responses_raw, list):
        raise ValidationError("$.responses: expected array")
    responses: list[SnapshotRef] = []
    for index, item in enumerate(responses_raw):
        item_path = f"$.responses[{index}]"
        obj = _object(item, item_path)
        expected_item = {
            "kind",
            "as_of_date",
            "vintage_date",
            "relative_path",
            "sha256",
        }
        if set(obj) != expected_item:
            raise ValidationError(f"{item_path}: fields do not match response ref")
        kind = _string(obj["kind"], f"{item_path}.kind")
        if kind not in {"realtime", "latest"}:
            raise ValidationError(f"{item_path}.kind: expected realtime or latest")
        as_of_date = _iso_date(
            obj["as_of_date"], f"{item_path}.as_of_date"
        )
        vintage_date = _iso_date(
            obj["vintage_date"], f"{item_path}.vintage_date"
        )
        if kind == "realtime" and vintage_date != as_of_date:
            raise ValidationError(
                f"{item_path}: realtime vintage must equal as_of_date"
            )
        if kind == "latest" and vintage_date != config.latest_vintage_date:
            raise ValidationError(
                f"{item_path}: latest vintage must match config"
            )
        relative_path = _string(
            obj["relative_path"], f"{item_path}.relative_path"
        )
        response_path = _safe_package_path(
            root, relative_path, f"{item_path}.relative_path"
        )
        digest = _string(obj["sha256"], f"{item_path}.sha256")
        if not SHA256_PATTERN.fullmatch(digest):
            raise ValidationError(f"{item_path}.sha256: expected lowercase SHA-256")
        if _sha256(response_path) != digest:
            raise ValidationError(f"{item_path}: response digest mismatch")
        responses.append(
            SnapshotRef(
                kind=kind,
                as_of_date=as_of_date,
                vintage_date=vintage_date,
                relative_path=relative_path,
                sha256=digest,
                path=response_path,
            )
        )

    keys = [(item.kind, item.as_of_date) for item in responses]
    if len(set(keys)) != len(keys):
        raise ValidationError("$.responses: duplicate kind/as_of_date pair")
    expected_keys = {
        (kind, decision.as_of_date)
        for decision in config.decisions
        for kind in ("realtime", "latest")
    }
    if set(keys) != expected_keys:
        missing = sorted(expected_keys - set(keys))
        extra = sorted(set(keys) - expected_keys)
        raise ValidationError(
            f"$.responses: incomplete decision coverage; "
            f"missing={missing} extra={extra}"
        )
    return VintagePackage(
        source=path.resolve(),
        series_id=config.series_id,
        latest_vintage_date=config.latest_vintage_date,
        release_calendar=release_calendar,
        release_at_by_observation=release_at_by_observation,
        responses=tuple(responses),
    )


def _scale_value(value: str, scale: int, path: str) -> int:
    try:
        decimal = Decimal(value)
    except InvalidOperation as exc:
        raise ValidationError(f"{path}: invalid decimal value") from exc
    scaled = decimal * scale
    integral = scaled.to_integral_value()
    if scaled != integral:
        raise ValidationError(
            f"{path}: value cannot be represented exactly at scale {scale}"
        )
    return int(integral)


def _load_observations(
    ref: SnapshotRef,
    config: StudyConfig,
    release_at_by_observation: dict[str, str],
) -> list[Observation]:
    raw = _object(load_json(ref.path), str(ref.path))
    if raw.get("realtime_start") != ref.vintage_date:
        raise ValidationError(
            f"{ref.relative_path}: realtime_start does not match manifest"
        )
    if raw.get("realtime_end") != ref.vintage_date:
        raise ValidationError(
            f"{ref.relative_path}: realtime_end does not match manifest"
        )
    if raw.get("output_type") not in {1, "1"}:
        raise ValidationError(
            f"{ref.relative_path}: expected FRED output_type=1"
        )
    observations_raw = raw.get("observations")
    if not isinstance(observations_raw, list):
        raise ValidationError(
            f"{ref.relative_path}: observations must be an array"
        )
    observations: list[Observation] = []
    seen_dates: set[str] = set()
    for index, item in enumerate(observations_raw):
        item_path = f"{ref.relative_path}.observations[{index}]"
        obj = _object(item, item_path)
        observation_date = _iso_date(obj.get("date"), f"{item_path}.date")
        value = obj.get("value")
        if value in {None, ".", ""}:
            continue
        value_text = _string(value, f"{item_path}.value")
        realtime_start = _iso_date(
            obj.get("realtime_start"), f"{item_path}.realtime_start"
        )
        realtime_end = _iso_date(
            obj.get("realtime_end"), f"{item_path}.realtime_end"
        )
        if not (realtime_start <= ref.vintage_date <= realtime_end):
            raise ValidationError(
                f"{item_path}: observation is not valid at declared vintage"
            )
        if observation_date in seen_dates:
            raise ValidationError(
                f"{ref.relative_path}: duplicate observation date "
                f"{observation_date}"
            )
        seen_dates.add(observation_date)
        if observation_date < ref.as_of_date:
            release_at = release_at_by_observation.get(observation_date)
            if release_at is None:
                raise ValidationError(
                    f"release calendar lacks observation {observation_date}"
                )
            observations.append(
                Observation(
                    observation_date=observation_date,
                    value_scaled=_scale_value(
                        value_text,
                        config.value_scale,
                        f"{item_path}.value",
                    ),
                    release_at=release_at,
                )
            )
    observations.sort(key=lambda item: item.observation_date)
    if len(observations) < 2:
        raise ValidationError(
            f"{ref.relative_path}: fewer than two observations precede "
            "as_of_date"
        )
    return observations


def _summary_from_pair(
    ref: SnapshotRef,
    pair: tuple[Observation, Observation],
    config: StudyConfig,
) -> dict[str, Any]:
    prior, current = pair
    signal = current.value_scaled - prior.value_scaled
    position = 1 if signal >= config.signal_threshold_scaled else -1
    return {
        "vintage_date": ref.vintage_date,
        "observation_dates": [prior.observation_date, current.observation_date],
        "release_at": [prior.release_at, current.release_at],
        "values_scaled": [prior.value_scaled, current.value_scaled],
        "signal_scaled": signal,
        "position": position,
        "source_sha256": ref.sha256,
        "source_path": ref.relative_path,
    }


def _turnover_cost(
    previous_position: int | None,
    position: int,
    turnover_cost_bps: int,
) -> int:
    return (
        turnover_cost_bps
        if previous_position is None or previous_position != position
        else 0
    )


def run_study(
    config: StudyConfig,
    package: VintagePackage,
) -> dict[str, Any]:
    by_key = package.by_key
    decisions: list[dict[str, Any]] = []
    vintage_total = 0
    release_strict_total = 0
    revision_only_total = 0
    latest_naive_total = 0
    vintage_previous: int | None = None
    strict_previous: int | None = None
    revision_previous: int | None = None
    naive_previous: int | None = None

    for spec in config.decisions:
        realtime_ref = by_key[("realtime", spec.as_of_date)]
        latest_ref = by_key[("latest", spec.as_of_date)]
        realtime_observations = _load_observations(
            realtime_ref,
            config,
            package.release_at_by_observation,
        )
        latest_observations = _load_observations(
            latest_ref,
            config,
            package.release_at_by_observation,
        )
        decision_instant = _parse_instant(spec.decision_at, "decision_at")
        vintage_pair = tuple(realtime_observations[-2:])
        release_safe_observations = [
            observation
            for observation in realtime_observations
            if _parse_instant(observation.release_at, "release_at")
            <= decision_instant
        ]
        if len(release_safe_observations) < 2:
            raise ValidationError(
                f"{spec.decision_at}: fewer than two release-time-safe "
                "observations"
            )
        strict_pair = tuple(release_safe_observations[-2:])
        latest_by_date = {
            observation.observation_date: observation
            for observation in latest_observations
        }
        try:
            revision_pair = tuple(
                latest_by_date[observation.observation_date]
                for observation in strict_pair
            )
        except KeyError as exc:
            raise ValidationError(
                f"{latest_ref.relative_path}: latest vintage lacks a "
                "release-time-safe observation"
            ) from exc
        latest_naive_pair = tuple(latest_observations[-2:])

        vintage = _summary_from_pair(
            realtime_ref,
            vintage_pair,  # type: ignore[arg-type]
            config,
        )
        release_strict = _summary_from_pair(
            realtime_ref,
            strict_pair,  # type: ignore[arg-type]
            config,
        )
        revision_only = _summary_from_pair(
            latest_ref,
            revision_pair,  # type: ignore[arg-type]
            config,
        )
        latest_naive = _summary_from_pair(
            latest_ref,
            latest_naive_pair,  # type: ignore[arg-type]
            config,
        )

        vintage_turnover = _turnover_cost(
            vintage_previous,
            int(vintage["position"]),
            config.turnover_cost_bps,
        )
        strict_turnover = _turnover_cost(
            strict_previous,
            int(release_strict["position"]),
            config.turnover_cost_bps,
        )
        revision_turnover = _turnover_cost(
            revision_previous,
            int(revision_only["position"]),
            config.turnover_cost_bps,
        )
        naive_turnover = _turnover_cost(
            naive_previous,
            int(latest_naive["position"]),
            config.turnover_cost_bps,
        )
        vintage_return = (
            int(vintage["position"]) * spec.realized_return_bps
            - vintage_turnover
        )
        strict_return = (
            int(release_strict["position"]) * spec.realized_return_bps
            - strict_turnover
        )
        revision_return = (
            int(revision_only["position"]) * spec.realized_return_bps
            - revision_turnover
        )
        naive_return = (
            int(latest_naive["position"]) * spec.realized_return_bps
            - naive_turnover
        )
        post_decision_inputs = [
            observation.observation_date
            for observation in vintage_pair
            if _parse_instant(observation.release_at, "release_at")
            > decision_instant
        ]
        same_day_after_decision = [
            observation.observation_date
            for observation in vintage_pair
            if observation.release_at[:10] == spec.as_of_date
            and _parse_instant(observation.release_at, "release_at")
            > decision_instant
        ]
        availability_changed = (
            release_strict["observation_dates"]
            != latest_naive["observation_dates"]
        )
        selected_values_revised = (
            release_strict["values_scaled"]
            != revision_only["values_scaled"]
        )
        decisions.append(
            {
                "decision_at": spec.decision_at,
                "as_of_date": spec.as_of_date,
                "realized_return_bps": spec.realized_return_bps,
                "vintage_date_path": vintage,
                "release_time_strict_path": release_strict,
                "revision_only_counterfactual": revision_only,
                "latest_naive_counterfactual": latest_naive,
                "vintage_date_policy_valid": (
                    realtime_ref.vintage_date <= spec.as_of_date
                ),
                "vintage_transformation_release_time_valid": (
                    not post_decision_inputs
                ),
                "release_time_strict_policy_valid": all(
                    _parse_instant(release_at, "release_at")
                    <= decision_instant
                    for release_at in release_strict["release_at"]
                ),
                "post_decision_release_inputs": post_decision_inputs,
                "same_day_release_after_decision_inputs": (
                    same_day_after_decision
                ),
                "availability_changed": availability_changed,
                "selected_values_revised": selected_values_revised,
                "vintage_vs_release_position_changed": (
                    vintage["position"] != release_strict["position"]
                ),
                "revision_position_changed": (
                    release_strict["position"]
                    != revision_only["position"]
                ),
                "naive_position_changed": (
                    release_strict["position"]
                    != latest_naive["position"]
                ),
                "vintage_turnover_cost_bps": vintage_turnover,
                "release_time_strict_turnover_cost_bps": strict_turnover,
                "revision_only_turnover_cost_bps": revision_turnover,
                "latest_naive_turnover_cost_bps": naive_turnover,
                "vintage_strategy_return_bps": vintage_return,
                "release_time_strict_strategy_return_bps": strict_return,
                "revision_only_strategy_return_bps": revision_return,
                "latest_naive_strategy_return_bps": naive_return,
                "intraday_release_leakage_bps": (
                    vintage_return - strict_return
                ),
                "revision_only_leakage_bps": (
                    revision_return - strict_return
                ),
                "revision_plus_availability_leakage_bps": (
                    naive_return - strict_return
                ),
            }
        )
        vintage_total += vintage_return
        release_strict_total += strict_return
        revision_only_total += revision_return
        latest_naive_total += naive_return
        vintage_previous = int(vintage["position"])
        strict_previous = int(release_strict["position"])
        revision_previous = int(revision_only["position"])
        naive_previous = int(latest_naive["position"])

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "name": config.name,
        "series_id": config.series_id,
        "api_contract": {
            "endpoint": FRED_OBSERVATIONS_ENDPOINT,
            "file_type": "json",
            "output_type": 1,
            "date_granularity": (
                "realtime_start=realtime_end=as_of_date"
            ),
            "intraday_release_times": (
                "hash-bound external release calendar"
            ),
        },
        "assurance": {
            "vintage_date_path": "dateGranularALFREDVintage",
            "release_time_strict_path": (
                "strictPointInTimeAtDecisionInstant"
            ),
            "revision_only_counterfactual": (
                "postDecisionLatestValuesOnReleaseTimeSafeObservations"
            ),
            "latest_naive_counterfactual": (
                "postDecisionLatestValuesAndObservationAvailability"
            ),
            "only_release_time_strict_path_is_strict_point_in_time": True,
        },
        "config_sha256": _sha256(config.source),
        "manifest_sha256": _sha256(package.source),
        "release_calendar": {
            "relative_path": package.release_calendar.relative_path,
            "sha256": package.release_calendar.sha256,
        },
        "latest_vintage_date": config.latest_vintage_date,
        "value_scale": config.value_scale,
        "signal_threshold_scaled": config.signal_threshold_scaled,
        "turnover_cost_bps": config.turnover_cost_bps,
        "decision_count": len(decisions),
        "decisions": decisions,
        "aggregate": {
            "vintage_date_total_return_bps": vintage_total,
            "release_time_strict_total_return_bps": release_strict_total,
            "revision_only_total_return_bps": revision_only_total,
            "latest_naive_total_return_bps": latest_naive_total,
            "intraday_release_leakage_bps": (
                vintage_total - release_strict_total
            ),
            "revision_only_leakage_bps": (
                revision_only_total - release_strict_total
            ),
            "revision_plus_availability_leakage_bps": (
                latest_naive_total - release_strict_total
            ),
            "vintage_only_leakage_decision_count": sum(
                1
                for item in decisions
                if not item["vintage_transformation_release_time_valid"]
            ),
            "both_policy_valid_decision_count": sum(
                1
                for item in decisions
                if item["vintage_transformation_release_time_valid"]
            ),
            "same_day_after_decision_boundary_count": sum(
                1
                for item in decisions
                if item["same_day_release_after_decision_inputs"]
            ),
            "vintage_vs_release_position_flip_count": sum(
                1
                for item in decisions
                if item["vintage_vs_release_position_changed"]
            ),
            "revision_position_flip_count": sum(
                1
                for item in decisions
                if item["revision_position_changed"]
            ),
            "naive_position_flip_count": sum(
                1 for item in decisions if item["naive_position_changed"]
            ),
            "availability_change_count": sum(
                1 for item in decisions if item["availability_changed"]
            ),
            "selected_value_revision_count": sum(
                1
                for item in decisions
                if item["selected_values_revised"]
            ),
            "all_release_time_strict_inputs_available": all(
                item["release_time_strict_policy_valid"]
                for item in decisions
            ),
            "all_latest_vintages_post_decision": all(
                item["as_of_date"] < config.latest_vintage_date
                for item in decisions
            ),
        },
        "source_responses": [
            {
                "kind": item.kind,
                "as_of_date": item.as_of_date,
                "vintage_date": item.vintage_date,
                "relative_path": item.relative_path,
                "sha256": item.sha256,
            }
            for item in sorted(
                package.responses,
                key=lambda item: (item.as_of_date, item.kind),
            )
        ],
        "interpretation": (
            "comparison of date-granular ALFRED availability, exact "
            "release-time availability, latest revisions on the same safe "
            "observations, and a naive latest-vintage reconstruction; not a "
            "future-profitability or causal market claim"
        ),
    }
    report["report_sha256"] = hashlib.sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify_report(
    config: StudyConfig,
    package: VintagePackage,
    report: Any,
) -> dict[str, Any]:
    expected = run_study(config, package)
    if report != expected:
        raise ValidationError(
            "ALFRED revision-leakage report does not match exact recomputation"
        )
    return expected


def resolve_api_key(explicit: str | None, environment_name: str) -> str:
    key = explicit or os.environ.get(environment_name, "")
    if not key:
        raise ValidationError(
            f"FRED API key is required via --api-key or {environment_name}"
        )
    if not API_KEY_PATTERN.fullmatch(key):
        raise ValidationError(
            "FRED API key must be 32 lowercase alphanumeric characters"
        )
    return key


def _download_json(parameters: dict[str, str], api_key: str) -> bytes:
    query = urllib.parse.urlencode({**parameters, "api_key": api_key})
    request = urllib.request.Request(
        f"{FRED_OBSERVATIONS_ENDPOINT}?{query}",
        headers={"User-Agent": "lean-finance-verification/0.2 research"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise ValidationError(
            f"FRED observations request failed with HTTP {exc.code}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ValidationError(
            f"FRED observations request failed: {exc.reason}"
        ) from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError("FRED response is not valid JSON") from exc
    if isinstance(parsed, dict) and "error_code" in parsed:
        raise ValidationError(
            f"FRED API error {parsed.get('error_code')}: "
            f"{parsed.get('error_message')}"
        )
    return raw


def download_package(
    config: StudyConfig,
    release_calendar_path: Path,
    out_dir: Path,
    api_key: str,
) -> Path:
    _load_release_calendar(release_calendar_path, config)
    out_dir.mkdir(parents=True, exist_ok=True)
    responses_dir = out_dir / "responses"
    responses_dir.mkdir(parents=True, exist_ok=True)
    release_destination = out_dir / "release-calendar.json"
    release_destination.write_bytes(release_calendar_path.read_bytes())
    refs: list[dict[str, str]] = []
    maximum_as_of = config.decisions[-1].as_of_date
    common = {
        "series_id": config.series_id,
        "file_type": "json",
        "output_type": "1",
        "observation_start": config.observation_start,
        "sort_order": "asc",
        "limit": "100000",
    }
    latest_path = responses_dir / "latest.json"
    latest_raw = _download_json(
        {
            **common,
            "realtime_start": config.latest_vintage_date,
            "realtime_end": config.latest_vintage_date,
            "observation_end": maximum_as_of,
        },
        api_key,
    )
    latest_path.write_bytes(latest_raw)
    latest_digest = hashlib.sha256(latest_raw).hexdigest()

    for decision in config.decisions:
        realtime_relative = f"responses/realtime-{decision.as_of_date}.json"
        realtime_path = out_dir / realtime_relative
        realtime_raw = _download_json(
            {
                **common,
                "realtime_start": decision.as_of_date,
                "realtime_end": decision.as_of_date,
                "observation_end": decision.as_of_date,
            },
            api_key,
        )
        realtime_path.write_bytes(realtime_raw)
        refs.append(
            {
                "kind": "realtime",
                "as_of_date": decision.as_of_date,
                "vintage_date": decision.as_of_date,
                "relative_path": realtime_relative,
                "sha256": hashlib.sha256(realtime_raw).hexdigest(),
            }
        )
        refs.append(
            {
                "kind": "latest",
                "as_of_date": decision.as_of_date,
                "vintage_date": config.latest_vintage_date,
                "relative_path": "responses/latest.json",
                "sha256": latest_digest,
            }
        )

    manifest = {
        "schema_version": PACKAGE_SCHEMA,
        "series_id": config.series_id,
        "latest_vintage_date": config.latest_vintage_date,
        "release_calendar": {
            "relative_path": "release-calendar.json",
            "sha256": _sha256(release_destination),
        },
        "responses": refs,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_bytes(canonical_bytes(manifest))
    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lfv-alfred-revision-leakage")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download")
    download.add_argument("--config", required=True, type=Path)
    download.add_argument("--release-calendar", required=True, type=Path)
    download.add_argument("--out-dir", required=True, type=Path)
    download.add_argument("--api-key")
    download.add_argument("--api-key-env", default="FRED_API_KEY")

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--config", required=True, type=Path)
    analyze.add_argument("--manifest", required=True, type=Path)
    analyze.add_argument("--out", required=True, type=Path)

    check = subparsers.add_parser("verify")
    check.add_argument("--config", required=True, type=Path)
    check.add_argument("--manifest", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "download":
            key = resolve_api_key(args.api_key, args.api_key_env)
            manifest = download_package(
                config,
                args.release_calendar,
                args.out_dir,
                key,
            )
            print(f"wrote {manifest}")
        else:
            package = load_package(args.manifest, config)
            if args.command == "analyze":
                report = run_study(config, package)
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_bytes(canonical_bytes(report))
                aggregate = report["aggregate"]
                print(
                    f"release_strict="
                    f"{aggregate['release_time_strict_total_return_bps']}bps "
                    f"vintage_date="
                    f"{aggregate['vintage_date_total_return_bps']}bps "
                    f"revision_only="
                    f"{aggregate['revision_only_total_return_bps']}bps "
                    f"intraday_leakage="
                    f"{aggregate['intraday_release_leakage_bps']}bps"
                )
            else:
                verify_report(config, package, load_json(args.report))
                print(f"verified {args.report}")
        return 0
    except (ValidationError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
