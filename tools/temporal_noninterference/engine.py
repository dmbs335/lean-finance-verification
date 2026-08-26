from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .model import Observation, Pipeline


@dataclass
class Entry:
    id: str
    time: int
    available_at: int
    value: Fraction | None


@dataclass(frozen=True)
class Evaluation:
    value: Fraction | None
    mutations: tuple[dict[str, Any], ...]


def _entries(history: tuple[Observation, ...]) -> list[Entry]:
    return [
        Entry(
            id=item.id,
            time=item.time,
            available_at=item.available_at,
            value=Fraction(item.value),
        )
        for item in history
    ]


def _serialize_value(value: Fraction | None) -> list[int] | None:
    if value is None:
        return None
    return [value.numerator, value.denominator]


def _position(value: Fraction | None, threshold: int) -> int:
    if value is None:
        return 0
    return 1 if value >= threshold else -1


def _exact_visible(entries: list[Entry], query: int) -> Fraction | None:
    return next(
        (
            item.value
            for item in entries
            if item.time == query and item.available_at <= query
        ),
        None,
    )


def _causal_candidates(entries: list[Entry], query: int) -> list[Entry]:
    return sorted(
        (
            item
            for item in entries
            if item.value is not None
            and item.time <= query
            and item.available_at <= query
        ),
        key=lambda item: item.time,
    )


def evaluate(
    entries: list[Entry], pipeline: Pipeline, query: int
) -> Evaluation:
    operation = pipeline.operation
    exact = _exact_visible(entries, query)
    if operation == "direct_exact":
        return Evaluation(value=exact, mutations=())

    if operation == "causal_forward_fill":
        candidates = _causal_candidates(entries, query)
        return Evaluation(
            value=candidates[-1].value if candidates else None,
            mutations=(),
        )

    if operation == "causal_trailing_mean":
        candidates = _causal_candidates(entries, query)[-pipeline.window :]
        if not candidates:
            return Evaluation(value=None, mutations=())
        total = sum((item.value for item in candidates), Fraction(0))
        return Evaluation(value=total / len(candidates), mutations=())

    if exact is not None:
        return Evaluation(value=exact, mutations=())

    marker = Entry(
        id=f"__query_{query}_{len(entries)}",
        time=query,
        available_at=query,
        value=None,
    )
    entries.append(marker)
    mutation = ({"kind": "insert_missing_query", "time": query},)

    if operation == "append_tail_forward_fill":
        prior = next(
            (item.value for item in reversed(entries) if item.value is not None),
            None,
        )
        return Evaluation(value=prior, mutations=mutation)

    if operation == "two_sided_interpolation":
        ordered = sorted(entries, key=lambda item: item.time)
        left = [
            item for item in ordered
            if item.value is not None and item.time < query
        ]
        right = [
            item for item in ordered
            if item.value is not None and query < item.time
        ]
        if not left or not right:
            return Evaluation(value=None, mutations=mutation)
        lower = left[-1]
        upper = right[0]
        distance = upper.time - lower.time
        weight = Fraction(query - lower.time, distance)
        value = lower.value + (upper.value - lower.value) * weight
        return Evaluation(value=value, mutations=mutation)

    raise AssertionError(f"unsupported operation {operation}")


def run_trace(
    history: tuple[Observation, ...],
    pipeline: Pipeline,
    query_times: tuple[int, ...],
) -> dict[str, Any]:
    entries = _entries(history)
    outputs: list[dict[str, Any]] = []
    mutations: list[dict[str, Any]] = []
    for query in query_times:
        result = evaluate(entries, pipeline, query)
        outputs.append(
            {
                "time": query,
                "value": _serialize_value(result.value),
                "position": _position(result.value, pipeline.threshold),
            }
        )
        mutations.extend(result.mutations)
    return {
        "outputs": outputs,
        "mutations": mutations,
        "source_mutated": bool(mutations),
    }


def evaluate_once(
    history: tuple[Observation, ...],
    pipeline: Pipeline,
    query: int,
) -> dict[str, Any]:
    result = evaluate(_entries(history), pipeline, query)
    return {
        "time": query,
        "value": _serialize_value(result.value),
        "position": _position(result.value, pipeline.threshold),
        "mutations": list(result.mutations),
    }
