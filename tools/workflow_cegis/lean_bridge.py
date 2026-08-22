from __future__ import annotations

from typing import Any

from .canonical import canonical_dumps
from .explore import ExpandedChannel, History
from .model import WorkflowModel
from .lean_common import _history_channel_maps, lean_list, unique_identifiers
from .lean_evidence import _observation_catalog

def _raw_observation_expr(
    observation: dict[str, Any], action_ident: dict[str, str]
) -> str:
    actions = [f".{action_ident[action_id]}" for action_id in observation["actions"]]
    state = ["true" if value else "false" for value in observation["state"]]
    return (
        "{ actions := " + lean_list(actions) +
        ", state := " + lean_list(state) + " }"
    )


def render_bridge_lean(
    model: WorkflowModel,
    report: dict[str, Any],
    histories: tuple[History, ...],
    channels: tuple[ExpandedChannel, ...],
) -> str:
    history_ident, channel_ident = _history_channel_maps(histories, channels)
    action_ident = unique_identifiers([action.id for action in model.actions], "action")
    sensor_ident = unique_identifiers([channel.id for channel in channels], "sensor")
    evidence_model = report["evidence_model"]
    observation_values, observation_ident = _observation_catalog(evidence_model)
    namespace = model.bridge_namespace
    workflow_ns = model.workflow_namespace
    evidence_ns = model.evidence_namespace
    refinement_rounds = [
        item for item in report["iterations"] if item["status"] == "counterexample"
    ]
    lines: list[str] = [
        "import LeanFinance.Epistemic.CounterexampleGuided",
        "import LeanFinance.Epistemic.FiniteSynthesisCompleteness",
        f"import {workflow_ns}",
        f"import {evidence_ns}",
        "",
        f"namespace {namespace}",
        "",
        "open LeanFinance.Epistemic",
        f"abbrev WorkflowAction := {workflow_ns}.Action",
        f"abbrev EvidenceHistory := {evidence_ns}.History",
        f"abbrev EvidenceChannel := {evidence_ns}.Channel",
        "",
        "def historyTrace : EvidenceHistory → List WorkflowAction",
    ]
    for history in histories:
        trace = lean_list([f".{action_ident[action_id]}" for action_id in history.trace])
        lines.append(f"  | .{history_ident[history.id]} => {trace}")
    lines += ["", f"def toSensor : EvidenceChannel → {workflow_ns}.Sensor"]
    for channel in channels:
        lines.append(
            f"  | .{channel_ident[channel.id]} => .{sensor_ident[channel.id]}"
        )
    lines.append("")
    for index, encoded in enumerate(observation_values):
        observation = __import__("json").loads(encoded)
        lines += [
            f"def rawObservation{index} : {workflow_ns}.RawObservation :=",
            "  " + _raw_observation_expr(observation, action_ident),
            "",
        ]
    lines += [
        f"def encodeObservation (value : {workflow_ns}.RawObservation) :",
        f"    {evidence_ns}.Observation :=",
    ]
    for index in range(len(observation_values)):
        prefix = "  if" if index == 0 else "  else if"
        lines.append(
            f"{prefix} value == rawObservation{index} then .{observation_ident[observation_values[index]]}"
        )
    lines += [
        "  else .obs0",
        "",
        "def projectedObservation",
        "    (channel : EvidenceChannel)",
        "    (trace : List WorkflowAction) :",
        f"    {evidence_ns}.Observation :=",
        "  encodeObservation",
        f"    ({workflow_ns}.projectTrace (toSensor channel) trace)",
        "",
        "theorem generated_history_catalog_complete :",
        f"    {evidence_ns}.histories.map historyTrace =",
        f"      {workflow_ns}.generatedTraces := by",
        "  decide",
        "",
        "theorem generated_claim_matches_workflow :",
        "    ∀ history : EvidenceHistory,",
        f"      {evidence_ns}.claim history =",
        f"        {workflow_ns}.traceClaim (historyTrace history) := by",
        "  intro history",
        "  cases history <;> decide",
        "",
        "theorem generated_observation_matches_workflow :",
        "    ∀ channel : EvidenceChannel,",
        "      ∀ history : EvidenceHistory,",
        f"        {evidence_ns}.observe channel history =",
        "          projectedObservation channel (historyTrace history) := by",
        "  intro channel history",
        "  cases channel <;> cases history <;> decide",
        "",
        "def initialSelection : List EvidenceChannel :=",
        "  " + lean_list(
            [f".{channel_ident[channel_id]}" for channel_id in report["initial_selection"]]
        ),
        "",
    ]

    round_names: list[str] = []
    chain_defs: list[str] = ["initialSelection"]
    for index, item in enumerate(refinement_rounds):
        before_ids = item["candidate"]["selected_channels"]
        after_ids = item["after_candidate"]["selected_channels"]
        counterexample = item["counterexample"]
        left = history_ident[counterexample["left"]]
        right = history_ident[counterexample["right"]]
        separators = [
            channel_id for channel_id in counterexample["separators"]
            if channel_id in set(after_ids)
        ]
        if not separators:
            raise AssertionError("refinement round does not resolve its counterexample")
        separator = channel_ident[separators[0]]
        before_name = f"round{index}Before"
        after_name = f"round{index}After"
        counterexample_name = f"round{index}Counterexample"
        round_name = f"refinementRound{index}"
        round_names.append(round_name)
        chain_defs.extend([before_name, after_name, round_name])
        lines += [
            f"def {before_name} : List EvidenceChannel :=",
            "  " + lean_list([f".{channel_ident[value]}" for value in before_ids]),
            "",
            f"def {after_name} : List EvidenceChannel :=",
            "  " + lean_list([f".{channel_ident[value]}" for value in after_ids]),
            "",
            f"def {counterexample_name} :",
            f"    BoundedCounterexample {evidence_ns}.model {before_name} :=",
            "  {",
            f"    left := .{left}",
            f"    right := .{right}",
            f"    leftMember := by simp [{evidence_ns}.model, {evidence_ns}.histories]",
            f"    rightMember := by simp [{evidence_ns}.model, {evidence_ns}.histories]",
            f"    claimDifferent := by simp [{evidence_ns}.model, {evidence_ns}.claim]",
            "    selectedAgree := by",
            "      intro evidenceChannel member",
            "      cases evidenceChannel <;>",
            f"        simp [{before_name}, {evidence_ns}.model, {evidence_ns}.observe] at member ⊢",
            "  }",
            "",
            f"def {round_name} : CEGISRefinementRound {evidence_ns}.model :=",
            "  {",
            f"    before := {before_name}",
            f"    after := {after_name}",
            f"    counterexample := {counterexample_name}",
            "    resolved := by",
            f"      refine ⟨.{separator}, ?_, ?_⟩",
            f"      · simp [{after_name}]",
            f"      · decide",
            "  }",
            "",
            f"theorem round{index}_refutes_before :",
            f"    ¬ BoundedSelectionVerifies {evidence_ns}.model {before_name} :=",
            f"  {round_name}.beforeDoesNotVerify",
            "",
        ]

    optional_channels = [channel for channel in channels if not channel.deployed]
    repair_mask = report["exact_repair_synthesis"]["selected"]["mask"]
    lines += [
        "def cegisRounds :",
        f"    List (CEGISRefinementRound {evidence_ns}.model) :=",
        "  " + lean_list(round_names),
        "",
        f"abbrev RepairCandidate := Fin {1 << len(optional_channels)}",
        "",
        "/-- Repair candidates retain every already-deployed channel and select",
        "    additional channels by bitmask. -/",
        "def decodeRepairMask (mask : Nat) : List EvidenceChannel :=",
        "  initialSelection",
    ]
    for index, channel in enumerate(optional_channels):
        lines.append(
            f"    ++ (if {evidence_ns}.bitSelected mask {index} then "
            f"[.{channel_ident[channel.id]}] else [])"
        )
    lines += [
        "",
        "def decodeRepair (candidate : RepairCandidate) : List EvidenceChannel :=",
        "  decodeRepairMask candidate.val",
        "",
        "def selectedRepair : RepairCandidate :=",
        f"  ⟨{repair_mask}, by decide⟩",
        "",
        "def refinedSelection : List EvidenceChannel :=",
        "  decodeRepair selectedRepair",
        "",
        "theorem selected_repair_verifies :",
        f"    BoundedSelectionVerifies {evidence_ns}.model refinedSelection := by",
        "  apply boundedVerifiesBool_sound",
        "  decide",
        "",
        "/-- Kernel computation checks every repair that preserves the deployed",
        "    baseline, establishing minimum total cost within that repair language. -/",
        "theorem selected_repair_cost_minimal :",
        "    ∀ candidate : RepairCandidate,",
        f"      boundedVerifiesBool {evidence_ns}.model (decodeRepair candidate) = true →",
        f"        selectionCost {evidence_ns}.model refinedSelection ≤",
        f"          selectionCost {evidence_ns}.model (decodeRepair candidate) := by",
        "  decide",
        "",
        "theorem cegis_chain_connected :",
        "    CEGISChain initialSelection cegisRounds refinedSelection := by",
        "  simp [CEGISChain, cegisRounds, initialSelection, refinedSelection,",
    ]
    if chain_defs:
        lines.append("    " + ", ".join(chain_defs[1:]) + ",")
    lines += [
        f"    selectedRepair, decodeRepair, decodeRepairMask, {evidence_ns}.bitSelected]",
        "",
        "def proofCarryingCEGIS :",
        f"    ProofCarryingCEGIS {evidence_ns}.model",
        "      RepairCandidate decodeRepair selectedRepair :=",
        "  {",
        "    initial := initialSelection",
        "    rounds := cegisRounds",
        "    connected := cegis_chain_connected",
        "    historyComplete := by",
        "      intro history",
        f"      cases history <;> simp [{evidence_ns}.model, {evidence_ns}.histories]",
        "    finalVerified := selected_repair_verifies",
        "    finalOptimal := by",
        "      intro candidate candidateVerifies",
        "      exact selected_repair_cost_minimal candidate",
        f"        (boundedVerifiesBool_complete {evidence_ns}.model",
        "          (decodeRepair candidate) candidateVerifies)",
        "  }",
        "",
        "theorem refined_selection_semantically_verifies :",
        "    ChannelSelectionVerifies",
        f"      {evidence_ns}.model.observe",
        "      (fun evidenceChannel => evidenceChannel ∈ refinedSelection)",
        f"      {evidence_ns}.model.ClaimHolds :=",
        "  proofCarryingCEGIS.finalSemanticallyVerifies",
        "",
        "theorem refined_selection_is_minimum_cost_repair",
        "    (candidate : RepairCandidate)",
        "    (candidateVerifies :",
        f"      BoundedSelectionVerifies {evidence_ns}.model",
        "        (decodeRepair candidate)) :",
        f"    selectionCost {evidence_ns}.model refinedSelection ≤",
        f"      selectionCost {evidence_ns}.model",
        "        (decodeRepair candidate) :=",
        "  proofCarryingCEGIS.finalCostMinimal",
        "    candidate candidateVerifies",
        "",
        f"end {namespace}",
        "",
    ]
    return "\n".join(lines)
