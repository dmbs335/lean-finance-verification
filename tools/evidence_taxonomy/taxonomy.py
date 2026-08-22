from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from tools.workflow_cegis.canonical import (
    CANONICAL_FORMAT,
    canonical_dumps,
    document_digest,
    load_json,
)

from .errors import ValidationError

TAXONOMY_SCHEMA = "lfv-evidence-obligation-taxonomy-v1"
SOURCE_DIGEST_SCHEMA = "lfv-evidence-taxonomy-source-v1"
TAXONOMY_DIGEST_SCHEMA = "lfv-evidence-obligation-taxonomy-digest-v1"


@dataclass(frozen=True)
class AttackSignature:
    attack: str
    history_index: int
    by_honest: tuple[tuple[str, tuple[str, ...]], ...]

    @property
    def key(self) -> str:
        return canonical_dumps(
            [
                {"honest": honest, "separators": list(separators)}
                for honest, separators in self.by_honest
            ]
        )

    @property
    def separator_channels(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    channel
                    for _honest, separators in self.by_honest
                    for channel in separators
                }
            )
        )

    def as_signature(self) -> list[dict[str, Any]]:
        return [
            {"honest": honest, "separators": list(separators)}
            for honest, separators in self.by_honest
        ]


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


def _bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path}: expected a boolean")
    return value


def _history_catalog(report: dict[str, Any]) -> list[dict[str, Any]]:
    exploration = _object(report.get("exploration"), "$.exploration")
    histories = _array(exploration.get("histories"), "$.exploration.histories")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(histories):
        path = f"$.exploration.histories[{index}]"
        item = _object(raw, path)
        history_id = _string(item.get("id"), f"{path}.id")
        claim = _bool(item.get("claim"), f"{path}.claim")
        if history_id in seen:
            raise ValidationError(f"{path}.id: duplicate history {history_id!r}")
        seen.add(history_id)
        result.append({"id": history_id, "claim": claim, "index": index})
    if not result:
        raise ValidationError("$.exploration.histories: empty history catalog")
    return result


def _channel_catalog(report: dict[str, Any]) -> tuple[str, ...]:
    raw_channels = _array(report.get("channels"), "$.channels")
    result: list[str] = []
    for index, raw in enumerate(raw_channels):
        item = _object(raw, f"$.channels[{index}]")
        result.append(_string(item.get("id"), f"$.channels[{index}].id"))
    if len(set(result)) != len(result):
        raise ValidationError("$.channels: channel ids must be unique")
    if not result:
        raise ValidationError("$.channels: expected at least one channel")
    return tuple(result)


def _edge_catalog(report: dict[str, Any]) -> dict[frozenset[str], tuple[str, ...]]:
    exact = _object(report.get("exact_synthesis"), "$.exact_synthesis")
    edges = _array(
        exact.get("disagreement_edges"),
        "$.exact_synthesis.disagreement_edges",
    )
    result: dict[frozenset[str], tuple[str, ...]] = {}
    for index, raw in enumerate(edges):
        path = f"$.exact_synthesis.disagreement_edges[{index}]"
        edge = _object(raw, path)
        left = _string(edge.get("left"), f"{path}.left")
        right = _string(edge.get("right"), f"{path}.right")
        separators = tuple(
            sorted(
                _string(value, f"{path}.separators[]")
                for value in _array(edge.get("separators"), f"{path}.separators")
            )
        )
        key = frozenset((left, right))
        if len(key) != 2:
            raise ValidationError(f"{path}: disagreement edge needs two histories")
        if key in result:
            raise ValidationError(f"{path}: duplicate disagreement pair")
        result[key] = separators
    return result


def extract_signatures(report: dict[str, Any]) -> tuple[
    tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[AttackSignature, ...]
]:
    histories = _history_catalog(report)
    channels = _channel_catalog(report)
    edge_by_pair = _edge_catalog(report)
    honest = tuple(item["id"] for item in histories if item["claim"])
    attacks = tuple(item["id"] for item in histories if not item["claim"])
    if not honest:
        raise ValidationError("workflow report contains no claim-satisfying history")
    if not attacks:
        raise ValidationError("workflow report contains no claim-violating history")
    index_by_id = {item["id"]: item["index"] for item in histories}
    signatures: list[AttackSignature] = []
    channel_set = set(channels)
    for attack in attacks:
        by_honest: list[tuple[str, tuple[str, ...]]] = []
        for honest_history in honest:
            key = frozenset((honest_history, attack))
            if key not in edge_by_pair:
                raise ValidationError(
                    "missing claim-disagreement edge for "
                    f"{honest_history!r} and {attack!r}"
                )
            separators = edge_by_pair[key]
            unknown = set(separators) - channel_set
            if unknown:
                raise ValidationError(
                    f"edge {honest_history!r}/{attack!r} references unknown "
                    f"channels {sorted(unknown)}"
                )
            by_honest.append((honest_history, separators))
        signatures.append(
            AttackSignature(
                attack=attack,
                history_index=index_by_id[attack],
                by_honest=tuple(by_honest),
            )
        )
    return honest, attacks, channels, tuple(signatures)


def _hits_all(candidate: set[str], edges: Iterable[set[str]]) -> bool:
    return all(not candidate.isdisjoint(edge) for edge in edges)


def minimum_separator_basis(signature: AttackSignature) -> tuple[str, ...]:
    edges = [set(separators) for _honest, separators in signature.by_honest]
    if any(not edge for edge in edges):
        return tuple()
    candidates = sorted(set().union(*edges))
    for size in range(len(candidates) + 1):
        for subset in combinations(candidates, size):
            if _hits_all(set(subset), edges):
                return tuple(subset)
    raise AssertionError("finite nonempty separator edges admit a hitting set")


def _subsumed_by(
    smaller: tuple[tuple[str, tuple[str, ...]], ...],
    larger: tuple[tuple[str, tuple[str, ...]], ...],
) -> bool:
    larger_map = {honest: set(separators) for honest, separators in larger}
    return all(
        set(separators).issubset(larger_map.get(honest, set()))
        for honest, separators in smaller
    )


def build_taxonomy(report: dict[str, Any]) -> dict[str, Any]:
    honest, attacks, channels, signatures = extract_signatures(report)
    grouped: dict[str, list[AttackSignature]] = {}
    for signature in signatures:
        grouped.setdefault(signature.key, []).append(signature)
    ordered_groups = sorted(
        grouped.values(),
        key=lambda group: min(item.history_index for item in group),
    )

    class_records: list[dict[str, Any]] = []
    class_signature: dict[str, AttackSignature] = {}
    attack_to_class: dict[str, str] = {}
    for index, group in enumerate(ordered_groups):
        class_id = f"class-{index}"
        representative = min(group, key=lambda item: item.history_index)
        attacks_in_class = [
            item.attack for item in sorted(group, key=lambda item: item.history_index)
        ]
        class_signature[class_id] = representative
        for attack in attacks_in_class:
            attack_to_class[attack] = class_id
        class_records.append(
            {
                "id": class_id,
                "representative": representative.attack,
                "attacks": attacks_in_class,
                "signature": representative.as_signature(),
                "separator_channels": list(representative.separator_channels),
                "minimum_separator_basis": list(
                    minimum_separator_basis(representative)
                ),
                "first_history_index": representative.history_index,
            }
        )

    all_class_channels = {
        record["id"]: set(record["separator_channels"])
        for record in class_records
    }
    introduced_so_far: set[str] = set()
    for record in class_records:
        current = all_class_channels[record["id"]]
        record["introduced_channels"] = sorted(current - introduced_so_far)
        introduced_so_far.update(current)
        other_union = set().union(
            *(
                channels_for_class
                for class_id, channels_for_class in all_class_channels.items()
                if class_id != record["id"]
            )
        ) if len(class_records) > 1 else set()
        record["class_exclusive_channels"] = sorted(current - other_union)

    subsumption_edges: list[dict[str, str]] = []
    for smaller in class_records:
        for larger in class_records:
            if smaller["id"] == larger["id"]:
                continue
            smaller_signature = class_signature[smaller["id"]].by_honest
            larger_signature = class_signature[larger["id"]].by_honest
            if _subsumed_by(smaller_signature, larger_signature) and not _subsumed_by(
                larger_signature, smaller_signature
            ):
                subsumption_edges.append(
                    {"smaller": smaller["id"], "larger": larger["id"]}
                )
    subsumption_edges.sort(key=lambda edge: (edge["smaller"], edge["larger"]))

    used_channels = set().union(
        *(set(record["separator_channels"]) for record in class_records)
    )
    core: dict[str, Any] = {
        "schema_version": TAXONOMY_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "source_report_digest": document_digest(
            "evidenceTaxonomySource", SOURCE_DIGEST_SCHEMA, report
        ),
        "honest_histories": list(honest),
        "attack_histories": list(attacks),
        "attack_count": len(attacks),
        "epistemic_class_count": len(class_records),
        "compression_ratio": {
            "techniques": len(attacks),
            "epistemic_classes": len(class_records),
        },
        "classes": class_records,
        "attack_to_class": attack_to_class,
        "strict_signature_subsumption": subsumption_edges,
        "channels_used_by_any_separator": sorted(used_channels),
        "channels_unused_by_all_attack_separators": sorted(
            set(channels) - used_channels
        ),
    }
    result = dict(core)
    result["taxonomy_digest"] = document_digest(
        "evidenceObligationTaxonomy", TAXONOMY_DIGEST_SCHEMA, core
    )
    return result


def load_and_build(path: Path) -> dict[str, Any]:
    report = _object(load_json(path), "$")
    return build_taxonomy(report)
