from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import load_json
from .errors import ValidationError
from .expr import validate_expr

MODEL_SCHEMA = "lfv-workflow-cegis-model-v1"
MAX_ACTIONS = 16
MAX_CHANNELS = 12
MAX_DEPTH = 12
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


def _nat(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{path}: expected a non-negative integer")
    return value


def _positive(value: Any, path: str) -> int:
    result = _nat(value, path)
    if result == 0:
        raise ValidationError(f"{path}: expected a positive integer")
    return result


def _bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path}: expected a boolean")
    return value


def _reject_unknown(obj: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        raise ValidationError(f"{path}: unknown fields: {sorted(unknown)}")


@dataclass(frozen=True)
class CostVector:
    operational: int
    privacy: int
    trust: int

    def weighted(self, weights: CostVector) -> int:
        return (
            self.operational * weights.operational
            + self.privacy * weights.privacy
            + self.trust * weights.trust
        )

    def as_dict(self) -> dict[str, int]:
        return {
            "operational": self.operational,
            "privacy": self.privacy,
            "trust": self.trust,
        }

    def __add__(self, other: CostVector) -> CostVector:
        return CostVector(
            self.operational + other.operational,
            self.privacy + other.privacy,
            self.trust + other.trust,
        )


ZERO_COST = CostVector(0, 0, 0)


@dataclass(frozen=True)
class Variable:
    id: str
    initial: bool
    sensor_cost: CostVector
    description: str


@dataclass(frozen=True)
class Effect:
    variable: str
    value: Any


@dataclass(frozen=True)
class Action:
    id: str
    guard: Any
    effects: tuple[Effect, ...]
    max_occurrences: int
    tags: tuple[str, ...]
    sensor_cost: CostVector
    description: str


@dataclass(frozen=True)
class Channel:
    id: str
    deployed: bool
    visible_actions: tuple[str, ...]
    visible_state: tuple[str, ...]
    cost: CostVector
    description: str
    generated_from: str | None = None


@dataclass(frozen=True)
class SensorTemplate:
    id: str
    kind: str
    action_tags: tuple[str, ...]
    variables: tuple[str, ...]
    cost: CostVector
    description: str


@dataclass(frozen=True)
class TraceAlias:
    id: str
    trace: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class WorkflowModel:
    source_path: Path
    name: str
    namespace_prefix: str
    max_depth: int
    max_histories: int
    max_refinements: int
    cost_weights: CostVector
    variables: tuple[Variable, ...]
    actions: tuple[Action, ...]
    terminal: Any
    claim: Any
    channels: tuple[Channel, ...]
    sensor_templates: tuple[SensorTemplate, ...]
    trace_aliases: tuple[TraceAlias, ...]

    @property
    def variable_by_id(self) -> dict[str, Variable]:
        return {variable.id: variable for variable in self.variables}

    @property
    def action_by_id(self) -> dict[str, Action]:
        return {action.id: action for action in self.actions}

    @property
    def channel_by_id(self) -> dict[str, Channel]:
        return {channel.id: channel for channel in self.channels}

    @property
    def initial_state(self) -> dict[str, bool]:
        return {variable.id: variable.initial for variable in self.variables}

    @property
    def workflow_namespace(self) -> str:
        return f"{self.namespace_prefix}.Search"

    @property
    def evidence_namespace(self) -> str:
        return f"{self.namespace_prefix}.Evidence"

    @property
    def bridge_namespace(self) -> str:
        return f"{self.namespace_prefix}.CEGIS"


def _parse_cost(value: Any, path: str) -> CostVector:
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


def _parse_variables(raw: Any) -> tuple[Variable, ...]:
    variables: list[Variable] = []
    for index, item in enumerate(_array(raw, "$.variables")):
        path = f"$.variables[{index}]"
        obj = _object(item, path)
        _reject_unknown(obj, {"id", "initial", "sensor_cost", "description"}, path)
        variable_id = _string(obj.get("id"), f"{path}.id")
        variables.append(
            Variable(
                id=variable_id,
                initial=_bool(obj.get("initial"), f"{path}.initial"),
                sensor_cost=_parse_cost(obj.get("sensor_cost"), f"{path}.sensor_cost"),
                description=_string(
                    obj.get("description", variable_id), f"{path}.description"
                ),
            )
        )
    if not variables:
        raise ValidationError("$.variables: expected at least one boolean variable")
    ids = [variable.id for variable in variables]
    if len(set(ids)) != len(ids):
        raise ValidationError("$.variables: variable ids must be unique")
    return tuple(variables)


def _parse_actions(raw: Any, variables: set[str]) -> tuple[Action, ...]:
    actions: list[Action] = []
    for index, item in enumerate(_array(raw, "$.actions")):
        path = f"$.actions[{index}]"
        obj = _object(item, path)
        _reject_unknown(
            obj,
            {
                "id",
                "guard",
                "effects",
                "max_occurrences",
                "tags",
                "sensor_cost",
                "description",
            },
            path,
        )
        action_id = _string(obj.get("id"), f"{path}.id")
        guard = obj.get("guard", True)
        validate_expr(guard, variables, f"{path}.guard")
        effects: list[Effect] = []
        written: set[str] = set()
        for effect_index, effect_raw in enumerate(
            _array(obj.get("effects"), f"{path}.effects")
        ):
            effect_path = f"{path}.effects[{effect_index}]"
            effect_obj = _object(effect_raw, effect_path)
            _reject_unknown(effect_obj, {"set"}, effect_path)
            set_obj = _object(effect_obj.get("set"), f"{effect_path}.set")
            _reject_unknown(set_obj, {"var", "value"}, f"{effect_path}.set")
            variable = _string(set_obj.get("var"), f"{effect_path}.set.var")
            if variable not in variables:
                raise ValidationError(
                    f"{effect_path}.set.var: unknown variable {variable!r}"
                )
            if variable in written:
                raise ValidationError(
                    f"{path}: variable {variable!r} is written more than once"
                )
            value = set_obj.get("value")
            validate_expr(value, variables, f"{effect_path}.set.value")
            written.add(variable)
            effects.append(Effect(variable=variable, value=value))
        if not effects:
            raise ValidationError(f"{path}.effects: expected at least one state update")
        tags = tuple(
            _string(tag, f"{path}.tags[]")
            for tag in _array(obj.get("tags", []), f"{path}.tags")
        )
        actions.append(
            Action(
                id=action_id,
                guard=guard,
                effects=tuple(effects),
                max_occurrences=_positive(
                    obj.get("max_occurrences", 1), f"{path}.max_occurrences"
                ),
                tags=tags,
                sensor_cost=_parse_cost(obj.get("sensor_cost"), f"{path}.sensor_cost"),
                description=_string(
                    obj.get("description", action_id), f"{path}.description"
                ),
            )
        )
    if not actions:
        raise ValidationError("$.actions: expected at least one action")
    if len(actions) > MAX_ACTIONS:
        raise ValidationError(f"$.actions: at most {MAX_ACTIONS} actions are supported")
    ids = [action.id for action in actions]
    if len(set(ids)) != len(ids):
        raise ValidationError("$.actions: action ids must be unique")
    return tuple(actions)


def _parse_channels(
    raw: Any, action_ids: set[str], variable_ids: set[str]
) -> tuple[Channel, ...]:
    channels: list[Channel] = []
    for index, item in enumerate(_array(raw, "$.channels")):
        path = f"$.channels[{index}]"
        obj = _object(item, path)
        _reject_unknown(
            obj,
            {
                "id",
                "deployed",
                "visible_actions",
                "visible_state",
                "cost",
                "description",
            },
            path,
        )
        channel_id = _string(obj.get("id"), f"{path}.id")
        visible_actions = tuple(
            _string(value, f"{path}.visible_actions[]")
            for value in _array(obj.get("visible_actions", []), f"{path}.visible_actions")
        )
        visible_state = tuple(
            _string(value, f"{path}.visible_state[]")
            for value in _array(obj.get("visible_state", []), f"{path}.visible_state")
        )
        unknown_actions = set(visible_actions) - action_ids
        unknown_state = set(visible_state) - variable_ids
        if unknown_actions:
            raise ValidationError(
                f"{path}.visible_actions: unknown actions {sorted(unknown_actions)}"
            )
        if unknown_state:
            raise ValidationError(
                f"{path}.visible_state: unknown variables {sorted(unknown_state)}"
            )
        if len(set(visible_actions)) != len(visible_actions):
            raise ValidationError(f"{path}.visible_actions: duplicates are not allowed")
        if len(set(visible_state)) != len(visible_state):
            raise ValidationError(f"{path}.visible_state: duplicates are not allowed")
        if not visible_actions and not visible_state:
            raise ValidationError(
                f"{path}: a channel must observe at least one action or state field"
            )
        channels.append(
            Channel(
                id=channel_id,
                deployed=_bool(obj.get("deployed", False), f"{path}.deployed"),
                visible_actions=visible_actions,
                visible_state=visible_state,
                cost=_parse_cost(obj.get("cost"), f"{path}.cost"),
                description=_string(
                    obj.get("description", channel_id), f"{path}.description"
                ),
            )
        )
    if not channels:
        raise ValidationError("$.channels: expected at least one channel")
    ids = [channel.id for channel in channels]
    if len(set(ids)) != len(ids):
        raise ValidationError("$.channels: channel ids must be unique")
    return tuple(channels)


def _parse_templates(
    raw: Any, action_tags: set[str], variable_ids: set[str]
) -> tuple[SensorTemplate, ...]:
    templates: list[SensorTemplate] = []
    for index, item in enumerate(_array(raw, "$.sensor_templates")):
        path = f"$.sensor_templates[{index}]"
        obj = _object(item, path)
        _reject_unknown(
            obj,
            {"id", "kind", "action_tags", "variables", "cost", "description"},
            path,
        )
        template_id = _string(obj.get("id"), f"{path}.id")
        kind = _string(obj.get("kind"), f"{path}.kind")
        if kind not in {"action", "state"}:
            raise ValidationError(f"{path}.kind: expected 'action' or 'state'")
        tags = tuple(
            _string(value, f"{path}.action_tags[]")
            for value in _array(obj.get("action_tags", []), f"{path}.action_tags")
        )
        variables = tuple(
            _string(value, f"{path}.variables[]")
            for value in _array(obj.get("variables", []), f"{path}.variables")
        )
        if kind == "action":
            if not tags:
                raise ValidationError(f"{path}.action_tags: expected at least one tag")
            unknown = set(tags) - action_tags
            if unknown:
                raise ValidationError(
                    f"{path}.action_tags: unknown tags {sorted(unknown)}"
                )
            if variables:
                raise ValidationError(f"{path}.variables: action template must be empty")
        else:
            if not variables:
                raise ValidationError(f"{path}.variables: expected at least one variable")
            unknown = set(variables) - variable_ids
            if unknown:
                raise ValidationError(
                    f"{path}.variables: unknown variables {sorted(unknown)}"
                )
            if tags:
                raise ValidationError(f"{path}.action_tags: state template must be empty")
        templates.append(
            SensorTemplate(
                id=template_id,
                kind=kind,
                action_tags=tags,
                variables=variables,
                cost=_parse_cost(obj.get("cost"), f"{path}.cost"),
                description=_string(
                    obj.get("description", template_id), f"{path}.description"
                ),
            )
        )
    ids = [template.id for template in templates]
    if len(set(ids)) != len(ids):
        raise ValidationError("$.sensor_templates: template ids must be unique")
    return tuple(templates)


def _parse_aliases(raw: Any, action_ids: set[str]) -> tuple[TraceAlias, ...]:
    aliases: list[TraceAlias] = []
    for index, item in enumerate(_array(raw, "$.trace_aliases")):
        path = f"$.trace_aliases[{index}]"
        obj = _object(item, path)
        _reject_unknown(obj, {"id", "trace", "description"}, path)
        alias_id = _string(obj.get("id"), f"{path}.id")
        trace = tuple(
            _string(value, f"{path}.trace[]")
            for value in _array(obj.get("trace"), f"{path}.trace")
        )
        unknown = set(trace) - action_ids
        if unknown:
            raise ValidationError(f"{path}.trace: unknown actions {sorted(unknown)}")
        aliases.append(
            TraceAlias(
                id=alias_id,
                trace=trace,
                description=_string(
                    obj.get("description", alias_id), f"{path}.description"
                ),
            )
        )
    ids = [alias.id for alias in aliases]
    traces = [alias.trace for alias in aliases]
    if len(set(ids)) != len(ids):
        raise ValidationError("$.trace_aliases: ids must be unique")
    if len(set(traces)) != len(traces):
        raise ValidationError("$.trace_aliases: traces must be unique")
    return tuple(aliases)


def load_model(path: Path) -> WorkflowModel:
    source_path = path.resolve()
    raw = _object(load_json(source_path), "$")
    allowed = {
        "schema_version",
        "name",
        "namespace_prefix",
        "max_depth",
        "max_histories",
        "max_refinements",
        "cost_weights",
        "variables",
        "actions",
        "terminal",
        "claim",
        "channels",
        "sensor_templates",
        "trace_aliases",
    }
    _reject_unknown(raw, allowed, "$")
    if raw.get("schema_version") != MODEL_SCHEMA:
        raise ValidationError(
            f"$.schema_version: expected {MODEL_SCHEMA!r}, got {raw.get('schema_version')!r}"
        )
    namespace_prefix = _string(raw.get("namespace_prefix"), "$.namespace_prefix")
    if not _NAMESPACE_RE.fullmatch(namespace_prefix):
        raise ValidationError("$.namespace_prefix: invalid Lean namespace prefix")
    variables = _parse_variables(raw.get("variables"))
    variable_ids = {variable.id for variable in variables}
    actions = _parse_actions(raw.get("actions"), variable_ids)
    action_ids = {action.id for action in actions}
    action_tags = {tag for action in actions for tag in action.tags}
    terminal = raw.get("terminal")
    claim = raw.get("claim")
    validate_expr(terminal, variable_ids, "$.terminal")
    validate_expr(claim, variable_ids, "$.claim")
    channels = _parse_channels(raw.get("channels"), action_ids, variable_ids)
    templates = _parse_templates(
        raw.get("sensor_templates", []), action_tags, variable_ids
    )
    aliases = _parse_aliases(raw.get("trace_aliases", []), action_ids)
    max_depth = _positive(raw.get("max_depth"), "$.max_depth")
    if max_depth > MAX_DEPTH:
        raise ValidationError(f"$.max_depth: at most {MAX_DEPTH} is supported")
    model = WorkflowModel(
        source_path=source_path,
        name=_string(raw.get("name"), "$.name"),
        namespace_prefix=namespace_prefix,
        max_depth=max_depth,
        max_histories=_positive(raw.get("max_histories", 4096), "$.max_histories"),
        max_refinements=_positive(raw.get("max_refinements", 8), "$.max_refinements"),
        cost_weights=_parse_cost(raw.get("cost_weights"), "$.cost_weights"),
        variables=variables,
        actions=actions,
        terminal=terminal,
        claim=claim,
        channels=channels,
        sensor_templates=templates,
        trace_aliases=aliases,
    )
    if model.cost_weights == ZERO_COST:
        raise ValidationError("$.cost_weights: at least one weight must be positive")
    return model
