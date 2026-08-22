from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import SUPPORTED_HASH_ALGORITHMS, load_json
from .errors import ValidationError
from .paths import resolve_under

SPEC_SCHEMA = "lfv-experiment-spec-v1"
_NAMESPACE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected an object")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{path}: expected an array")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected a non-empty string")
    return value


def _nat(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected a non-negative integer")
    return value


def _reject_unknown(obj: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        raise ValidationError(f"{path}: unknown fields: {sorted(unknown)}")


@dataclass(frozen=True)
class CodeSpec:
    schema_id: str
    paths: tuple[str, ...]


@dataclass(frozen=True)
class DatasetSpec:
    id: str
    path: str
    schema_id: str
    observed_at: int
    available_at: int


@dataclass(frozen=True)
class JsonArtifactSpec:
    path: str
    schema_id: str


@dataclass(frozen=True)
class ExecutionSpec:
    argv: tuple[str, ...]
    timeout_seconds: int
    result_schema_id: str


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    pointer: str
    schema_id: str
    generated_at: int
    inputs: tuple[str, ...]


@dataclass(frozen=True)
class DecisionSpec:
    strategy_id: str
    decision_time: int
    metric_name: str
    metric_pointer: str
    dataset_ids: tuple[str, ...]
    feature_names: tuple[str, ...]


@dataclass(frozen=True)
class ExperimentSpec:
    source_path: Path
    root: Path
    name: str
    namespace: str
    hash_algorithm: str
    code: CodeSpec
    datasets: tuple[DatasetSpec, ...]
    parameters: JsonArtifactSpec
    environment: JsonArtifactSpec
    execution: ExecutionSpec
    features: tuple[FeatureSpec, ...]
    decision: DecisionSpec
    ledger_path: str
    anchor_path: str

    def resolve(self, relative: str, *, must_exist: bool = True) -> Path:
        return resolve_under(self.root, relative, must_exist=must_exist)

    @property
    def dataset_by_id(self) -> dict[str, DatasetSpec]:
        return {dataset.id: dataset for dataset in self.datasets}

    @property
    def feature_by_name(self) -> dict[str, FeatureSpec]:
        return {feature.name: feature for feature in self.features}

    def topological_features(self) -> tuple[FeatureSpec, ...]:
        features = self.feature_by_name
        datasets = self.dataset_by_id
        state: dict[str, int] = {}
        ordered: list[FeatureSpec] = []

        def visit(name: str, stack: list[str]) -> None:
            mark = state.get(name, 0)
            if mark == 2:
                return
            if mark == 1:
                cycle = " -> ".join(stack + [name])
                raise ValidationError(f"feature dependency cycle: {cycle}")
            state[name] = 1
            feature = features[name]
            for reference in feature.inputs:
                kind, sep, target = reference.partition(":")
                if not sep or not target:
                    raise ValidationError(
                        f"feature {name!r}: input must be dataset:<id> or feature:<name>"
                    )
                if kind == "dataset":
                    if target not in datasets:
                        raise ValidationError(
                            f"feature {name!r}: unknown dataset input {target!r}"
                        )
                elif kind == "feature":
                    if target not in features:
                        raise ValidationError(
                            f"feature {name!r}: unknown feature input {target!r}"
                        )
                    visit(target, stack + [name])
                else:
                    raise ValidationError(
                        f"feature {name!r}: unsupported input kind {kind!r}"
                    )
            state[name] = 2
            ordered.append(feature)

        for feature in self.features:
            visit(feature.name, [])
        return tuple(ordered)


def _parse_code(value: Any) -> CodeSpec:
    obj = _object(value, "$.code")
    _reject_unknown(obj, {"schema_id", "paths"}, "$.code")
    paths = tuple(_string(item, "$.code.paths[]") for item in _list(obj.get("paths"), "$.code.paths"))
    if not paths:
        raise ValidationError("$.code.paths: expected at least one file")
    if len(set(paths)) != len(paths):
        raise ValidationError("$.code.paths: duplicate paths are not allowed")
    return CodeSpec(_string(obj.get("schema_id"), "$.code.schema_id"), paths)


def _parse_datasets(value: Any) -> tuple[DatasetSpec, ...]:
    datasets: list[DatasetSpec] = []
    for index, raw in enumerate(_list(value, "$.datasets")):
        path = f"$.datasets[{index}]"
        obj = _object(raw, path)
        _reject_unknown(
            obj,
            {"id", "path", "schema_id", "observed_at", "available_at"},
            path,
        )
        observed = _nat(obj.get("observed_at"), f"{path}.observed_at")
        available = _nat(obj.get("available_at"), f"{path}.available_at")
        if observed > available:
            raise ValidationError(f"{path}: observed_at must be <= available_at")
        datasets.append(
            DatasetSpec(
                id=_string(obj.get("id"), f"{path}.id"),
                path=_string(obj.get("path"), f"{path}.path"),
                schema_id=_string(obj.get("schema_id"), f"{path}.schema_id"),
                observed_at=observed,
                available_at=available,
            )
        )
    if not datasets:
        raise ValidationError("$.datasets: expected at least one dataset")
    ids = [dataset.id for dataset in datasets]
    if len(set(ids)) != len(ids):
        raise ValidationError("$.datasets: dataset ids must be unique")
    return tuple(datasets)


def _parse_json_artifact(value: Any, path: str) -> JsonArtifactSpec:
    obj = _object(value, path)
    _reject_unknown(obj, {"path", "schema_id"}, path)
    return JsonArtifactSpec(
        path=_string(obj.get("path"), f"{path}.path"),
        schema_id=_string(obj.get("schema_id"), f"{path}.schema_id"),
    )


def _parse_execution(value: Any) -> ExecutionSpec:
    obj = _object(value, "$.execution")
    _reject_unknown(obj, {"argv", "timeout_seconds", "result_schema_id"}, "$.execution")
    argv = tuple(_string(item, "$.execution.argv[]") for item in _list(obj.get("argv"), "$.execution.argv"))
    if not argv:
        raise ValidationError("$.execution.argv: expected at least one argument")
    timeout = _nat(obj.get("timeout_seconds"), "$.execution.timeout_seconds")
    if timeout == 0:
        raise ValidationError("$.execution.timeout_seconds: must be greater than zero")
    return ExecutionSpec(
        argv=argv,
        timeout_seconds=timeout,
        result_schema_id=_string(obj.get("result_schema_id"), "$.execution.result_schema_id"),
    )


def _parse_features(value: Any) -> tuple[FeatureSpec, ...]:
    features: list[FeatureSpec] = []
    for index, raw in enumerate(_list(value, "$.features")):
        path = f"$.features[{index}]"
        obj = _object(raw, path)
        _reject_unknown(obj, {"name", "pointer", "schema_id", "generated_at", "inputs"}, path)
        pointer = _string(obj.get("pointer"), f"{path}.pointer")
        if not pointer.startswith("/"):
            raise ValidationError(f"{path}.pointer: expected an RFC 6901 JSON pointer")
        inputs = tuple(_string(item, f"{path}.inputs[]") for item in _list(obj.get("inputs"), f"{path}.inputs"))
        if not inputs:
            raise ValidationError(f"{path}.inputs: expected at least one lineage input")
        features.append(
            FeatureSpec(
                name=_string(obj.get("name"), f"{path}.name"),
                pointer=pointer,
                schema_id=_string(obj.get("schema_id"), f"{path}.schema_id"),
                generated_at=_nat(obj.get("generated_at"), f"{path}.generated_at"),
                inputs=inputs,
            )
        )
    names = [feature.name for feature in features]
    if len(set(names)) != len(names):
        raise ValidationError("$.features: feature names must be unique")
    return tuple(features)


def _parse_decision(value: Any) -> DecisionSpec:
    obj = _object(value, "$.decision")
    _reject_unknown(
        obj,
        {
            "strategy_id",
            "decision_time",
            "metric_name",
            "metric_pointer",
            "dataset_ids",
            "feature_names",
        },
        "$.decision",
    )
    pointer = _string(obj.get("metric_pointer"), "$.decision.metric_pointer")
    if not pointer.startswith("/"):
        raise ValidationError("$.decision.metric_pointer: expected an RFC 6901 JSON pointer")
    dataset_ids = tuple(
        _string(item, "$.decision.dataset_ids[]")
        for item in _list(obj.get("dataset_ids"), "$.decision.dataset_ids")
    )
    if not dataset_ids:
        raise ValidationError("$.decision.dataset_ids: expected at least one dataset")
    return DecisionSpec(
        strategy_id=_string(obj.get("strategy_id"), "$.decision.strategy_id"),
        decision_time=_nat(obj.get("decision_time"), "$.decision.decision_time"),
        metric_name=_string(obj.get("metric_name"), "$.decision.metric_name"),
        metric_pointer=pointer,
        dataset_ids=dataset_ids,
        feature_names=tuple(
            _string(item, "$.decision.feature_names[]")
            for item in _list(obj.get("feature_names"), "$.decision.feature_names")
        ),
    )


def load_experiment_spec(path: Path) -> ExperimentSpec:
    source_path = path.resolve()
    raw = _object(load_json(source_path), "$")
    _reject_unknown(
        raw,
        {
            "schema_version",
            "name",
            "namespace",
            "hash_algorithm",
            "code",
            "datasets",
            "parameters",
            "environment",
            "execution",
            "features",
            "decision",
            "ledger_path",
            "anchor_path",
        },
        "$",
    )
    if raw.get("schema_version") != SPEC_SCHEMA:
        raise ValidationError(
            f"$.schema_version: expected {SPEC_SCHEMA!r}, got {raw.get('schema_version')!r}"
        )
    namespace = _string(raw.get("namespace"), "$.namespace")
    if not _NAMESPACE_RE.fullmatch(namespace):
        raise ValidationError("$.namespace: invalid Lean namespace")
    algorithm = _string(raw.get("hash_algorithm"), "$.hash_algorithm")
    if algorithm not in SUPPORTED_HASH_ALGORITHMS:
        raise ValidationError(f"$.hash_algorithm: unsupported value {algorithm!r}")

    spec = ExperimentSpec(
        source_path=source_path,
        root=source_path.parent,
        name=_string(raw.get("name"), "$.name"),
        namespace=namespace,
        hash_algorithm=algorithm,
        code=_parse_code(raw.get("code")),
        datasets=_parse_datasets(raw.get("datasets")),
        parameters=_parse_json_artifact(raw.get("parameters"), "$.parameters"),
        environment=_parse_json_artifact(raw.get("environment"), "$.environment"),
        execution=_parse_execution(raw.get("execution")),
        features=_parse_features(raw.get("features")),
        decision=_parse_decision(raw.get("decision")),
        ledger_path=_string(raw.get("ledger_path"), "$.ledger_path"),
        anchor_path=_string(raw.get("anchor_path"), "$.anchor_path"),
    )

    dataset_ids = set(spec.dataset_by_id)
    feature_names = set(spec.feature_by_name)
    if len(set(spec.decision.dataset_ids)) != len(spec.decision.dataset_ids):
        raise ValidationError("$.decision.dataset_ids: duplicate ids are not allowed")
    if len(set(spec.decision.feature_names)) != len(spec.decision.feature_names):
        raise ValidationError("$.decision.feature_names: duplicate names are not allowed")
    unknown_datasets = set(spec.decision.dataset_ids) - dataset_ids
    unknown_features = set(spec.decision.feature_names) - feature_names
    if unknown_datasets:
        raise ValidationError(
            f"$.decision.dataset_ids: unknown datasets {sorted(unknown_datasets)}"
        )
    if unknown_features:
        raise ValidationError(
            f"$.decision.feature_names: unknown features {sorted(unknown_features)}"
        )

    # Validate every referenced path and the complete feature DAG eagerly.
    for code_path in spec.code.paths:
        resolved = spec.resolve(code_path)
        if not resolved.is_file():
            raise ValidationError(f"code path is not a file: {code_path}")
    for dataset in spec.datasets:
        resolved = spec.resolve(dataset.path)
        if not resolved.is_file():
            raise ValidationError(f"dataset path is not a file: {dataset.path}")
    for artifact in (spec.parameters, spec.environment):
        resolved = spec.resolve(artifact.path)
        if not resolved.is_file():
            raise ValidationError(f"JSON artifact path is not a file: {artifact.path}")
        load_json(resolved)
    spec.topological_features()
    return spec
