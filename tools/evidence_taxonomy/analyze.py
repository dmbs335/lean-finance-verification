from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import CANONICAL_FORMAT, canonical_dumps, document_digest, load_json
from .errors import ValidationError

SPEC_SCHEMA = "lfv-evidence-taxonomy-spec-v1"
REPORT_SCHEMA = "lfv-evidence-taxonomy-report-v1"
SPEC_DIGEST_SCHEMA = "lfv-evidence-taxonomy-spec-digest-v1"
MODEL_DIGEST_SCHEMA = "lfv-evidence-taxonomy-model-digest-v1"
REPORT_DIGEST_SCHEMA = "lfv-evidence-taxonomy-report-digest-v1"


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected an object")
    return value


def _array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{path}: expected an array")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: expected a non-empty string")
    return value


def _strings(value: Any, path: str) -> tuple[str, ...]:
    result = tuple(
        _string(item, f"{path}[{index}]")
        for index, item in enumerate(_array(value, path))
    )
    if len(set(result)) != len(result):
        raise ValidationError(f"{path}: duplicate identifiers are not allowed")
    return result


def _reject_unknown(obj: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        raise ValidationError(f"{path}: unknown fields: {sorted(unknown)}")


@dataclass(frozen=True)
class TaxonomyInput:
    spec_path: Path
    raw_spec: dict[str, Any]
    name: str
    model_path: Path
    model: dict[str, Any]
    reference_history: str
    known_attacks: tuple[str, ...]
    candidate_attacks: tuple[str, ...]
    basis_channels: tuple[str, ...]


def load_taxonomy_input(spec_path: Path) -> TaxonomyInput:
    resolved_spec = spec_path.resolve()
    raw = _object(load_json(resolved_spec), "$")
    allowed = {
        "schema_version",
        "name",
        "evidence_model",
        "reference_history",
        "known_attacks",
        "candidate_attacks",
        "basis_channels",
    }
    _reject_unknown(raw, allowed, "$")
    if raw.get("schema_version") != SPEC_SCHEMA:
        raise ValidationError(
            f"$.schema_version: expected {SPEC_SCHEMA!r}, "
            f"got {raw.get('schema_version')!r}"
        )
    model_path = (
        resolved_spec.parent / _string(raw.get("evidence_model"), "$.evidence_model")
    ).resolve()
    model = _object(load_json(model_path), "$model")
    if model.get("schema_version") != "lfv-evidence-synthesis-model-v1":
        raise ValidationError("$model.schema_version: unsupported evidence model")
    histories = _array(model.get("histories"), "$model.histories")
    channels = _array(model.get("channels"), "$model.channels")
    history_ids = [_string(item.get("id"), "$model.histories[].id") for item in histories]
    channel_ids = [_string(item.get("id"), "$model.channels[].id") for item in channels]
    if len(set(history_ids)) != len(history_ids):
        raise ValidationError("$model.histories: ids must be unique")
    if len(set(channel_ids)) != len(channel_ids):
        raise ValidationError("$model.channels: ids must be unique")
    reference = _string(raw.get("reference_history"), "$.reference_history")
    known = _strings(raw.get("known_attacks"), "$.known_attacks")
    candidates = _strings(raw.get("candidate_attacks"), "$.candidate_attacks")
    basis = _strings(raw.get("basis_channels"), "$.basis_channels")
    for history_id in (reference, *known, *candidates):
        if history_id not in history_ids:
            raise ValidationError(f"unknown history id {history_id!r}")
    for channel_id in basis:
        if channel_id not in channel_ids:
            raise ValidationError(f"unknown channel id {channel_id!r}")
    history_by_id = {item["id"]: item for item in histories}
    reference_claim = history_by_id[reference].get("claim")
    if not isinstance(reference_claim, bool):
        raise ValidationError("reference history claim must be Boolean")
    for attack in (*known, *candidates):
        if history_by_id[attack].get("claim") == reference_claim:
            raise ValidationError(
                f"history {attack!r} does not disagree with the reference claim"
            )
    return TaxonomyInput(
        spec_path=resolved_spec,
        raw_spec=raw,
        name=_string(raw.get("name"), "$.name"),
        model_path=model_path,
        model=model,
        reference_history=reference,
        known_attacks=known,
        candidate_attacks=candidates,
        basis_channels=basis,
    )


def _signatures(data: TaxonomyInput) -> tuple[list[str], dict[str, tuple[str, ...]]]:
    histories = data.model["histories"]
    channels = data.model["channels"]
    history_by_id = {item["id"]: item for item in histories}
    reference_claim = history_by_id[data.reference_history]["claim"]
    attack_ids = [
        item["id"] for item in histories if item["claim"] != reference_claim
    ]
    signatures: dict[str, tuple[str, ...]] = {}
    for attack in attack_ids:
        separators: list[str] = []
        for channel in channels:
            observations = _object(
                channel.get("observations"),
                f"$model.channels[{channel['id']}].observations",
            )
            try:
                reference_observation = observations[data.reference_history]
                attack_observation = observations[attack]
            except KeyError as exc:
                raise ValidationError(
                    f"channel {channel['id']!r} lacks a required history observation"
                ) from exc
            if canonical_dumps(reference_observation) != canonical_dumps(
                attack_observation
            ):
                separators.append(channel["id"])
        signatures[attack] = tuple(separators)
    return attack_ids, signatures


def analyze(spec_path: Path) -> dict[str, Any]:
    data = load_taxonomy_input(spec_path)
    attack_ids, signatures = _signatures(data)
    grouped: dict[tuple[str, ...], list[str]] = {}
    for attack in attack_ids:
        grouped.setdefault(signatures[attack], []).append(attack)
    ordered_groups = sorted(grouped.items(), key=lambda item: (len(item[0]), item[0]))
    classes: list[dict[str, Any]] = []
    class_by_attack: dict[str, str] = {}
    signature_by_class: dict[str, tuple[str, ...]] = {}
    for index, (signature, members) in enumerate(ordered_groups):
        class_id = f"class-{index}"
        ordered_members = [attack for attack in attack_ids if attack in set(members)]
        classes.append(
            {
                "class_id": class_id,
                "separators": list(signature),
                "members": ordered_members,
                "unique_separator": len(signature) == 1,
            }
        )
        signature_by_class[class_id] = signature
        for attack in members:
            class_by_attack[attack] = class_id
    subsumption: list[dict[str, str]] = []
    for harder in classes:
        harder_set = set(harder["separators"])
        for easier in classes:
            if harder["class_id"] == easier["class_id"]:
                continue
            easier_set = set(easier["separators"])
            if harder_set < easier_set:
                subsumption.append(
                    {
                        "stricter_class": harder["class_id"],
                        "broader_class": easier["class_id"],
                    }
                )
    known_signature_union = {
        channel for attack in data.known_attacks for channel in signatures[attack]
    }
    basis = set(data.basis_channels)
    candidates: list[dict[str, Any]] = []
    for attack in data.candidate_attacks:
        signature = signatures[attack]
        signature_set = set(signature)
        equivalent_known = [
            previous
            for previous in data.known_attacks
            if signatures[previous] == signature
        ]
        unseen = [
            channel for channel in signature if channel not in known_signature_union
        ]
        basis_covered = bool(signature_set & basis)
        if equivalent_known:
            classification = "existing_class"
        elif unseen and not basis_covered:
            classification = "new_observation_boundary"
        else:
            classification = "new_signature_combination"
        candidates.append(
            {
                "attack": attack,
                "class_id": class_by_attack[attack],
                "separators": list(signature),
                "equivalent_known_attacks": equivalent_known,
                "exact_signature_novel": not equivalent_known,
                "basis_covered": basis_covered,
                "unique_separator": len(signature) == 1,
                "unseen_separators": unseen,
                "classification": classification,
            }
        )
    core: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "name": data.name,
        "reference_history": data.reference_history,
        "known_attacks": list(data.known_attacks),
        "candidate_attacks": list(data.candidate_attacks),
        "basis_channels": list(data.basis_channels),
        "spec_digest": document_digest(
            "taxonomySpec", SPEC_DIGEST_SCHEMA, data.raw_spec
        ),
        "model_digest": document_digest(
            "taxonomyEvidenceModel", MODEL_DIGEST_SCHEMA, data.model
        ),
        "attack_count": len(attack_ids),
        "class_count": len(classes),
        "attacks": [
            {
                "attack": attack,
                "class_id": class_by_attack[attack],
                "separators": list(signatures[attack]),
            }
            for attack in attack_ids
        ],
        "equivalence_classes": classes,
        "strict_signature_subsumption": subsumption,
        "candidate_novelty": candidates,
    }
    report = dict(core)
    report["report_digest"] = document_digest(
        "evidenceTaxonomyReport", REPORT_DIGEST_SCHEMA, core
    )
    return report


def verify_report(spec_path: Path, report: Any) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise ValidationError("taxonomy report must be an object")
    expected = analyze(spec_path)
    if report != expected:
        raise ValidationError(
            "taxonomy report does not match exact regeneration"
        )
    return report
