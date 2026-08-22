from __future__ import annotations

import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.workflow_cegis.build import BuildResult as WorkflowBuildResult
from tools.workflow_cegis.build import build as build_workflow
from tools.workflow_cegis.canonical import (
    CANONICAL_FORMAT,
    document_digest,
    load_json,
    write_canonical_json,
)
from tools.workflow_cegis.engine import normalized_model
from tools.workflow_cegis.expr import EvalContext, eval_expr
from tools.workflow_cegis.model import WorkflowModel, load_model

from .errors import ValidationError
from .trace import ObservedAttackTrace, TraceStep, load_trace

REPORT_SCHEMA = "lfv-trace-model-refinement-report-v1"
REPORT_DIGEST_SCHEMA = "lfv-trace-model-refinement-report-digest-v1"
MODEL_DIGEST_SCHEMA = "lfv-trace-refined-model-digest-v1"
TRACE_DIGEST_SCHEMA = "lfv-observed-attack-trace-digest-v1"


@dataclass(frozen=True)
class RefinementResult:
    base_model: WorkflowModel
    trace: ObservedAttackTrace
    refined_model_raw: dict[str, Any]
    refined_model: WorkflowModel
    workflow: WorkflowBuildResult
    report: dict[str, Any]
    trace_lean: str


def normalized_trace(trace: ObservedAttackTrace) -> dict[str, Any]:
    return load_json(trace.source_path)


def _cost_dict(cost) -> dict[str, int]:
    return {
        "operational": cost.operational,
        "privacy": cost.privacy,
        "trust": cost.trust,
    }


def _assert_state(
    state: dict[str, bool], expected: dict[str, bool], path: str
) -> None:
    for field, value in expected.items():
        if field not in state:
            raise ValidationError(f"{path}: unknown state field {field!r}")
        if state[field] != value:
            raise ValidationError(
                f"{path}.{field}: observed {value}, model replay has {state[field]}"
            )


def _guard_from_observation(step: TraceStep) -> Any:
    if not step.guard_fields:
        raise ValidationError(
            f"unknown event {step.event!r} needs guard_fields to infer applicability"
        )
    terms: list[Any] = []
    for field in step.guard_fields:
        value = step.observed_before[field]
        terms.append({"var": field} if value else {"not": {"var": field}})
    return terms[0] if len(terms) == 1 else {"all": terms}


def _action_enabled(
    action: dict[str, Any], state: dict[str, bool], trace: list[str]
) -> bool:
    return (
        trace.count(action["id"]) < action["max_occurrences"]
        and eval_expr(action["guard"], EvalContext(state))
    )


def _apply_action(
    action: dict[str, Any], state: dict[str, bool]
) -> dict[str, bool]:
    original = dict(state)
    context = EvalContext(original)
    updates: dict[str, bool] = {}
    for effect in action["effects"]:
        target = effect["set"]["var"]
        updates[target] = eval_expr(effect["set"]["value"], context)
    result = dict(original)
    result.update(updates)
    if result == original:
        raise ValidationError(
            f"event {action['id']!r} is a no-op under the observed pre-state"
        )
    return result


def _extend_claim(raw: dict[str, Any], variable_id: str) -> None:
    extension = {"not": {"var": variable_id}}
    claim = raw["claim"]
    if isinstance(claim, dict) and set(claim) == {"all"}:
        if extension not in claim["all"]:
            claim["all"].append(extension)
    else:
        raw["claim"] = {"all": [claim, extension]}


def _add_variable_extensions(
    raw: dict[str, Any], trace: ObservedAttackTrace
) -> list[dict[str, Any]]:
    existing = {variable["id"]: variable for variable in raw["variables"]}
    added: list[dict[str, Any]] = []
    for extension in trace.variable_extensions:
        if extension.id in existing:
            if existing[extension.id]["initial"] != extension.initial:
                raise ValidationError(
                    f"variable {extension.id!r} already exists with a different initial value"
                )
        else:
            variable = {
                "id": extension.id,
                "initial": extension.initial,
                "sensor_cost": _cost_dict(extension.sensor_cost),
                "description": extension.description,
            }
            raw["variables"].append(variable)
            existing[extension.id] = variable
            added.append(variable)
        if extension.claim_violation:
            _extend_claim(raw, extension.id)
    return added


def _bind_sensor_templates(raw: dict[str, Any], step: TraceStep) -> list[str]:
    if not step.sensor_templates:
        return []
    templates = {template["id"]: template for template in raw["sensor_templates"]}
    updated: list[str] = []
    for template_id in step.sensor_templates:
        if template_id not in templates:
            raise ValidationError(
                f"event {step.event!r}: unknown sensor template {template_id!r}"
            )
        template = templates[template_id]
        if template["kind"] != "action":
            raise ValidationError(
                f"event {step.event!r}: sensor template {template_id!r} is not action-based"
            )
        for tag in step.tags:
            if tag not in template["action_tags"]:
                template["action_tags"].append(tag)
        updated.append(template_id)
    return updated


def _propagate_channels(raw: dict[str, Any], step: TraceStep) -> list[str]:
    channels = {channel["id"]: channel for channel in raw["channels"]}
    updated: list[str] = []
    for channel_id in step.propagate_to_channels:
        if channel_id not in channels:
            raise ValidationError(
                f"event {step.event!r}: unknown channel {channel_id!r}"
            )
        visible = channels[channel_id]["visible_actions"]
        if step.event not in visible:
            visible.append(step.event)
        updated.append(channel_id)
    return updated


def _synthesize_action(
    raw: dict[str, Any],
    trace: ObservedAttackTrace,
    step: TraceStep,
    state: dict[str, bool],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not step.observed_before or not step.observed_after:
        raise ValidationError(
            f"unknown event {step.event!r} needs observed_before and observed_after"
        )
    _assert_state(state, step.observed_before, f"event {step.event}.observed_before")
    unknown_fields = (
        set(step.observed_before) | set(step.observed_after)
    ) - set(state)
    if unknown_fields:
        raise ValidationError(
            f"event {step.event!r}: missing variable_extensions for {sorted(unknown_fields)}"
        )
    effects = [
        {"set": {"var": field, "value": value}}
        for field, value in step.observed_after.items()
        if state[field] != value
    ]
    if not effects:
        raise ValidationError(
            f"unknown event {step.event!r} has no observed state delta"
        )
    if not step.tags:
        raise ValidationError(
            f"unknown event {step.event!r} needs at least one semantic tag"
        )
    action = {
        "id": step.event,
        "guard": _guard_from_observation(step),
        "effects": effects,
        "max_occurrences": trace.event_counts[step.event],
        "tags": list(step.tags),
        "sensor_cost": _cost_dict(step.sensor_cost),
        "description": step.description,
    }
    raw["actions"].append(action)
    bound_templates = _bind_sensor_templates(raw, step)
    propagated_channels = _propagate_channels(raw, step)
    refinement = {
        "event": step.event,
        "reason": "event absent from the current action alphabet",
        "guard_observation": {
            field: step.observed_before[field] for field in step.guard_fields
        },
        "state_delta": {
            effect["set"]["var"]: effect["set"]["value"] for effect in effects
        },
        "synthesized_action": deepcopy(action),
        "bound_sensor_templates": bound_templates,
        "propagated_channels": propagated_channels,
    }
    return action, refinement


def _validate_refined_model(
    raw: dict[str, Any],
) -> tuple[WorkflowModel, Path, tempfile.TemporaryDirectory]:
    temporary = tempfile.TemporaryDirectory(prefix="lfv-trace-refinement-")
    path = Path(temporary.name) / "refined-model.json"
    write_canonical_json(path, raw)
    return load_model(path), path, temporary


def _replay_and_refine(
    base_model: WorkflowModel,
    trace: ObservedAttackTrace,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    raw = deepcopy(normalized_model(base_model))
    raw["name"] = trace.refined_name
    raw["namespace_prefix"] = trace.refined_namespace_prefix
    raw["max_depth"] = max(raw["max_depth"], len(trace.steps))
    added_variables = _add_variable_extensions(raw, trace)
    state = {variable["id"]: variable["initial"] for variable in raw["variables"]}
    executed: list[str] = []
    refinements: list[dict[str, Any]] = []
    original_actions = set(base_model.action_by_id)
    first_original_gap: dict[str, Any] | None = None

    for index, step in enumerate(trace.steps):
        actions = {action["id"]: action for action in raw["actions"]}
        if step.observed_before:
            _assert_state(
                state,
                step.observed_before,
                f"$.steps[{index}].observed_before",
            )
        action = actions.get(step.event)
        if action is None:
            if first_original_gap is None:
                first_original_gap = {
                    "step_index": index,
                    "event": step.event,
                    "reason": "unknown_action",
                }
            action, refinement = _synthesize_action(raw, trace, step, state)
            refinement["step_index"] = index
            refinements.append(refinement)
        elif step.event not in original_actions and first_original_gap is None:
            first_original_gap = {
                "step_index": index,
                "event": step.event,
                "reason": "unknown_action",
            }
        if not _action_enabled(action, state, executed):
            raise ValidationError(
                f"$.steps[{index}]: event {step.event!r} is disabled in state {state}"
            )
        state = _apply_action(action, state)
        executed.append(step.event)
        if step.observed_after:
            _assert_state(
                state,
                step.observed_after,
                f"$.steps[{index}].observed_after",
            )

    # Each synthesized action may lengthen a previously maximal attack trace by
    # one event. Preserve bounded composition coverage rather than only making
    # the one observed trace replayable.
    raw["max_depth"] = max(
        raw["max_depth"],
        base_model.max_depth + len(refinements),
        len(trace.steps),
    )

    if first_original_gap is None:
        raise ValidationError(
            "the observed trace is already expressible by the current action alphabet; "
            "no model refinement is required"
        )
    terminal = eval_expr(raw["terminal"], EvalContext(state))
    claim = eval_expr(raw["claim"], EvalContext(state))
    if terminal != trace.expected_terminal:
        raise ValidationError(
            f"refined replay terminal={terminal}, expected {trace.expected_terminal}"
        )
    if claim != trace.expected_claim:
        raise ValidationError(
            f"refined replay claim={claim}, expected {trace.expected_claim}"
        )
    alias = {
        "id": trace.id,
        "trace": list(trace.event_ids),
        "description": trace.description,
    }
    aliases = {item["id"]: item for item in raw["trace_aliases"]}
    if trace.id in aliases and aliases[trace.id]["trace"] != alias["trace"]:
        raise ValidationError(
            f"trace alias {trace.id!r} already names another workflow trace"
        )
    if trace.id not in aliases:
        raw["trace_aliases"].append(alias)
    replay = {
        "trace": list(trace.event_ids),
        "final_state": state,
        "terminal": terminal,
        "claim": claim,
    }
    metadata = {
        "original_failure": first_original_gap,
        "added_variables": added_variables,
        "iterations": refinements,
        "replay": replay,
    }
    return raw, refinements, metadata


def _trace_separator_analysis(
    workflow_report: dict[str, Any], trace_id: str
) -> dict[str, Any]:
    claims = {
        history["id"]: history["claim"]
        for history in workflow_report["exploration"]["histories"]
    }
    edges = []
    for edge in workflow_report["exact_synthesis"]["disagreement_edges"]:
        if trace_id not in {edge["left"], edge["right"]}:
            continue
        other = edge["right"] if edge["left"] == trace_id else edge["left"]
        if claims.get(other) is True:
            edges.append(edge)
    separator_basis = sorted(
        {channel for edge in edges for channel in edge["separators"]}
    )
    return {
        "honest_attack_edges": edges,
        "separator_basis": separator_basis,
        "greenfield_selection": workflow_report["exact_synthesis"].get(
            "selected", {}
        ).get("channels", []),
        "minimum_repair": workflow_report["exact_repair_synthesis"].get(
            "selected", {}
        ).get("optional_channels", []),
    }


def build_refinement(model_path: Path, trace_path: Path) -> RefinementResult:
    from .lean import render_trace_refinement_lean

    base_model = load_model(model_path)
    trace = load_trace(trace_path)
    refined_raw, _refinements, metadata = _replay_and_refine(base_model, trace)
    refined_model, refined_path, temporary = _validate_refined_model(refined_raw)
    try:
        workflow = build_workflow(refined_path)
    finally:
        temporary.cleanup()
    history_ids = {
        history["id"] for history in workflow.report["exploration"]["histories"]
    }
    if trace.id not in history_ids:
        raise ValidationError(
            "refined transition exploration did not reproduce the observed attack trace"
        )
    trace_analysis = _trace_separator_analysis(workflow.report, trace.id)
    core: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "trace_id": trace.id,
        "base_model_digest": document_digest(
            "traceRefinementBaseModel",
            MODEL_DIGEST_SCHEMA,
            normalized_model(base_model),
        ),
        "trace_digest": document_digest(
            "observedAttackTrace",
            TRACE_DIGEST_SCHEMA,
            normalized_trace(trace),
        ),
        "refined_model_digest": document_digest(
            "traceRefinedModel",
            MODEL_DIGEST_SCHEMA,
            refined_raw,
        ),
        "original_failure": metadata["original_failure"],
        "added_variables": metadata["added_variables"],
        "refinement_iterations": metadata["iterations"],
        "refined_replay": metadata["replay"],
        "generated_history_count": workflow.report["exploration"]["history_count"],
        "generated_channel_count": len(workflow.report["channels"]),
        "separator_analysis": trace_analysis,
    }
    report = dict(core)
    report["report_digest"] = document_digest(
        "traceModelRefinementReport",
        REPORT_DIGEST_SCHEMA,
        core,
    )
    trace_lean = render_trace_refinement_lean(
        base_model=base_model,
        refined_model=refined_model,
        trace=trace,
        report=report,
    )
    return RefinementResult(
        base_model=base_model,
        trace=trace,
        refined_model_raw=refined_raw,
        refined_model=refined_model,
        workflow=workflow,
        report=report,
        trace_lean=trace_lean,
    )


def verify_refinement_report(
    model_path: Path,
    trace_path: Path,
    report: Any,
) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise ValidationError("refinement report must be an object")
    expected = build_refinement(model_path, trace_path).report
    if report != expected:
        raise ValidationError(
            "trace refinement report does not match exact regeneration"
        )
    return report
