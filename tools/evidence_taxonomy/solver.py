from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.evidence_synth.canonical import (
    CANONICAL_FORMAT,
    document_digest,
)
from tools.evidence_synth.errors import ValidationError
from tools.evidence_synth.model import EvidenceModel

from .config import TaxonomyConfig

REPORT_SCHEMA = "lfv-evidence-taxonomy-report-v1"
REPORT_DIGEST_SCHEMA = "lfv-evidence-taxonomy-report-digest-v1"
MODEL_DIGEST_SCHEMA = "lfv-evidence-taxonomy-model-digest-v1"
CONFIG_DIGEST_SCHEMA = "lfv-evidence-taxonomy-config-digest-v1"


@dataclass(frozen=True)
class AttackAnalysis:
    id: str
    separator_edges: tuple[dict[str, Any], ...]
    covering_masks: tuple[int, ...]
    minimal_masks: tuple[int, ...]
    minimum_cost: int | None
    optimal_masks: tuple[int, ...]
    required_channels: tuple[str, ...]


def _validate_catalog(model: EvidenceModel, config: TaxonomyConfig) -> None:
    histories = {history.id: history for history in model.histories}
    for history_id in config.honest_histories:
        if history_id not in histories:
            raise ValidationError(
                f"unknown honest history in taxonomy: {history_id!r}"
            )
        if not histories[history_id].claim:
            raise ValidationError(
                f"taxonomy honest history has false claim: {history_id!r}"
            )
    for history_id in config.attack_histories:
        if history_id not in histories:
            raise ValidationError(
                f"unknown attack history in taxonomy: {history_id!r}"
            )
        if histories[history_id].claim:
            raise ValidationError(
                f"taxonomy attack history has true claim: {history_id!r}"
            )


def _channel_mask(model: EvidenceModel, channel_ids: list[str]) -> int:
    index = {channel.id: position for position, channel in enumerate(model.channels)}
    mask = 0
    for channel_id in channel_ids:
        mask |= 1 << index[channel_id]
    return mask


def _channels_from_mask(model: EvidenceModel, mask: int) -> list[str]:
    return [
        channel.id
        for index, channel in enumerate(model.channels)
        if mask & (1 << index)
    ]


def _mask_cost(model: EvidenceModel, mask: int) -> int:
    return sum(
        model.weighted_channel_cost(channel.id)
        for index, channel in enumerate(model.channels)
        if mask & (1 << index)
    )


def _proper_subset(left: int, right: int) -> bool:
    return left != right and (left & right) == left


def _separator_edges(
    model: EvidenceModel,
    config: TaxonomyConfig,
    attack_id: str,
) -> tuple[dict[str, Any], ...]:
    edges: list[dict[str, Any]] = []
    for honest_id in config.honest_histories:
        separators = [
            channel.id
            for channel in model.channels
            if model.observation_key(channel.id, honest_id)
            != model.observation_key(channel.id, attack_id)
        ]
        edges.append(
            {
                "honest": honest_id,
                "attack": attack_id,
                "separators": separators,
                "separator_mask": _channel_mask(model, separators),
            }
        )
    return tuple(edges)


def _covers(mask: int, edges: tuple[dict[str, Any], ...]) -> bool:
    return all(mask & edge["separator_mask"] for edge in edges)


def analyze_attack(
    model: EvidenceModel,
    config: TaxonomyConfig,
    attack_id: str,
) -> AttackAnalysis:
    edges = _separator_edges(model, config, attack_id)
    candidate_count = 1 << len(model.channels)
    covering = tuple(
        mask for mask in range(candidate_count) if _covers(mask, edges)
    )
    minimal = tuple(
        mask
        for mask in covering
        if not any(_proper_subset(other, mask) for other in covering)
    )
    if covering:
        minimum_cost = min(_mask_cost(model, mask) for mask in covering)
        optimal = tuple(
            mask
            for mask in covering
            if _mask_cost(model, mask) == minimum_cost
        )
        required_mask = (1 << len(model.channels)) - 1
        for mask in covering:
            required_mask &= mask
        required = tuple(_channels_from_mask(model, required_mask))
    else:
        minimum_cost = None
        optimal = tuple()
        required = tuple()
    return AttackAnalysis(
        id=attack_id,
        separator_edges=edges,
        covering_masks=covering,
        minimal_masks=minimal,
        minimum_cost=minimum_cost,
        optimal_masks=optimal,
        required_channels=required,
    )


def _attack_as_dict(
    model: EvidenceModel,
    analysis: AttackAnalysis,
    class_id: str,
    first_representative: str,
) -> dict[str, Any]:
    return {
        "id": analysis.id,
        "class_id": class_id,
        "class_representative": first_representative,
        "separator_edges": list(analysis.separator_edges),
        "covering_selection_count": len(analysis.covering_masks),
        "minimum_cost": analysis.minimum_cost,
        "optimal_selections": [
            {
                "mask": mask,
                "channels": _channels_from_mask(model, mask),
                "cost": _mask_cost(model, mask),
            }
            for mask in analysis.optimal_masks
        ],
        "minimal_covering_selections": [
            {
                "mask": mask,
                "channels": _channels_from_mask(model, mask),
                "cost": _mask_cost(model, mask),
            }
            for mask in analysis.minimal_masks
        ],
        "required_channels": list(analysis.required_channels),
    }


def _classify(
    analyses: list[AttackAnalysis],
) -> tuple[dict[str, tuple[str, str]], list[dict[str, Any]]]:
    signature_to_class: dict[tuple[int, ...], tuple[str, str]] = {}
    assignment: dict[str, tuple[str, str]] = {}
    members: dict[str, list[str]] = {}
    signatures: dict[str, tuple[int, ...]] = {}
    for analysis in analyses:
        signature = analysis.covering_masks
        if signature not in signature_to_class:
            class_id = f"class-{len(signature_to_class)}"
            signature_to_class[signature] = (class_id, analysis.id)
            members[class_id] = []
            signatures[class_id] = signature
        class_id, representative = signature_to_class[signature]
        assignment[analysis.id] = (class_id, representative)
        members[class_id].append(analysis.id)
    classes = [
        {
            "id": class_id,
            "representative": representative,
            "members": members[class_id],
            "covering_selection_count": len(signatures[class_id]),
        }
        for signature, (class_id, representative) in signature_to_class.items()
    ]
    return assignment, classes


def _subsumptions(
    analyses: list[AttackAnalysis],
    assignment: dict[str, tuple[str, str]],
) -> list[dict[str, Any]]:
    by_id = {analysis.id: analysis for analysis in analyses}
    result: list[dict[str, Any]] = []
    for stronger in analyses:
        if not stronger.covering_masks:
            continue
        stronger_set = set(stronger.covering_masks)
        for weaker in analyses:
            if stronger.id == weaker.id or not weaker.covering_masks:
                continue
            if assignment[stronger.id][0] == assignment[weaker.id][0]:
                continue
            if stronger_set.issubset(weaker.covering_masks):
                result.append(
                    {
                        "stronger": stronger.id,
                        "weaker": weaker.id,
                    }
                )
    return result


def _prefix_debt(
    model: EvidenceModel,
    analyses: list[AttackAnalysis],
) -> list[dict[str, Any]]:
    candidate_count = 1 << len(model.channels)
    accumulated_edges: list[dict[str, Any]] = []
    previous_cost = 0
    result: list[dict[str, Any]] = []
    for analysis in analyses:
        accumulated_edges.extend(analysis.separator_edges)
        feasible = [
            mask
            for mask in range(candidate_count)
            if _covers(mask, tuple(accumulated_edges))
        ]
        if not feasible:
            result.append(
                {
                    "attack": analysis.id,
                    "status": "impossible",
                    "previous_cost": previous_cost,
                    "new_cost": None,
                    "marginal_debt": None,
                }
            )
            continue
        new_cost = min(_mask_cost(model, mask) for mask in feasible)
        optimal_mask = min(
            (
                mask
                for mask in feasible
                if _mask_cost(model, mask) == new_cost
            ),
            key=lambda mask: (
                len(_channels_from_mask(model, mask)),
                _channels_from_mask(model, mask),
                mask,
            ),
        )
        result.append(
            {
                "attack": analysis.id,
                "status": "synthesized",
                "previous_cost": previous_cost,
                "new_cost": new_cost,
                "marginal_debt": new_cost - previous_cost,
                "selected": {
                    "mask": optimal_mask,
                    "channels": _channels_from_mask(model, optimal_mask),
                },
            }
        )
        previous_cost = new_cost
    return result


def normalized_config(config: TaxonomyConfig) -> dict[str, Any]:
    return {
        "schema_version": "lfv-evidence-taxonomy-config-v1",
        "name": config.name,
        "honest_histories": list(config.honest_histories),
        "attack_histories": list(config.attack_histories),
    }


def solve_taxonomy(
    model: EvidenceModel,
    config: TaxonomyConfig,
) -> dict[str, Any]:
    _validate_catalog(model, config)
    analyses = [
        analyze_attack(model, config, attack_id)
        for attack_id in config.attack_histories
    ]
    assignment, classes = _classify(analyses)
    core: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "name": config.name,
        "model_digest": document_digest(
            "evidenceTaxonomyModel",
            MODEL_DIGEST_SCHEMA,
            {
                "name": model.name,
                "histories": [
                    {"id": history.id, "claim": history.claim}
                    for history in model.histories
                ],
                "channels": [
                    {
                        "id": channel.id,
                        "cost": channel.cost.as_dict(),
                        "observations": channel.observations,
                    }
                    for channel in model.channels
                ],
                "cost_weights": model.weights.as_dict(),
            },
        ),
        "config_digest": document_digest(
            "evidenceTaxonomyConfig",
            CONFIG_DIGEST_SCHEMA,
            normalized_config(config),
        ),
        "honest_histories": list(config.honest_histories),
        "attack_order": list(config.attack_histories),
        "channels": [
            {
                "id": channel.id,
                "weighted_cost": model.weighted_channel_cost(channel.id),
            }
            for channel in model.channels
        ],
        "attacks": [
            _attack_as_dict(
                model,
                analysis,
                assignment[analysis.id][0],
                assignment[analysis.id][1],
            )
            for analysis in analyses
        ],
        "classes": classes,
        "subsumptions": _subsumptions(analyses, assignment),
        "evidence_debt_trace": _prefix_debt(model, analyses),
    }
    report = dict(core)
    report["report_digest"] = document_digest(
        "evidenceTaxonomyReport", REPORT_DIGEST_SCHEMA, core
    )
    return report


def verify_report(
    model: EvidenceModel,
    config: TaxonomyConfig,
    report: Any,
) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise ValidationError("taxonomy report: expected an object")
    expected = solve_taxonomy(model, config)
    if report != expected:
        raise ValidationError(
            "evidence taxonomy report does not match exact recomputation"
        )
    return report
