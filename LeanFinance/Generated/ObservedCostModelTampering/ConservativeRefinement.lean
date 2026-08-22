import LeanFinance.Epistemic.ModelRefinement
import LeanFinance.Generated.WorkflowSearch
import LeanFinance.Generated.ObservedCostModelTampering.Search

namespace LeanFinance.Generated.ObservedCostModelTampering.ConservativeRefinement

open LeanFinance.Epistemic

abbrev OriginalState :=
  LeanFinance.Generated.WorkflowIntegrity.Search.State
abbrev OriginalAction :=
  LeanFinance.Generated.WorkflowIntegrity.Search.Action
abbrev RefinedState :=
  LeanFinance.Generated.ObservedCostModelTampering.Search.State
abbrev RefinedAction :=
  LeanFinance.Generated.ObservedCostModelTampering.Search.Action

/-- Embed every original state by assigning the newly learned violation bit its
    safe default value. -/
def embedState (state : OriginalState) : RefinedState :=
  {
    baselineDeclared := state.baselineDeclared
    baselineExecuted := state.baselineExecuted
    hiddenSweepExecuted := state.hiddenSweepExecuted
    futureDataRead := state.futureDataRead
    resultPublished := state.resultPublished
    ledgerAnchored := state.ledgerAnchored
    costModelTampered := false
  }

/-- Embed the complete original action alphabet into the refined alphabet. -/
def embedAction : OriginalAction → RefinedAction
  | .declareBaseline => .declareBaseline
  | .executeBaseline => .executeBaseline
  | .executeHiddenSweep => .executeHiddenSweep
  | .readFutureData => .readFutureData
  | .publishResult => .publishResult
  | .anchorLedger => .anchorLedger

theorem embedAction_injective : Function.Injective embedAction := by
  intro left right same
  cases left <;> cases right <;>
    simp [embedAction] at same ⊢

/-- Public legacy state seen by every pre-refinement state-derived evidence
    contract. -/
structure LegacyObservation where
  baselineDeclared : Bool
  baselineExecuted : Bool
  hiddenSweepExecuted : Bool
  futureDataRead : Bool
  resultPublished : Bool
  ledgerAnchored : Bool
  deriving Repr, DecidableEq

def originalObservation (state : OriginalState) : LegacyObservation :=
  {
    baselineDeclared := state.baselineDeclared
    baselineExecuted := state.baselineExecuted
    hiddenSweepExecuted := state.hiddenSweepExecuted
    futureDataRead := state.futureDataRead
    resultPublished := state.resultPublished
    ledgerAnchored := state.ledgerAnchored
  }

def refinedObservation (state : RefinedState) : LegacyObservation :=
  {
    baselineDeclared := state.baselineDeclared
    baselineExecuted := state.baselineExecuted
    hiddenSweepExecuted := state.hiddenSweepExecuted
    futureDataRead := state.futureDataRead
    resultPublished := state.resultPublished
    ledgerAnchored := state.ledgerAnchored
  }

theorem enabled_preserved
    (state : OriginalState)
    (trace : List OriginalAction)
    (action : OriginalAction) :
    LeanFinance.Generated.ObservedCostModelTampering.Search.enabled
        (embedState state)
        (trace.map embedAction)
        (embedAction action) =
      LeanFinance.Generated.WorkflowIntegrity.Search.enabled
        state trace action := by
  cases action <;>
    simp [
      LeanFinance.Generated.ObservedCostModelTampering.Search.enabled,
      LeanFinance.Generated.WorkflowIntegrity.Search.enabled,
      embedState,
      embedAction,
      list_count_map_of_injective,
      embedAction_injective]

/-- The observed cost-model extension is conservative over the entire original
    workflow: old traces, terminal states, claims, and legacy observations are
    unchanged. -/
def conservativeRefinement :
    SemanticWorkflowRefinement
      LeanFinance.Generated.WorkflowIntegrity.Search.workflow
      LeanFinance.Generated.ObservedCostModelTampering.Search.workflow
      LeanFinance.Generated.WorkflowIntegrity.Search.claimState
      LeanFinance.Generated.ObservedCostModelTampering.Search.claimState
      originalObservation
      refinedObservation :=
  {
    embedState := embedState
    embedAction := embedAction
    actionInjective := embedAction_injective
    initialPreserved := rfl
    actionIncluded := by
      intro action _member
      cases action <;>
        simp [
          LeanFinance.Generated.WorkflowIntegrity.Search.workflow,
          LeanFinance.Generated.ObservedCostModelTampering.Search.workflow,
          embedAction]
    enabledPreserved := enabled_preserved
    transitionPreserved := by
      intro state action
      cases state
      cases action <;> rfl
    terminalPreserved := by
      intro state
      rfl
    claimPreserved := by
      intro state
      simp [
        LeanFinance.Generated.WorkflowIntegrity.Search.claimState,
        LeanFinance.Generated.ObservedCostModelTampering.Search.claimState,
        embedState]
    observationPreserved := by
      intro state
      rfl
  }

theorem old_trace_replay_preserved
    (trace : List OriginalAction) :
    replay
        LeanFinance.Generated.ObservedCostModelTampering.Search.workflow
        (trace.map embedAction) =
      Option.map embedState
        (replay
          LeanFinance.Generated.WorkflowIntegrity.Search.workflow
          trace) :=
  WorkflowRefinement.replay_eq_map
    conservativeRefinement.toWorkflowRefinement trace

theorem old_trace_claim_preserved
    (trace : List OriginalAction) :
    LeanFinance.Generated.ObservedCostModelTampering.Search.traceClaim
        (trace.map embedAction) =
      LeanFinance.Generated.WorkflowIntegrity.Search.traceClaim trace :=
  SemanticWorkflowRefinement.traceClaimPreserved
    conservativeRefinement trace

theorem old_trace_observation_preserved
    (trace : List OriginalAction) :
    Option.map refinedObservation
        (replay
          LeanFinance.Generated.ObservedCostModelTampering.Search.workflow
          (trace.map embedAction)) =
      Option.map originalObservation
        (replay
          LeanFinance.Generated.WorkflowIntegrity.Search.workflow
          trace) :=
  SemanticWorkflowRefinement.traceObservationPreserved
    conservativeRefinement trace

end LeanFinance.Generated.ObservedCostModelTampering.ConservativeRefinement
