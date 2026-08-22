from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_dumps
from .errors import ValidationError
from .expr import EvalContext, eval_expr
from .model import Action, Channel, CostVector, SensorTemplate, WorkflowModel


@dataclass(frozen=True)
class History:
    id: str
    trace: tuple[str, ...]
    final_state: dict[str, bool]
    claim: bool
    description: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "trace": list(self.trace),
            "final_state": dict(self.final_state),
            "claim": self.claim,
            "description": self.description,
        }


@dataclass(frozen=True)
class ExpandedChannel:
    id: str
    deployed: bool
    visible_actions: tuple[str, ...]
    visible_state: tuple[str, ...]
    cost: CostVector
    description: str
    generated_from: str | None

    def weighted_cost(self, weights: CostVector) -> int:
        return self.cost.weighted(weights)

    def as_dict(self, weights: CostVector) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "deployed": self.deployed,
            "visible_actions": list(self.visible_actions),
            "visible_state": list(self.visible_state),
            "cost": self.cost.as_dict(),
            "weighted_cost": self.weighted_cost(weights),
            "description": self.description,
        }
        if self.generated_from is not None:
            result["generated_from"] = self.generated_from
        return result


def _enabled(action: Action, state: dict[str, bool], trace: tuple[str, ...]) -> bool:
    if trace.count(action.id) >= action.max_occurrences:
        return False
    return eval_expr(action.guard, EvalContext(state))


def _apply(action: Action, state: dict[str, bool]) -> dict[str, bool]:
    original = dict(state)
    context = EvalContext(original)
    updates = {
        effect.variable: eval_expr(effect.value, context)
        for effect in action.effects
    }
    next_state = dict(original)
    next_state.update(updates)
    if next_state == original:
        raise ValidationError(
            f"action {action.id!r} produced a no-op transition; finite workflow actions must change state"
        )
    return next_state


def explore_histories(model: WorkflowModel) -> tuple[History, ...]:
    alias_by_trace = {alias.trace: alias for alias in model.trace_aliases}
    frontier: list[tuple[dict[str, bool], tuple[str, ...]]] = [
        (model.initial_state, tuple())
    ]
    terminals: list[tuple[dict[str, bool], tuple[str, ...]]] = []
    for depth in range(model.max_depth + 1):
        next_frontier: list[tuple[dict[str, bool], tuple[str, ...]]] = []
        for state, trace in frontier:
            if eval_expr(model.terminal, EvalContext(state)):
                terminals.append((state, trace))
                continue
            if depth == model.max_depth:
                continue
            for action in model.actions:
                if not _enabled(action, state, trace):
                    continue
                next_state = _apply(action, state)
                next_trace = trace + (action.id,)
                next_frontier.append((next_state, next_trace))
                if len(next_frontier) + len(terminals) > model.max_histories:
                    raise ValidationError(
                        f"workflow exploration exceeded max_histories={model.max_histories}"
                    )
        frontier = next_frontier
    if not terminals:
        raise ValidationError(
            "workflow exploration found no terminal history within max_depth"
        )
    traces = [trace for _, trace in terminals]
    if len(set(traces)) != len(traces):
        raise AssertionError("deterministic trace expansion emitted a duplicate trace")
    unreachable_aliases = set(alias_by_trace) - set(traces)
    if unreachable_aliases:
        raise ValidationError(
            "trace_aliases contain unreachable traces: "
            + ", ".join("/".join(trace) for trace in sorted(unreachable_aliases))
        )
    histories: list[History] = []
    used_ids: set[str] = set()
    for index, (state, trace) in enumerate(terminals):
        alias = alias_by_trace.get(trace)
        history_id = alias.id if alias is not None else f"history{index}"
        description = (
            alias.description
            if alias is not None
            else " → ".join(trace) or "initial terminal state"
        )
        if history_id in used_ids:
            raise ValidationError(f"duplicate generated history id {history_id!r}")
        used_ids.add(history_id)
        histories.append(
            History(
                id=history_id,
                trace=trace,
                final_state=dict(state),
                claim=eval_expr(model.claim, EvalContext(state)),
                description=description,
            )
        )
    if len({history.claim for history in histories}) < 2:
        raise ValidationError(
            "generated terminal histories do not contain a claim disagreement"
        )
    return tuple(histories)


def expand_channels(model: WorkflowModel) -> tuple[ExpandedChannel, ...]:
    channels: list[ExpandedChannel] = [
        ExpandedChannel(
            id=channel.id,
            deployed=channel.deployed,
            visible_actions=channel.visible_actions,
            visible_state=channel.visible_state,
            cost=channel.cost,
            description=channel.description,
            generated_from=None,
        )
        for channel in model.channels
    ]
    used_ids = {channel.id for channel in channels}
    for template in model.sensor_templates:
        if template.kind == "action":
            for action in model.actions:
                if not set(action.tags).intersection(template.action_tags):
                    continue
                channel_id = f"{template.id}_{action.id}"
                if channel_id in used_ids:
                    raise ValidationError(
                        f"generated channel id collides with existing id: {channel_id}"
                    )
                used_ids.add(channel_id)
                channels.append(
                    ExpandedChannel(
                        id=channel_id,
                        deployed=False,
                        visible_actions=(action.id,),
                        visible_state=tuple(),
                        cost=template.cost + action.sensor_cost,
                        description=(
                            f"{template.description} Action: {action.description}"
                        ),
                        generated_from=f"{template.id}:action:{action.id}",
                    )
                )
        else:
            for variable_id in template.variables:
                variable = model.variable_by_id[variable_id]
                channel_id = f"{template.id}_{variable_id}"
                if channel_id in used_ids:
                    raise ValidationError(
                        f"generated channel id collides with existing id: {channel_id}"
                    )
                used_ids.add(channel_id)
                channels.append(
                    ExpandedChannel(
                        id=channel_id,
                        deployed=False,
                        visible_actions=tuple(),
                        visible_state=(variable_id,),
                        cost=template.cost + variable.sensor_cost,
                        description=(
                            f"{template.description} State: {variable.description}"
                        ),
                        generated_from=f"{template.id}:state:{variable_id}",
                    )
                )
    if len(channels) > 12:
        raise ValidationError(
            "expanded exact synthesis language exceeds 12 channels; tighten sensor templates"
        )
    return tuple(channels)


def observe(channel: ExpandedChannel, history: History) -> dict[str, Any]:
    visible_actions = set(channel.visible_actions)
    return {
        "actions": [
            action_id for action_id in history.trace if action_id in visible_actions
        ],
        "state": [history.final_state[field] for field in channel.visible_state],
    }


def observation_key(channel: ExpandedChannel, history: History) -> str:
    return canonical_dumps(observe(channel, history))
