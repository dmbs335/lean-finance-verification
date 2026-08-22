from __future__ import annotations

from typing import Any

from .canonical import CANONICAL_FORMAT, document_digest
from .cegis import run_cegis as run_exact_repair_cegis
from .errors import ValidationError
from .explore import ExpandedChannel, History, expand_channels, explore_histories, observe
from .model import WorkflowModel

REPORT_SCHEMA = "lfv-workflow-cegis-report-v1"
REPORT_DIGEST_SCHEMA = "lfv-workflow-cegis-report-digest-v1"
MODEL_DIGEST_SCHEMA = "lfv-workflow-cegis-model-digest-v1"


def normalized_model(model: WorkflowModel) -> dict[str, Any]:
    return {
        "schema_version": "lfv-workflow-cegis-model-v1",
        "name": model.name,
        "namespace_prefix": model.namespace_prefix,
        "max_depth": model.max_depth,
        "max_histories": model.max_histories,
        "max_refinements": model.max_refinements,
        "cost_weights": model.cost_weights.as_dict(),
        "variables": [
            {
                "id": variable.id,
                "initial": variable.initial,
                "sensor_cost": variable.sensor_cost.as_dict(),
                "description": variable.description,
            }
            for variable in model.variables
        ],
        "actions": [
            {
                "id": action.id,
                "guard": action.guard,
                "effects": [
                    {"set": {"var": effect.variable, "value": effect.value}}
                    for effect in action.effects
                ],
                "max_occurrences": action.max_occurrences,
                "tags": list(action.tags),
                "sensor_cost": action.sensor_cost.as_dict(),
                "description": action.description,
            }
            for action in model.actions
        ],
        "terminal": model.terminal,
        "claim": model.claim,
        "channels": [
            {
                "id": channel.id,
                "deployed": channel.deployed,
                "visible_actions": list(channel.visible_actions),
                "visible_state": list(channel.visible_state),
                "cost": channel.cost.as_dict(),
                "description": channel.description,
            }
            for channel in model.channels
        ],
        "sensor_templates": [
            {
                "id": template.id,
                "kind": template.kind,
                "action_tags": list(template.action_tags),
                "variables": list(template.variables),
                "cost": template.cost.as_dict(),
                "description": template.description,
            }
            for template in model.sensor_templates
        ],
        "trace_aliases": [
            {
                "id": alias.id,
                "trace": list(alias.trace),
                "description": alias.description,
            }
            for alias in model.trace_aliases
        ],
    }


def _evidence_model(
    model: WorkflowModel,
    histories: tuple[History, ...],
    channels: tuple[ExpandedChannel, ...],
) -> dict[str, Any]:
    return {
        "schema_version": "lfv-evidence-synthesis-model-v1",
        "name": f"{model.name}-generated-evidence-model",
        "namespace": model.evidence_namespace,
        "claim_name": "workflowClaim",
        "cost_weights": model.cost_weights.as_dict(),
        "histories": [
            {
                "id": history.id,
                "claim": history.claim,
                "description": history.description,
            }
            for history in histories
        ],
        "channels": [
            {
                "id": channel.id,
                "cost": channel.cost.as_dict(),
                "observations": {
                    history.id: observe(channel, history) for history in histories
                },
                "description": channel.description,
            }
            for channel in channels
        ],
    }


def run_cegis(model: WorkflowModel) -> dict[str, Any]:
    histories = explore_histories(model)
    channels = expand_channels(model)
    cegis = run_exact_repair_cegis(model, histories, channels)
    evidence_model = _evidence_model(model, histories, channels)
    exact_global = cegis["exact_global_synthesis"]
    exact_repair = cegis["exact_repair_synthesis"]
    core: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "canonical_format": CANONICAL_FORMAT,
        "name": model.name,
        "namespace_prefix": model.namespace_prefix,
        "model_digest": document_digest(
            "workflowCegisModel", MODEL_DIGEST_SCHEMA, normalized_model(model)
        ),
        "exploration": {
            "max_depth": model.max_depth,
            "history_count": len(histories),
            "histories": [history.as_dict() for history in histories],
        },
        "channels": [channel.as_dict(model.cost_weights) for channel in channels],
        "initial_selection": [
            channel.id for channel in channels if channel.deployed
        ],
        "refinement_status": cegis["status"],
        "iterations": cegis["rounds"],
        "refined_selection": (
            cegis["final_selection"]["selected_channels"]
            if cegis["status"] == "synthesized"
            else cegis["rounds"][-1]["candidate"]["selected_channels"]
        ),
        "newly_required_channels": cegis.get("newly_required_channels", []),
        "exact_synthesis": exact_global,
        "exact_repair_synthesis": exact_repair,
        "evidence_model": evidence_model,
        "cegis_digest": cegis["cegis_digest"],
    }
    if cegis["status"] != "synthesized":
        core["failure"] = cegis.get("unresolved_gap")
    if exact_global["status"] == "synthesized" and exact_repair["status"] == "synthesized":
        global_optimal = set(exact_global["selected"]["channels"])
        repaired = set(exact_repair["selected"]["selected_channels"])
        core["deployment_analysis"] = {
            "global_optimal_selection": exact_global["selected"]["channels"],
            "minimum_incremental_repair": exact_repair["selected"][
                "optional_channels"
            ],
            "deployed_but_globally_redundant": sorted(repaired - global_optimal),
            "global_optimal_but_not_in_repair": sorted(global_optimal - repaired),
        }
    report = dict(core)
    report["report_digest"] = document_digest(
        "workflowCegisReport", REPORT_DIGEST_SCHEMA, core
    )
    return report


def verify_report(model: WorkflowModel, report: Any) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise ValidationError("report: expected an object")
    expected = run_cegis(model)
    if report != expected:
        raise ValidationError(
            "workflow CEGIS report does not match exact regeneration"
        )
    return report
