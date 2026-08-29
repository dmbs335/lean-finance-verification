from __future__ import annotations

import hashlib
import importlib
import inspect
import textwrap
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes, load_json
from tools.evidence_synth.errors import ValidationError as CanonicalValidationError

from .errors import ValidationError


SCHEMA = "lfv-gs-quant-pnl-conformance-v2"
REPORT_SCHEMA = "lfv-gs-quant-pnl-conformance-report-v2"


@dataclass(frozen=True)
class AttributeSpec:
    name: str
    risk_metric: str
    market_data_metric: str
    scaling_factor: Fraction
    second_order: bool


@dataclass(frozen=True)
class Snapshot:
    date: date
    location: str
    instruments: dict[str, dict[str, int]]


@dataclass(frozen=True)
class ConformanceModel:
    source: Path
    raw: dict[str, Any]
    package_name: str
    distribution_version: str
    module: str
    symbol: str
    method_source_sha256: str
    attributes: tuple[AttributeSpec, ...]
    snapshots: tuple[Snapshot, ...]
    expected_output: dict[str, dict[str, str]]


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


def _fields(value: dict[str, Any], expected: set[str], path: str) -> None:
    if set(value) != expected:
        raise ValidationError(f"{path}: fields do not match schema")


def load_conformance_model(path: Path) -> ConformanceModel:
    try:
        raw = _object(load_json(path), "$")
    except CanonicalValidationError as exc:
        raise ValidationError(str(exc)) from exc
    _fields(
        raw,
        {"schema_version", "upstream", "attributes", "snapshots", "expected_output"},
        "$",
    )
    if raw["schema_version"] != SCHEMA:
        raise ValidationError("$: unsupported schema_version")

    upstream = _object(raw["upstream"], "$.upstream")
    _fields(
        upstream,
        {
            "package_name",
            "distribution_version",
            "module",
            "symbol",
            "method_source_sha256",
        },
        "$.upstream",
    )
    source_digest = _string(
        upstream["method_source_sha256"], "$.upstream.method_source_sha256"
    )
    if len(source_digest) != 64 or any(
        character not in "0123456789abcdef" for character in source_digest
    ):
        raise ValidationError("$.upstream.method_source_sha256: expected SHA-256")
    symbol = _string(upstream["symbol"], "$.upstream.symbol")
    if symbol.count(".") != 1 or any(not part for part in symbol.split(".")):
        raise ValidationError("$.upstream.symbol: expected ClassName.method_name")

    attributes_raw = raw["attributes"]
    if not isinstance(attributes_raw, list) or not attributes_raw:
        raise ValidationError("$.attributes: expected non-empty array")
    attributes: list[AttributeSpec] = []
    for index, item in enumerate(attributes_raw):
        item_path = f"$.attributes[{index}]"
        attribute = _object(item, item_path)
        _fields(
            attribute,
            {
                "name",
                "risk_metric",
                "market_data_metric",
                "scaling_numerator",
                "scaling_denominator",
                "second_order",
            },
            item_path,
        )
        denominator = _integer(
            attribute["scaling_denominator"],
            f"{item_path}.scaling_denominator",
        )
        if denominator == 0:
            raise ValidationError(f"{item_path}.scaling_denominator: must be nonzero")
        second_order = attribute["second_order"]
        if not isinstance(second_order, bool):
            raise ValidationError(f"{item_path}.second_order: expected boolean")
        attributes.append(
            AttributeSpec(
                name=_string(attribute["name"], f"{item_path}.name"),
                risk_metric=_string(
                    attribute["risk_metric"], f"{item_path}.risk_metric"
                ),
                market_data_metric=_string(
                    attribute["market_data_metric"],
                    f"{item_path}.market_data_metric",
                ),
                scaling_factor=Fraction(
                    _integer(
                        attribute["scaling_numerator"],
                        f"{item_path}.scaling_numerator",
                    ),
                    denominator,
                ),
                second_order=second_order,
            )
        )
    names = [attribute.name for attribute in attributes]
    if len(names) != len(set(names)):
        raise ValidationError("$.attributes: names must be unique")

    snapshots_raw = raw["snapshots"]
    if not isinstance(snapshots_raw, list) or len(snapshots_raw) < 2:
        raise ValidationError("$.snapshots: expected at least two snapshots")
    snapshots: list[Snapshot] = []
    for index, item in enumerate(snapshots_raw):
        item_path = f"$.snapshots[{index}]"
        snapshot = _object(item, item_path)
        _fields(snapshot, {"date", "location", "instruments"}, item_path)
        try:
            snapshot_date = date.fromisoformat(
                _string(snapshot["date"], f"{item_path}.date")
            )
        except ValueError as exc:
            raise ValidationError(f"{item_path}.date: expected ISO date") from exc
        location = _string(snapshot["location"], f"{item_path}.location")
        if location not in {"results", "exit_results"}:
            raise ValidationError(f"{item_path}.location: unsupported location")
        instruments_raw = _object(snapshot["instruments"], f"{item_path}.instruments")
        if not instruments_raw:
            raise ValidationError(f"{item_path}.instruments: must not be empty")
        instruments: dict[str, dict[str, int]] = {}
        for instrument_name, metrics_raw in instruments_raw.items():
            name = _string(instrument_name, f"{item_path}.instruments key")
            metrics_obj = _object(
                metrics_raw, f"{item_path}.instruments.{instrument_name}"
            )
            instruments[name] = {
                _string(metric, f"{item_path}.metric key"): _integer(
                    metric_value, f"{item_path}.instruments.{instrument_name}.{metric}"
                )
                for metric, metric_value in metrics_obj.items()
            }
        snapshots.append(Snapshot(snapshot_date, location, instruments))
    snapshot_dates = [snapshot.date for snapshot in snapshots]
    if snapshot_dates != sorted(snapshot_dates):
        raise ValidationError("$.snapshots: dates must be increasing")
    snapshot_keys = [(snapshot.date, snapshot.location) for snapshot in snapshots]
    if len(snapshot_keys) != len(set(snapshot_keys)):
        raise ValidationError(
            "$.snapshots: each date/location pair must be unique"
        )
    distinct_dates = sorted(set(snapshot_dates))
    if len(distinct_dates) < 2:
        raise ValidationError("$.snapshots: expected at least two distinct dates")
    first_date = distinct_dates[0]
    if (first_date, "results") not in snapshot_keys:
        raise ValidationError("$.snapshots: initial date must contain results")
    for snapshot_index, snapshot in enumerate(snapshots):
        for instrument_name, metrics in snapshot.instruments.items():
            for attribute in attributes:
                required_metrics = {attribute.market_data_metric}
                if snapshot.location == "results":
                    required_metrics.add(attribute.risk_metric)
                missing = required_metrics.difference(metrics)
                if missing:
                    raise ValidationError(
                        f"$.snapshots[{snapshot_index}].instruments."
                        f"{instrument_name}: missing metrics {sorted(missing)}"
                    )

    results_by_date = {
        snapshot.date: snapshot.instruments
        for snapshot in snapshots
        if snapshot.location == "results"
    }
    exits_by_date = {
        snapshot.date: snapshot.instruments
        for snapshot in snapshots
        if snapshot.location == "exit_results"
    }
    for current_date in distinct_dates[1:]:
        previous_date = distinct_dates[distinct_dates.index(current_date) - 1]
        previous = results_by_date.get(previous_date)
        current = results_by_date.get(current_date, {})
        exits = exits_by_date.get(current_date, {})
        overlap = set(current).intersection(exits)
        if overlap:
            raise ValidationError(
                f"$.snapshots: {current_date.isoformat()} instruments cannot be "
                f"both current and exited: {sorted(overlap)}"
            )
        if previous is None:
            if exits:
                raise ValidationError(
                    f"$.snapshots: {current_date.isoformat()} has exit results "
                    "without previous-date results"
                )
            continue
        unaccounted = set(previous).difference(current).difference(exits)
        if unaccounted:
            raise ValidationError(
                f"$.snapshots: {current_date.isoformat()} does not account for "
                f"previous instruments {sorted(unaccounted)}"
            )
        orphan_exits = set(exits).difference(previous)
        if orphan_exits:
            raise ValidationError(
                f"$.snapshots: {current_date.isoformat()} exit results contain "
                f"non-previous instruments {sorted(orphan_exits)}"
            )

    expected_output_raw = _object(raw["expected_output"], "$.expected_output")
    expected_output: dict[str, dict[str, str]] = {}
    expected_dates = {day.isoformat() for day in distinct_dates[1:]}
    for attribute_name, series_raw in expected_output_raw.items():
        series = _object(series_raw, f"$.expected_output.{attribute_name}")
        normalized_series: dict[str, str] = {}
        for day, amount in series.items():
            day_text = _string(day, "$.expected_output date")
            try:
                date.fromisoformat(day_text)
            except ValueError as exc:
                raise ValidationError(
                    f"$.expected_output.{attribute_name}: invalid ISO date"
                ) from exc
            amount_text = _string(
                amount, f"$.expected_output.{attribute_name}.{day}"
            )
            try:
                Fraction(amount_text)
            except (ValueError, ZeroDivisionError) as exc:
                raise ValidationError(
                    f"$.expected_output.{attribute_name}.{day}: invalid rational"
                ) from exc
            normalized_series[day_text] = amount_text
        if set(normalized_series) != expected_dates:
            raise ValidationError(
                f"$.expected_output.{attribute_name}: dates do not match snapshots"
            )
        expected_output[attribute_name] = normalized_series
    if set(expected_output) != set(names):
        raise ValidationError("$.expected_output: attribute names do not match")

    return ConformanceModel(
        source=path.resolve(),
        raw=raw,
        package_name=_string(upstream["package_name"], "$.upstream.package_name"),
        distribution_version=_string(
            upstream["distribution_version"], "$.upstream.distribution_version"
        ),
        module=_string(upstream["module"], "$.upstream.module"),
        symbol=symbol,
        method_source_sha256=source_digest,
        attributes=tuple(attributes),
        snapshots=tuple(snapshots),
        expected_output=expected_output,
    )


class _Portfolio:
    def __init__(self, instruments: tuple[str, ...]):
        self.all_instruments = instruments
        self._instruments = frozenset(instruments)

    def __contains__(self, instrument: str) -> bool:
        return instrument in self._instruments


class _RiskResult:
    def __init__(self, instruments: dict[str, dict[str, int]]):
        self.portfolio = _Portfolio(tuple(instruments))
        self._instruments = instruments

    def __getitem__(self, instrument: str) -> dict[str, int]:
        return self._instruments[instrument]


def _fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _method_source(method: Any) -> str:
    source = textwrap.dedent(inspect.getsource(method))
    return source.replace("\r\n", "\n").replace("\r", "\n")


def method_source_sha256(method: Any) -> str:
    return hashlib.sha256(_method_source(method).encode("utf-8")).hexdigest()


def _runtime_subject(model: ConformanceModel) -> SimpleNamespace:
    results: dict[date, _RiskResult] = {}
    exit_results: dict[date, _RiskResult] = {}
    for snapshot in model.snapshots:
        destination = results if snapshot.location == "results" else exit_results
        destination[snapshot.date] = _RiskResult(snapshot.instruments)
    attributes = [
        SimpleNamespace(
            attribute_name=attribute.name,
            attribute_metric=attribute.risk_metric,
            market_data_metric=attribute.market_data_metric,
            scaling_factor=float(attribute.scaling_factor),
            second_order=attribute.second_order,
        )
        for attribute in model.attributes
    ]
    return SimpleNamespace(
        pnl_explain_def=SimpleNamespace(attributes=attributes),
        results=results,
        trade_exit_risk_results=exit_results,
    )


def _canonicalize_runtime_output(value: Any) -> dict[str, dict[str, str]]:
    if not isinstance(value, dict):
        raise ValidationError("GS Quant pnl_explain returned a non-object")
    output: dict[str, dict[str, str]] = {}
    for attribute_name, series_value in value.items():
        if not isinstance(attribute_name, str) or not isinstance(series_value, dict):
            raise ValidationError("GS Quant pnl_explain returned an invalid series")
        series: dict[str, str] = {}
        for day, amount in series_value.items():
            if not isinstance(day, date) or isinstance(amount, bool) or not isinstance(
                amount, (int, float)
            ):
                raise ValidationError("GS Quant pnl_explain returned invalid values")
            series[day.isoformat()] = _fraction_text(Fraction(str(amount)))
        output[attribute_name] = series
    return output


def recompute_lfv_output(model: ConformanceModel) -> dict[str, dict[str, str]]:
    results = {
        snapshot.date: snapshot.instruments
        for snapshot in model.snapshots
        if snapshot.location == "results"
    }
    exit_results = {
        snapshot.date: snapshot.instruments
        for snapshot in model.snapshots
        if snapshot.location == "exit_results"
    }
    dates = sorted(set(results).union(exit_results))
    output: dict[str, dict[str, str]] = {}
    for attribute in model.attributes:
        cumulative = Fraction(0)
        series: dict[str, str] = {}
        for index in range(1, len(dates)):
            current_date = dates[index]
            previous_date = dates[index - 1]
            if previous_date not in results:
                series[current_date.isoformat()] = _fraction_text(cumulative)
                continue
            increment = Fraction(0)
            for instrument, previous_metrics in results[previous_date].items():
                previous_risk = previous_metrics[attribute.risk_metric]
                if previous_risk == 0:
                    continue
                previous_market = previous_metrics[attribute.market_data_metric]
                if current_date in results and instrument in results[current_date]:
                    current_metrics = results[current_date][instrument]
                else:
                    current_metrics = exit_results[current_date][instrument]
                market_move = current_metrics[attribute.market_data_metric] - previous_market
                term = attribute.scaling_factor * previous_risk * market_move
                if attribute.second_order:
                    term *= Fraction(market_move, 2)
                increment += term
            cumulative += increment
            series[current_date.isoformat()] = _fraction_text(cumulative)
        output[attribute.name] = series
    return output


def _path_coverage(
    model: ConformanceModel,
    lfv_output: dict[str, dict[str, str]],
) -> dict[str, bool]:
    results = {
        snapshot.date: snapshot.instruments
        for snapshot in model.snapshots
        if snapshot.location == "results"
    }
    exits = {
        snapshot.date: snapshot.instruments
        for snapshot in model.snapshots
        if snapshot.location == "exit_results"
    }
    dates = sorted(set(results).union(exits))
    previous_results = [results[day] for day in dates[:-1] if day in results]
    mixed_current_exit = False
    portfolio_transition = False
    for index in range(1, len(dates)):
        previous = results.get(dates[index - 1])
        if previous is None:
            continue
        current = results.get(dates[index], {})
        exited = exits.get(dates[index], {})
        if set(previous).intersection(current) and set(previous).intersection(exited):
            mixed_current_exit = True
        if set(previous) != set(current):
            portfolio_transition = True
    return {
        "first_order_executed": any(
            not attribute.second_order for attribute in model.attributes
        ),
        "second_order_executed": any(
            attribute.second_order for attribute in model.attributes
        ),
        "exit_path_executed": bool(exits),
        "multi_instrument_aggregation_executed": any(
            len(instruments) > 1 for instruments in previous_results
        ),
        "mixed_current_exit_executed": mixed_current_exit,
        "zero_risk_skip_executed": any(
            metrics[attribute.risk_metric] == 0
            for instruments in previous_results
            for metrics in instruments.values()
            for attribute in model.attributes
        ),
        "portfolio_transition_executed": portfolio_transition,
        "fractional_output_executed": any(
            Fraction(amount).denominator != 1
            for series in lfv_output.values()
            for amount in series.values()
        ),
    }


def run_conformance(
    model: ConformanceModel,
    *,
    backtest_type: type[Any] | None = None,
    distribution_version: str | None = None,
) -> dict[str, Any]:
    try:
        if backtest_type is None:
            module = importlib.import_module(model.module)
            class_name, method_name = model.symbol.split(".", 1)
            backtest_type = getattr(module, class_name)
        else:
            _, method_name = model.symbol.split(".", 1)
        method = getattr(backtest_type, method_name)
        actual_version = distribution_version or version(model.package_name)
    except (ImportError, AttributeError, PackageNotFoundError) as exc:
        raise ValidationError(
            f"unable to load pinned runtime {model.package_name} "
            f"{model.distribution_version}"
        ) from exc
    if actual_version != model.distribution_version:
        raise ValidationError(
            f"expected {model.package_name} {model.distribution_version}, got {actual_version}"
        )
    source_digest = method_source_sha256(method)
    if source_digest != model.method_source_sha256:
        raise ValidationError(
            "GS Quant pnl_explain source digest does not match the pinned contract"
        )

    actual_output = _canonicalize_runtime_output(method(_runtime_subject(model)))
    lfv_output = recompute_lfv_output(model)
    if lfv_output != model.expected_output:
        raise ValidationError("fixture expected_output does not match LFV recomputation")
    if actual_output != lfv_output:
        raise ValidationError("GS Quant runtime output does not match LFV recomputation")

    path_coverage = _path_coverage(model, lfv_output)
    if not all(path_coverage.values()):
        missing_paths = sorted(
            name for name, executed in path_coverage.items() if not executed
        )
        raise ValidationError(
            f"conformance fixture does not execute required paths {missing_paths}"
        )

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "upstream": {
            "package_name": model.package_name,
            "distribution_version": actual_version,
            "module": model.module,
            "symbol": model.symbol,
            "method_source_sha256": source_digest,
        },
        "model_sha256": hashlib.sha256(canonical_bytes(model.raw)).hexdigest(),
        "runtime_output": actual_output,
        "lfv_recomputed_output": lfv_output,
        "checks": {
            "version_bound": True,
            "source_bound": True,
            **path_coverage,
            "runtime_matches_lfv": True,
        },
        "coverage_status": "DIRECT_TESTED_CONTROLLED_INPUT",
    }
    report["report_sha256"] = hashlib.sha256(canonical_bytes(report)).hexdigest()
    return report


def verify_conformance(
    model: ConformanceModel,
    report: Any,
    *,
    backtest_type: type[Any] | None = None,
    distribution_version: str | None = None,
) -> dict[str, Any]:
    expected = run_conformance(
        model,
        backtest_type=backtest_type,
        distribution_version=distribution_version,
    )
    if report != expected:
        raise ValidationError("GS Quant conformance report does not match replay")
    return expected
