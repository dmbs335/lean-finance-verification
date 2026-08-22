from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.workflow_cegis.canonical import load_json
from tools.workflow_cegis.model import CostVector, ZERO_COST

from .errors import ValidationError

TRACE_SCHEMA = "lfv-observed-attack-trace-v1"
_NAMESPACE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")


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


def _nat(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected a non-negative integer")
    return value


def _reject_unknown(obj: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        raise ValidationError(f"{path}: unknown fields: {sorted(unknown)}")


def _cost(value: Any, path: str) -> CostVector:
    if value is None:
        return ZERO_COST
    obj = _object(value, path)
    expected = {"operational", "privacy", "trust"}
    _reject_unknown(obj, expected, path)
    missing = expected - set(obj)
    if missing:
        raise ValidationError(f"{path}: missing fields: {sorted(missing)}")
    return CostVector(
        operational=_nat(obj["operational"], f"{path}.operational"),
        privacy=_nat(obj["privacy"], f"{path}.privacy"),
        trust=_nat(obj["trust"], f"{path}.trust"),
    )


def _state_patch(value: Any, path: str) -> dict[str, bool]:
    obj = _object(value, path)
    result: dict[str, bool] = {}
    for field, field_value in obj.items():
        if not isinstance(field, str) or not field:
            raise ValidationError(f"{path}: state field names must be non-empty strings")
        result[field] = _bool(field_value, f"{path}.{field}")
    return result


@dataclass(frozen=True)
class VariableExtension:
    id: str
    initial: bool
    claim_violation: bool
    sensor_cost: CostVector
    description: str


@dataclass(frozen=True)
class TraceStep:
    event: str
    observed_before: dict[str, bool]
    observed_after: dict[str, bool]
    guard_fields: tuple[str, ...]
    tags: tuple[str, ...]
    sensor_templates: tuple[str, ...]
    propagate_to_channels: tuple[str, ...]
    sensor_cost: CostVector
    description: str

    @property
    def carries_semantics(self) -> bool:
        return bool(
            self.observed_before
            or self.observed_after
            or self.guard_fields
            or self.tags
            or self.sensor_templates
            or self.propagate_to_channels
        )


@dataclass(frozen=True)
class ObservedAttackTrace:
    source_path: Path
    id: str
    description: str
    refined_name: str
    refined_namespace_prefix: str
    variable_extensions: tuple[VariableExtension, ...]
    steps: tuple[TraceStep, ...]
    expected_terminal: bool
    expected_claim: bool

    @property
    def event_ids(self) -> tuple[str, ...]:
        return tuple(step.event for step in self.steps)

    @property
    def event_counts(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for event in self.event_ids:
            result[event] = result.get(event, 0) + 1
        return result

    @property
    def extension_by_id(self) -> dict[str, VariableExtension]:
        return {extension.id: extension for extension in self.variable_extensions}


def _parse_extensions(raw: Any) -> tuple[VariableExtension, ...]:
    extensions: list[VariableExtension] = []
    for index, item in enumerate(_array(raw, "$.variable_extensions")):
        path = f"$.variable_extensions[{index}]"
        obj = _object(item, path)
        _reject_unknown(
            obj,
            {"id", "initial", "claim_violation", "sensor_cost", "description"},
            path,
        )
        variable_id = _string(obj.get("id"), f"{path}.id")
        extensions.append(
            VariableExtension(
                id=variable_id,
                initial=_bool(obj.get("initial"), f"{path}.initial"),
                claim_violation=_bool(
                    obj.get("claim_violation", False),
                    f"{path}.claim_violation",
                ),
                sensor_cost=_cost(obj.get("sensor_cost"), f"{path}.sensor_cost"),
                description=_string(
                    obj.get("description", variable_id),
                    f"{path}.description",
                ),
            )
        )
    ids = [extension.id for extension in extensions]
    if len(set(ids)) != len(ids):
        raise ValidationError("$.variable_extensions: ids must be unique")
    return tuple(extensions)


def _parse_steps(raw: Any) -> tuple[TraceStep, ...]:
    steps: list[TraceStep] = []
    for index, item in enumerate(_array(raw, "$.steps")):
        path = f"$.steps[{index}]"
        obj = _object(item, path)
        _reject_unknown(
            obj,
            {
                "event",
                "observed_before",
                "observed_after",
                "guard_fields",
                "tags",
                "sensor_templates",
                "propagate_to_channels",
                "sensor_cost",
                "description",
            },
            path,
        )
        event = _string(obj.get("event"), f"{path}.event")
        before = _state_patch(obj.get("observed_before", {}), f"{path}.observed_before")
        after = _state_patch(obj.get("observed_after", {}), f"{path}.observed_after")
        guard_fields = tuple(
            _string(value, f"{path}.guard_fields[]")
            for value in _array(obj.get("guard_fields", []), f"{path}.guard_fields")
        )
        tags = tuple(
            _string(value, f"{path}.tags[]")
            for value in _array(obj.get("tags", []), f"{path}.tags")
        )
        templates = tuple(
            _string(value, f"{path}.sensor_templates[]")
            for value in _array(
                obj.get("sensor_templates", []), f"{path}.sensor_templates"
            )
        )
        channels = tuple(
            _string(value, f"{path}.propagate_to_channels[]")
            for value in _array(
                obj.get("propagate_to_channels", []),
                f"{path}.propagate_to_channels",
            )
        )
        for name, values in (
            ("guard_fields", guard_fields),
            ("tags", tags),
            ("sensor_templates", templates),
            ("propagate_to_channels", channels),
        ):
            if len(set(values)) != len(values):
                raise ValidationError(f"{path}.{name}: duplicates are not allowed")
        unknown_guard_fields = set(guard_fields) - set(before)
        if unknown_guard_fields:
            raise ValidationError(
                f"{path}.guard_fields: fields need observed_before values: "
                f"{sorted(unknown_guard_fields)}"
            )
        steps.append(
            TraceStep(
                event=event,
                observed_before=before,
                observed_after=after,
                guard_fields=guard_fields,
                tags=tags,
                sensor_templates=templates,
                propagate_to_channels=channels,
                sensor_cost=_cost(obj.get("sensor_cost"), f"{path}.sensor_cost"),
                description=_string(
                    obj.get("description", event), f"{path}.description"
                ),
            )
        )
    if not steps:
        raise ValidationError("$.steps: expected at least one observed event")
    return tuple(steps)


def load_trace(path: Path) -> ObservedAttackTrace:
    source_path = path.resolve()
    raw = _object(load_json(source_path), "$")
    allowed = {
        "schema_version",
        "id",
        "description",
        "refined_name",
        "refined_namespace_prefix",
        "variable_extensions",
        "steps",
        "expected_terminal",
        "expected_claim",
    }
    _reject_unknown(raw, allowed, "$")
    if raw.get("schema_version") != TRACE_SCHEMA:
        raise ValidationError(
            f"$.schema_version: expected {TRACE_SCHEMA!r}, "
            f"got {raw.get('schema_version')!r}"
        )
    namespace = _string(
        raw.get("refined_namespace_prefix"),
        "$.refined_namespace_prefix",
    )
    if not _NAMESPACE_RE.fullmatch(namespace):
        raise ValidationError(
            "$.refined_namespace_prefix: invalid Lean namespace"
        )
    return ObservedAttackTrace(
        source_path=source_path,
        id=_string(raw.get("id"), "$.id"),
        description=_string(raw.get("description"), "$.description"),
        refined_name=_string(raw.get("refined_name"), "$.refined_name"),
        refined_namespace_prefix=namespace,
        variable_extensions=_parse_extensions(raw.get("variable_extensions", [])),
        steps=_parse_steps(raw.get("steps")),
        expected_terminal=_bool(
            raw.get("expected_terminal", True), "$.expected_terminal"
        ),
        expected_claim=_bool(
            raw.get("expected_claim", False), "$.expected_claim"
        ),
    )
