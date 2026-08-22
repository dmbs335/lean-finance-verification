from __future__ import annotations

from copy import deepcopy
from typing import Any

from .bundle_schema import BUNDLE_DIGEST_SCHEMA, BUNDLE_SCHEMA
from .canonical import (
    CANONICAL_FORMAT,
    make_document_digest,
    validate_artifact_ref,
)
from .errors import ValidationError
from .ledger import verify_anchor, verify_ledger

def _validate_descriptor_ref(descriptor: Any, path: str) -> dict[str, str]:
    if not isinstance(descriptor, dict) or "ref" not in descriptor:
        raise ValidationError(f"{path}: missing artifact ref")
    if descriptor.get("canonical_format") != CANONICAL_FORMAT:
        raise ValidationError(f"{path}.canonical_format: unexpected value")
    serialized_size = descriptor.get("serialized_size")
    if (
        isinstance(serialized_size, bool)
        or not isinstance(serialized_size, int)
        or serialized_size < 0
    ):
        raise ValidationError(f"{path}.serialized_size: expected a non-negative integer")
    return validate_artifact_ref(descriptor["ref"], f"{path}.ref")


def verify_bundle(bundle: Any, *, allow_local_anchor: bool = False) -> dict[str, Any]:
    if not isinstance(bundle, dict):
        raise ValidationError("bundle: expected an object")
    required = {
        "schema_version",
        "canonical_format",
        "experiment",
        "artifacts",
        "decision",
        "ledger",
        "anchor",
        "selected_trial_index",
        "claim",
        "execution",
        "bundle_digest",
    }
    missing = required - set(bundle)
    unknown = set(bundle) - required
    if missing:
        raise ValidationError(f"bundle: missing fields: {sorted(missing)}")
    if unknown:
        raise ValidationError(f"bundle: unknown fields: {sorted(unknown)}")
    if bundle["schema_version"] != BUNDLE_SCHEMA:
        raise ValidationError(f"bundle.schema_version: expected {BUNDLE_SCHEMA!r}")
    if bundle["canonical_format"] != CANONICAL_FORMAT:
        raise ValidationError(f"bundle.canonical_format: expected {CANONICAL_FORMAT!r}")
    experiment = bundle["experiment"]
    if not isinstance(experiment, dict):
        raise ValidationError("bundle.experiment: expected an object")
    algorithm = experiment.get("hash_algorithm")
    digest_ref = validate_artifact_ref(bundle["bundle_digest"], "bundle.bundle_digest")
    if digest_ref["schema_id"] != BUNDLE_DIGEST_SCHEMA:
        raise ValidationError("bundle.bundle_digest: unexpected schema id")
    if digest_ref["algorithm"] != algorithm:
        raise ValidationError("bundle.bundle_digest: algorithm mismatch")
    core = {key: deepcopy(value) for key, value in bundle.items() if key != "bundle_digest"}
    expected_digest = make_document_digest(
        domain="certificateBundle",
        schema_id=BUNDLE_DIGEST_SCHEMA,
        payload=core,
        algorithm=algorithm,
    )
    if expected_digest != digest_ref:
        raise ValidationError("bundle.bundle_digest: canonical digest mismatch")

    artifacts = bundle["artifacts"]
    if not isinstance(artifacts, dict):
        raise ValidationError("bundle.artifacts: expected an object")
    code_ref = _validate_descriptor_ref(artifacts.get("code"), "bundle.artifacts.code")
    parameter_ref = _validate_descriptor_ref(
        artifacts.get("parameters"), "bundle.artifacts.parameters"
    )
    _validate_descriptor_ref(
        artifacts.get("environment"), "bundle.artifacts.environment"
    )
    result_ref = _validate_descriptor_ref(artifacts.get("result"), "bundle.artifacts.result")
    dataset_entries = artifacts.get("datasets")
    feature_entries = artifacts.get("features")
    if not isinstance(dataset_entries, list) or not dataset_entries:
        raise ValidationError("bundle.artifacts.datasets: expected a non-empty array")
    if not isinstance(feature_entries, list):
        raise ValidationError("bundle.artifacts.features: expected an array")
    datasets: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(dataset_entries):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValidationError(f"bundle.artifacts.datasets[{index}]: invalid dataset")
        _validate_descriptor_ref(item.get("artifact"), f"bundle.artifacts.datasets[{index}].artifact")
        datasets[item["id"]] = item
    features: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(feature_entries):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValidationError(f"bundle.artifacts.features[{index}]: invalid feature")
        _validate_descriptor_ref(item.get("artifact"), f"bundle.artifacts.features[{index}].artifact")
        features[item["name"]] = item

    decision = bundle["decision"]
    if not isinstance(decision, dict):
        raise ValidationError("bundle.decision: expected an object")
    decision_time = decision.get("decision_time")
    if isinstance(decision_time, bool) or not isinstance(decision_time, int) or decision_time < 0:
        raise ValidationError("bundle.decision.decision_time: invalid timestamp")
    if decision.get("parameter_hash") != parameter_ref["digest"]:
        raise ValidationError("bundle.decision.parameter_hash does not match parameters")
    for dataset in decision.get("datasets", []):
        dataset_id = dataset.get("id")
        if dataset_id not in datasets:
            raise ValidationError(f"decision references unknown dataset {dataset_id!r}")
        source = datasets[dataset_id]
        if dataset.get("content_hash") != source["artifact"]["ref"]["digest"]:
            raise ValidationError(f"decision dataset {dataset_id!r}: hash mismatch")
        if dataset.get("observed_at") != source.get("observed_at"):
            raise ValidationError(f"decision dataset {dataset_id!r}: observed_at mismatch")
        if dataset.get("available_at") != source.get("available_at"):
            raise ValidationError(f"decision dataset {dataset_id!r}: available_at mismatch")
        if dataset.get("available_at", decision_time + 1) > decision_time:
            raise ValidationError(f"decision dataset {dataset_id!r}: future information")
    if decision.get("dataset_ids") != [item.get("id") for item in decision.get("datasets", [])]:
        raise ValidationError("decision.dataset_ids does not match decision.datasets")
    feature_times: dict[str, int] = {}
    feature_hashes: dict[str, str] = {}
    for name, feature in features.items():
        generated = feature.get("generated_at")
        if isinstance(generated, bool) or not isinstance(generated, int) or generated < 0:
            raise ValidationError(f"feature {name!r}: invalid generated_at")
        feature_times[name] = generated
        expected_input_hashes: list[str] = []
        for reference in feature.get("inputs", []):
            kind, _, target = reference.partition(":")
            if kind == "dataset":
                if target not in datasets or datasets[target]["available_at"] > generated:
                    raise ValidationError(f"feature {name!r}: temporally invalid dataset input")
                expected_input_hashes.append(datasets[target]["artifact"]["ref"]["digest"])
            elif kind == "feature":
                if target not in feature_times:
                    # Artifacts are required to be emitted in topological order.
                    raise ValidationError(f"feature {name!r}: non-topological dependency")
                if feature_times[target] > generated:
                    raise ValidationError(f"feature {name!r}: later feature dependency")
                expected_input_hashes.append(feature_hashes[target])
            else:
                raise ValidationError(f"feature {name!r}: invalid lineage reference")
        if feature.get("input_hashes") != expected_input_hashes:
            raise ValidationError(f"feature {name!r}: lineage hash mismatch")
        if feature.get("code_hash") != code_ref["digest"]:
            raise ValidationError(f"feature {name!r}: code hash mismatch")
        feature_hashes[name] = feature["artifact"]["ref"]["digest"]
    for feature in decision.get("features", []):
        name = feature.get("name")
        if name not in features:
            raise ValidationError(f"decision references unknown feature {name!r}")
        source = features[name]
        if feature.get("output_hash") != source["artifact"]["ref"]["digest"]:
            raise ValidationError(f"decision feature {name!r}: output hash mismatch")
        if feature.get("input_hashes") != source.get("input_hashes"):
            raise ValidationError(f"decision feature {name!r}: input hash mismatch")
        if feature.get("code_hash") != source.get("code_hash"):
            raise ValidationError(f"decision feature {name!r}: code hash mismatch")
        if feature.get("generated_at") != source.get("generated_at"):
            raise ValidationError(f"decision feature {name!r}: generated_at mismatch")
        if feature.get("generated_at", decision_time + 1) > decision_time:
            raise ValidationError(f"decision feature {name!r}: future information")
    if decision.get("feature_names") != [item.get("name") for item in decision.get("features", [])]:
        raise ValidationError("decision.feature_names does not match decision.features")

    ledger = verify_ledger(bundle["ledger"])
    verify_anchor(
        bundle["anchor"],
        ledger,
        cutoff_time=decision_time,
        allow_local=allow_local_anchor,
    )
    selected_index = bundle["selected_trial_index"]
    if isinstance(selected_index, bool) or not isinstance(selected_index, int):
        raise ValidationError("bundle.selected_trial_index: expected an integer")
    if selected_index < 0 or selected_index >= len(ledger["entries"]):
        raise ValidationError("bundle.selected_trial_index: out of range")
    selected = ledger["entries"][selected_index]
    if selected["hypothesis_id"] != decision.get("strategy_id"):
        raise ValidationError("selected trial strategy mismatch")
    if selected["parameters"] != parameter_ref or selected["code"] != code_ref:
        raise ValidationError("selected trial artifact mismatch")
    if selected["registered_at"] > decision_time:
        raise ValidationError("selected trial was registered after the cutoff")
    claim = bundle["claim"]
    if not isinstance(claim, dict):
        raise ValidationError("bundle.claim: expected an object")
    if claim.get("result_hash") != result_ref["digest"]:
        raise ValidationError("claim result hash does not match the result artifact")
    metric = claim.get("metric_value")
    if isinstance(metric, bool) or not isinstance(metric, int):
        raise ValidationError("claim metric value must be an integer")
    return bundle

