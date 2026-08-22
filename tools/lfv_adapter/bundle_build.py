from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .canonical import (
    CANONICAL_FORMAT,
    canonical_bytes,
    hash_bytes,
    load_json,
    make_artifact_ref,
    make_document_digest,
)
from .errors import ExecutionError, ValidationError
from .ledger import find_selected_trial, load_anchor, load_ledger, verify_anchor
from .paths import logical_path
from .spec import DatasetSpec, ExperimentSpec, FeatureSpec

from .bundle_schema import BUNDLE_DIGEST_SCHEMA, BUNDLE_SCHEMA
from .bundle_verify import verify_bundle

if TYPE_CHECKING:
    from .rfc3161 import Rfc3161Trust


@dataclass(frozen=True)
class BuildResult:
    spec: ExperimentSpec
    bundle: dict[str, Any]
    result_payload: Any
    lean_source: str


def _raw_file_descriptor(spec: ExperimentSpec, relative: str) -> dict[str, Any]:
    path = spec.resolve(relative)
    raw = path.read_bytes()
    return {
        "path": logical_path(spec.root, path),
        "size": len(raw),
        "content_digest": {
            "algorithm": spec.hash_algorithm,
            "digest": hash_bytes(spec.hash_algorithm, raw),
        },
    }


def _artifact_descriptor(
    *,
    kind: str,
    schema_id: str,
    payload: Any,
    algorithm: str,
    source: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ref, size = make_artifact_ref(
        kind=kind,
        schema_id=schema_id,
        payload=payload,
        algorithm=algorithm,
    )
    descriptor: dict[str, Any] = {
        "ref": ref,
        "canonical_format": CANONICAL_FORMAT,
        "serialized_size": size,
    }
    if source is not None:
        descriptor["source"] = source
    if extra:
        descriptor.update(extra)
    return descriptor


def compute_code_artifact(spec: ExperimentSpec) -> dict[str, Any]:
    files = [
        _raw_file_descriptor(spec, relative)
        for relative in sorted(spec.code.paths)
    ]
    return _artifact_descriptor(
        kind="sourceCode",
        schema_id=spec.code.schema_id,
        payload={"files": files},
        algorithm=spec.hash_algorithm,
        extra={"files": files},
    )


def compute_dataset_artifact(
    spec: ExperimentSpec, dataset: DatasetSpec
) -> dict[str, Any]:
    file_descriptor = _raw_file_descriptor(spec, dataset.path)
    payload = {
        "dataset_id": dataset.id,
        "file": file_descriptor,
    }
    return _artifact_descriptor(
        kind="dataset",
        schema_id=dataset.schema_id,
        payload=payload,
        algorithm=spec.hash_algorithm,
        source=file_descriptor["path"],
        extra={"raw_file": file_descriptor},
    )


def compute_json_artifact(
    spec: ExperimentSpec,
    *,
    relative: str,
    schema_id: str,
    kind: str,
) -> tuple[dict[str, Any], Any]:
    path = spec.resolve(relative)
    payload = load_json(path)
    descriptor = _artifact_descriptor(
        kind=kind,
        schema_id=schema_id,
        payload=payload,
        algorithm=spec.hash_algorithm,
        source=logical_path(spec.root, path),
    )
    return descriptor, payload


def compute_preregistration_artifacts(
    spec: ExperimentSpec,
) -> tuple[dict[str, Any], dict[str, Any]]:
    code = compute_code_artifact(spec)
    parameters, _ = compute_json_artifact(
        spec,
        relative=spec.parameters.path,
        schema_id=spec.parameters.schema_id,
        kind="parameterSet",
    )
    return code["ref"], parameters["ref"]


def resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValidationError(f"invalid JSON pointer: {pointer!r}")
    current = document
    for raw_token in pointer.split("/")[1:]:
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise ValidationError(
                    f"JSON pointer {pointer!r}: missing object key {token!r}"
                )
            current = current[token]
        elif isinstance(current, list):
            if token == "-" or not token.isdigit():
                raise ValidationError(
                    f"JSON pointer {pointer!r}: invalid array index {token!r}"
                )
            index = int(token)
            if index >= len(current):
                raise ValidationError(
                    f"JSON pointer {pointer!r}: array index out of range"
                )
            current = current[index]
        else:
            raise ValidationError(
                f"JSON pointer {pointer!r}: traverses a scalar value"
            )
    return current


def run_empirical_command(spec: ExperimentSpec) -> tuple[Any, dict[str, Any]]:
    argv = [
        sys.executable if argument == "{python}" else argument
        for argument in spec.execution.argv
    ]
    environment = os.environ.copy()
    environment["PYTHONHASHSEED"] = "0"
    try:
        completed = subprocess.run(
            argv,
            cwd=spec.root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            timeout=spec.execution.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExecutionError(
            f"empirical command exceeded {spec.execution.timeout_seconds} seconds"
        ) from exc
    except OSError as exc:
        raise ExecutionError(f"failed to execute empirical command: {exc}") from exc

    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        raise ExecutionError(
            f"empirical command exited with {completed.returncode}: "
            f"{stderr or '<empty stderr>'}"
        )
    stdout = completed.stdout.strip()
    if not stdout:
        raise ExecutionError("empirical command emitted empty stdout")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ExecutionError(
            f"empirical command stdout is not JSON: {exc}"
        ) from exc
    # canonical_bytes performs the restricted-value validation, including
    # floating-point rejection.
    canonical_bytes(payload)
    metadata = {
        "argv": list(spec.execution.argv),
        "return_code": completed.returncode,
        "stderr": completed.stderr,
    }
    return payload, metadata


def _validate_temporal_lineage(
    spec: ExperimentSpec,
    feature: FeatureSpec,
) -> None:
    datasets = spec.dataset_by_id
    features = spec.feature_by_name
    for reference in feature.inputs:
        kind, _, target = reference.partition(":")
        if kind == "dataset":
            if datasets[target].available_at > feature.generated_at:
                raise ValidationError(
                    f"feature {feature.name!r} was generated before "
                    f"dataset {target!r} was available"
                )
        elif kind == "feature":
            if features[target].generated_at > feature.generated_at:
                raise ValidationError(
                    f"feature {feature.name!r} depends on later "
                    f"feature {target!r}"
                )


def _build_feature_descriptors(
    spec: ExperimentSpec,
    result_payload: Any,
    dataset_descriptors: dict[str, dict[str, Any]],
    code_descriptor: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    features: dict[str, dict[str, Any]] = {}
    for feature in spec.topological_features():
        _validate_temporal_lineage(spec, feature)
        value = resolve_pointer(result_payload, feature.pointer)
        input_hashes: list[str] = []
        for reference in feature.inputs:
            kind, _, target = reference.partition(":")
            if kind == "dataset":
                input_hashes.append(
                    dataset_descriptors[target]["artifact"]["ref"]["digest"]
                )
            else:
                input_hashes.append(
                    features[target]["artifact"]["ref"]["digest"]
                )
        code_hash = code_descriptor["ref"]["digest"]
        artifact_payload = {
            "name": feature.name,
            "value": value,
            "lineage": {
                "input_hashes": input_hashes,
                "code_hash": code_hash,
                "generated_at": feature.generated_at,
            },
        }
        artifact = _artifact_descriptor(
            kind="feature",
            schema_id=feature.schema_id,
            payload=artifact_payload,
            algorithm=spec.hash_algorithm,
        )
        features[feature.name] = {
            "name": feature.name,
            "pointer": feature.pointer,
            "generated_at": feature.generated_at,
            "inputs": list(feature.inputs),
            "input_hashes": input_hashes,
            "code_hash": code_hash,
            "artifact": artifact,
        }
    return features


def build_bundle(
    spec: ExperimentSpec,
    *,
    allow_local_anchor: bool = False,
    rfc3161_trust: Rfc3161Trust | None = None,
) -> tuple[dict[str, Any], Any]:
    code = compute_code_artifact(spec)
    datasets: dict[str, dict[str, Any]] = {}
    for dataset in spec.datasets:
        datasets[dataset.id] = {
            "id": dataset.id,
            "observed_at": dataset.observed_at,
            "available_at": dataset.available_at,
            "artifact": compute_dataset_artifact(spec, dataset),
        }
    parameters, _ = compute_json_artifact(
        spec,
        relative=spec.parameters.path,
        schema_id=spec.parameters.schema_id,
        kind="parameterSet",
    )
    environment, _ = compute_json_artifact(
        spec,
        relative=spec.environment.path,
        schema_id=spec.environment.schema_id,
        kind="environment",
    )

    for dataset_id in spec.decision.dataset_ids:
        if datasets[dataset_id]["available_at"] > spec.decision.decision_time:
            raise ValidationError(
                f"dataset {dataset_id!r} was not available by the decision time"
            )
    for feature_name in spec.decision.feature_names:
        if (
            spec.feature_by_name[feature_name].generated_at
            > spec.decision.decision_time
        ):
            raise ValidationError(
                f"feature {feature_name!r} was not generated by the decision time"
            )

    ledger = load_ledger(spec.resolve(spec.ledger_path))
    selected_index, _selected_trial = find_selected_trial(
        ledger,
        strategy_id=spec.decision.strategy_id,
        parameters=parameters["ref"],
        code=code["ref"],
        cutoff_time=spec.decision.decision_time,
    )
    anchor = verify_anchor(
        load_anchor(
            spec.resolve(spec.anchor_path),
            allow_local=allow_local_anchor,
            rfc3161_trust=rfc3161_trust,
        ),
        ledger,
        cutoff_time=spec.decision.decision_time,
        allow_local=allow_local_anchor,
        rfc3161_trust=rfc3161_trust,
    )

    result_payload, execution = run_empirical_command(spec)
    result_artifact = _artifact_descriptor(
        kind="result",
        schema_id=spec.execution.result_schema_id,
        payload=result_payload,
        algorithm=spec.hash_algorithm,
    )
    metric_value = resolve_pointer(
        result_payload, spec.decision.metric_pointer
    )
    if isinstance(metric_value, bool) or not isinstance(metric_value, int):
        raise ValidationError(
            "selected metric must be an integer for Lean Scalar"
        )

    features = _build_feature_descriptors(
        spec, result_payload, datasets, code
    )
    used_datasets = [
        datasets[dataset_id] for dataset_id in spec.decision.dataset_ids
    ]
    used_features = [
        features[name] for name in spec.decision.feature_names
    ]

    core: dict[str, Any] = {
        "schema_version": BUNDLE_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "experiment": {
            "name": spec.name,
            "lean_namespace": spec.namespace,
            "hash_algorithm": spec.hash_algorithm,
        },
        "artifacts": {
            "code": code,
            "datasets": [
                datasets[dataset.id] for dataset in spec.datasets
            ],
            "parameters": parameters,
            "environment": environment,
            "result": result_artifact,
            "features": [
                features[feature.name]
                for feature in spec.topological_features()
            ],
        },
        "decision": {
            "strategy_id": spec.decision.strategy_id,
            "decision_time": spec.decision.decision_time,
            "dataset_ids": list(spec.decision.dataset_ids),
            "feature_names": list(spec.decision.feature_names),
            "datasets": [
                {
                    "id": item["id"],
                    "observed_at": item["observed_at"],
                    "available_at": item["available_at"],
                    "content_hash": item["artifact"]["ref"]["digest"],
                }
                for item in used_datasets
            ],
            "features": [
                {
                    "name": item["name"],
                    "input_hashes": item["input_hashes"],
                    "generated_at": item["generated_at"],
                    "code_hash": item["code_hash"],
                    "output_hash": item["artifact"]["ref"]["digest"],
                }
                for item in used_features
            ],
            "parameter_hash": parameters["ref"]["digest"],
        },
        "ledger": ledger,
        "anchor": anchor,
        "selected_trial_index": selected_index,
        "claim": {
            "result_hash": result_artifact["ref"]["digest"],
            "metric_name": spec.decision.metric_name,
            "metric_value": metric_value,
        },
        "execution": execution,
    }
    bundle_digest = make_document_digest(
        domain="certificateBundle",
        schema_id=BUNDLE_DIGEST_SCHEMA,
        payload=core,
        algorithm=spec.hash_algorithm,
    )
    bundle = deepcopy(core)
    bundle["bundle_digest"] = bundle_digest
    verify_bundle(
        bundle,
        allow_local_anchor=allow_local_anchor,
        rfc3161_trust=rfc3161_trust,
    )
    return bundle, result_payload
