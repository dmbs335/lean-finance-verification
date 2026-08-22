from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from tools.evidence_synth.canonical import canonical_bytes

from .errors import ValidationError
from .model import Corpus

REPORT_SCHEMA = "lfv-symbolic-evidence-report-v1"


@dataclass
class SearchStats:
    explored: int = 0
    pruned: int = 0
    memo_pruned: int = 0


def _signature_classes(corpus: Corpus) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[str]] = {}
    for attack in corpus.attacks:
        signature = tuple(sorted(attack.separators))
        groups.setdefault(signature, []).append(attack.id)
    return [
        {"separators": list(signature), "attacks": sorted(attacks)}
        for signature, attacks in sorted(groups.items())
    ]


def _greedy_upper_bound(
    corpus: Corpus,
    coverage: list[int],
    full_mask: int,
) -> tuple[int, tuple[int, ...]]:
    covered = 0
    selected: list[int] = []
    remaining = set(range(len(corpus.channels)))
    while covered != full_mask:
        candidates = []
        for index in remaining:
            new_bits = (coverage[index] & ~covered).bit_count()
            if new_bits:
                channel = corpus.channels[index]
                candidates.append((
                    Fraction(channel.cost, new_bits),
                    channel.cost,
                    -new_bits,
                    channel.id,
                    index,
                ))
        if not candidates:
            raise ValidationError("attack corpus contains an uncovered obligation")
        index = min(candidates)[-1]
        selected.append(index)
        remaining.remove(index)
        covered |= coverage[index]
    return sum(corpus.channels[index].cost for index in selected), tuple(selected)


def solve(corpus: Corpus) -> dict[str, Any]:
    channel_index = {
        channel.id: index for index, channel in enumerate(corpus.channels)
    }
    edge_channels = [
        tuple(channel_index[channel_id] for channel_id in attack.separators)
        for attack in corpus.attacks
    ]
    coverage = [0 for _ in corpus.channels]
    for attack_index, candidates in enumerate(edge_channels):
        for channel_index_value in candidates:
            coverage[channel_index_value] |= 1 << attack_index
    full_mask = (1 << len(corpus.attacks)) - 1
    best_cost, best_indices = _greedy_upper_bound(corpus, coverage, full_mask)
    best_ids = tuple(sorted(corpus.channels[index].id for index in best_indices))
    stats = SearchStats()
    memo: dict[int, int] = {}

    def search(covered: int, selected: tuple[int, ...], cost: int) -> None:
        nonlocal best_cost, best_indices, best_ids
        stats.explored += 1
        if cost > best_cost:
            stats.pruned += 1
            return
        previous = memo.get(covered)
        if previous is not None and previous < cost:
            stats.memo_pruned += 1
            return
        memo[covered] = cost
        if covered == full_mask:
            ids = tuple(sorted(corpus.channels[index].id for index in selected))
            if cost < best_cost or (cost == best_cost and ids < best_ids):
                best_cost = cost
                best_indices = selected
                best_ids = ids
            return

        selected_set = set(selected)
        uncovered_indices = [
            index for index in range(len(corpus.attacks))
            if not (covered & (1 << index))
        ]
        attack_index = min(
            uncovered_indices,
            key=lambda index: (
                len([candidate for candidate in edge_channels[index]
                    if candidate not in selected_set]),
                corpus.attacks[index].id,
            ),
        )
        candidates = [
            index for index in edge_channels[attack_index]
            if index not in selected_set
        ]
        if not candidates:
            stats.pruned += 1
            return
        cheapest = min(corpus.channels[index].cost for index in candidates)
        if cost + cheapest > best_cost:
            stats.pruned += 1
            return
        candidates.sort(key=lambda index: (
            corpus.channels[index].cost,
            -(coverage[index] & ~covered).bit_count(),
            corpus.channels[index].id,
        ))
        for index in candidates:
            new_covered = covered | coverage[index]
            if new_covered == covered:
                continue
            search(
                new_covered,
                selected + (index,),
                cost + corpus.channels[index].cost,
            )

    search(0, tuple(), 0)
    selected_ids = [
        channel.id for channel in corpus.channels
        if channel.id in set(best_ids)
    ]
    selected_set = set(selected_ids)
    witnesses = [
        {
            "attack": attack.id,
            "selected_separators": [
                channel_id for channel_id in attack.separators
                if channel_id in selected_set
            ],
        }
        for attack in corpus.attacks
    ]
    if any(not witness["selected_separators"] for witness in witnesses):
        raise AssertionError("branch-and-bound returned an uncovered attack")
    boundaries = sorted({attack.boundary for attack in corpus.attacks})
    categories = sorted({attack.category for attack in corpus.attacks})
    report = {
        "schema_version": REPORT_SCHEMA,
        "name": corpus.name,
        "attack_count": len(corpus.attacks),
        "channel_count": len(corpus.channels),
        "categories": categories,
        "boundaries": boundaries,
        "signature_classes": _signature_classes(corpus),
        "selected": {"channels": selected_ids, "cost": best_cost},
        "coverage_witnesses": witnesses,
        "search": {
            "explored_nodes": stats.explored,
            "pruned_nodes": stats.pruned,
            "memo_pruned_nodes": stats.memo_pruned,
            "exhaustive_candidate_count": 1 << len(corpus.channels),
        },
    }
    report["report_sha256"] = __import__("hashlib").sha256(
        canonical_bytes(report)
    ).hexdigest()
    return report


def verify(corpus: Corpus, report: Any) -> dict[str, Any]:
    expected = solve(corpus)
    if report != expected:
        raise ValidationError(
            "symbolic evidence report does not match exact recomputation"
        )
    return expected
