from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from typing import Any

from .errors import ValidationError
from .model import EngineSpec, Operation, Point


def point_to_json(point: Point) -> dict[str, Any]:
    return {
        "id": point.id,
        "observation_time": point.observation_time,
        "available_time": point.available_time,
        "value": point.value,
        "representation": point.representation,
    }


def operation_to_json(operation: Operation) -> dict[str, Any]:
    return {"kind": operation.kind, **operation.data}


def causal_prefix(
    points: tuple[Point, ...] | list[Point],
    decision_time: int,
) -> tuple[tuple[str, int, int, int], ...]:
    return tuple(sorted(
        (
            point.id,
            point.observation_time,
            point.available_time,
            point.value,
        )
        for point in points
        if point.observation_time <= decision_time
        and point.available_time <= decision_time
    ))


def apply_operations(
    points: tuple[Point, ...] | list[Point],
    operations: tuple[Operation, ...] | list[Operation],
) -> tuple[Point, ...]:
    working = list(points)
    for operation in operations:
        data = operation.data
        if operation.kind == "append_point":
            point = Point(**data["point"])
            if point.id in {item.id for item in working}:
                raise ValidationError(
                    f"append_point duplicates point id {point.id}"
                )
            working.append(point)
        elif operation.kind == "revise_value":
            point_id = data["point_id"]
            if point_id not in {item.id for item in working}:
                raise ValidationError(
                    f"revise_value references missing point {point_id}"
                )
            working = [
                replace(point, value=data["value"])
                if point.id == point_id else point
                for point in working
            ]
        elif operation.kind == "reorder":
            by_id = {point.id: point for point in working}
            order = data["order"]
            if set(order) != set(by_id) or len(order) != len(by_id):
                raise ValidationError(
                    "reorder must contain every current point exactly once"
                )
            working = [by_id[point_id] for point_id in order]
        elif operation.kind == "change_representation":
            point_id = data["point_id"]
            if point_id not in {item.id for item in working}:
                raise ValidationError(
                    "change_representation references missing point "
                    f"{point_id}"
                )
            working = [
                replace(point, representation=data["representation"])
                if point.id == point_id else point
                for point in working
            ]
        elif operation.kind == "change_availability":
            point_id = data["point_id"]
            if point_id not in {item.id for item in working}:
                raise ValidationError(
                    "change_availability references missing point "
                    f"{point_id}"
                )
            working = [
                replace(point, available_time=data["available_time"])
                if point.id == point_id else point
                for point in working
            ]
        else:
            raise ValidationError(
                f"unsupported mutation operation {operation.kind}"
            )
    return tuple(working)


def _fraction_to_json(value: Fraction | None) -> dict[str, int] | None:
    if value is None:
        return None
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
    }


def _select_output(
    engine: EngineSpec,
    points: list[Point],
    decision_time: int,
) -> dict[str, Any]:
    selected: list[Point] = []
    mark: Fraction | None = None

    if engine.semantics == "causal_forward_fill":
        candidates = [
            point
            for point in points
            if point.observation_time <= decision_time
            and point.available_time <= decision_time
        ]
        if candidates:
            selected = [max(
                candidates,
                key=lambda point: (
                    point.observation_time,
                    point.available_time,
                    point.id,
                ),
            )]
            mark = Fraction(selected[0].value)

    elif engine.semantics == "observation_only_forward_fill":
        candidates = [
            point
            for point in points
            if point.observation_time <= decision_time
        ]
        if candidates:
            selected = [max(
                candidates,
                key=lambda point: (point.observation_time, point.id),
            )]
            mark = Fraction(selected[0].value)

    elif engine.semantics in {
        "global_last_fill", "mutating_global_last_fill"
    }:
        if engine.semantics == "mutating_global_last_fill":
            points.sort(
                key=lambda point: (
                    point.observation_time,
                    point.available_time,
                    point.id,
                )
            )
        exact = [
            point
            for point in points
            if point.observation_time == decision_time
        ]
        if exact:
            selected = [exact[-1]]
        elif points:
            selected = [points[-1]]
        if selected:
            mark = Fraction(selected[0].value)

    elif engine.semantics == "bidirectional_interpolation":
        exact = [
            point
            for point in points
            if point.observation_time == decision_time
        ]
        if exact:
            selected = [max(
                exact,
                key=lambda point: (point.available_time, point.id),
            )]
            mark = Fraction(selected[0].value)
        else:
            left_candidates = [
                point
                for point in points
                if point.observation_time < decision_time
            ]
            right_candidates = [
                point
                for point in points
                if point.observation_time > decision_time
            ]
            left = (
                max(
                    left_candidates,
                    key=lambda point: (point.observation_time, point.id),
                )
                if left_candidates else None
            )
            right = (
                min(
                    right_candidates,
                    key=lambda point: (point.observation_time, point.id),
                )
                if right_candidates else None
            )
            if left is not None and right is not None:
                selected = [left, right]
                mark = (
                    Fraction(left.value)
                    + Fraction(
                        right.value - left.value,
                        right.observation_time - left.observation_time,
                    )
                    * (decision_time - left.observation_time)
                )
            elif left is not None:
                selected = [left]
                mark = Fraction(left.value)
            elif right is not None:
                selected = [right]
                mark = Fraction(right.value)

    else:
        raise ValidationError(
            f"unsupported engine semantics {engine.semantics}"
        )

    if mark is None:
        return {
            "decision_time": decision_time,
            "status": "missing",
            "selected_point_ids": [],
            "mark": None,
            "position": None,
        }
    return {
        "decision_time": decision_time,
        "status": "ok",
        "selected_point_ids": [point.id for point in selected],
        "mark": _fraction_to_json(mark),
        "position": 1 if mark >= engine.threshold else -1,
    }


def evaluate_engine(
    engine: EngineSpec,
    points: tuple[Point, ...] | list[Point],
    decision_times: tuple[int, ...] | list[int],
) -> tuple[list[dict[str, Any]], bool, tuple[Point, ...]]:
    working = list(points)
    before = tuple(working)
    outputs = [
        _select_output(engine, working, decision_time)
        for decision_time in decision_times
    ]
    after = tuple(working)
    return outputs, after != before, after


def availability_violations(
    outputs: list[dict[str, Any]],
    points: tuple[Point, ...] | list[Point],
) -> list[dict[str, Any]]:
    by_id = {point.id: point for point in points}
    violations: list[dict[str, Any]] = []
    for output in outputs:
        decision_time = output["decision_time"]
        for point_id in output["selected_point_ids"]:
            point = by_id[point_id]
            reasons: list[str] = []
            if point.observation_time > decision_time:
                reasons.append("observation_after_decision")
            if point.available_time > decision_time:
                reasons.append("available_after_decision")
            if reasons:
                violations.append({
                    "decision_time": decision_time,
                    "point_id": point_id,
                    "observation_time": point.observation_time,
                    "available_time": point.available_time,
                    "reasons": reasons,
                })
    return violations
