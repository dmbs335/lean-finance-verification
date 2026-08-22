import LeanFinance.Epistemic.WorkflowTransition

namespace LeanFinance.Epistemic

universe u v w x y

/-- Mapping a list through an injective action embedding preserves the number
    of occurrences of every original action. -/
theorem list_count_map_of_injective
    {α : Type u}
    {β : Type v}
    [DecidableEq α]
    [DecidableEq β]
    (mapItem : α → β)
    (injective : Function.Injective mapItem)
    (items : List α)
    (item : α) :
    (items.map mapItem).count (mapItem item) = items.count item := by
  induction items with
  | nil => rfl
  | cons head tail ih =>
      by_cases same : head = item
      · subst head
        simp [ih]
      · have mappedDifferent : mapItem head ≠ mapItem item := by
          intro mappedSame
          exact same (injective mappedSame)
        simp [same, mappedDifferent, ih]

/-- A conservative embedding of one deterministic workflow into another.

Every original action remains available, old enablement decisions are
preserved on embedded executed prefixes, transitions commute with the state
embedding, and terminal classification is unchanged. The refined workflow may
add new states or actions, but it cannot reinterpret an old trace. -/
structure WorkflowRefinement
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    (original : FiniteWorkflow OriginalState OriginalAction)
    (refined : FiniteWorkflow RefinedState RefinedAction) where
  embedState : OriginalState → RefinedState
  embedAction : OriginalAction → RefinedAction
  actionInjective : Function.Injective embedAction
  initialPreserved : embedState original.initial = refined.initial
  actionIncluded :
    ∀ action,
      action ∈ original.actions →
        embedAction action ∈ refined.actions
  enabledPreserved :
    ∀ state executedPrefix action,
      refined.enabled
          (embedState state)
          (executedPrefix.map embedAction)
          (embedAction action) =
        original.enabled state executedPrefix action
  transitionPreserved :
    ∀ state action,
      refined.transition
          (embedState state)
          (embedAction action) =
        embedState (original.transition state action)
  terminalPreserved :
    ∀ state,
      refined.terminal (embedState state) =
        original.terminal state

namespace WorkflowRefinement

/-- Replay commutes with a conservative workflow embedding, including arbitrary
    already-executed action lists used by occurrence bounds. -/
theorem replayFrom_eq_map
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (state : OriginalState)
    (executedPrefix trace : List OriginalAction) :
    replayFrom refined
        (refinement.embedState state)
        (executedPrefix.map refinement.embedAction)
        (trace.map refinement.embedAction) =
      Option.map refinement.embedState
        (replayFrom original state executedPrefix trace) := by
  induction trace generalizing state executedPrefix with
  | nil => rfl
  | cons action rest ih =>
      simp only [List.map_cons, replayFrom]
      rw [refinement.terminalPreserved]
      by_cases terminalNow : original.terminal state = true
      · simp [terminalNow]
      · by_cases enabledNow :
          original.enabled state executedPrefix action = true
        · have recursive :=
            ih
              (state := original.transition state action)
              (executedPrefix := executedPrefix ++ [action])
          simpa [terminalNow, enabledNow,
            refinement.enabledPreserved,
            refinement.transitionPreserved,
            List.map_append] using recursive
        · simp [terminalNow, enabledNow,
            refinement.enabledPreserved]

/-- A complete old trace has exactly the embedded replay result in the refined
    workflow. -/
theorem replay_eq_map
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (trace : List OriginalAction) :
    replay refined (trace.map refinement.embedAction) =
      Option.map refinement.embedState (replay original trace) := by
  unfold replay
  rw [← refinement.initialPreserved]
  simpa using
    replayFrom_eq_map refinement original.initial [] trace

/-- Successful old executions remain successful with the embedded final state. -/
theorem replay_some_preserved
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (trace : List OriginalAction)
    (finalState : OriginalState)
    (replayed : replay original trace = some finalState) :
    replay refined (trace.map refinement.embedAction) =
      some (refinement.embedState finalState) := by
  rw [replay_eq_map refinement, replayed]
  rfl

/-- Failed old executions cannot become valid merely because the action
    alphabet was extended. -/
theorem replay_none_preserved
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (trace : List OriginalAction)
    (replayed : replay original trace = none) :
    replay refined (trace.map refinement.embedAction) = none := by
  rw [replay_eq_map refinement, replayed]
  rfl

/-- Terminal classification of every old trace is preserved. -/
theorem terminal_trace_preserved
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (trace : List OriginalAction) :
    isTerminalTrace refined (trace.map refinement.embedAction) =
      isTerminalTrace original trace := by
  unfold isTerminalTrace
  rw [replay_eq_map refinement]
  cases replayed : replay original trace with
  | none => rfl
  | some state =>
      simp [refinement.terminalPreserved]

end WorkflowRefinement

/-- A semantic refinement additionally preserves an old claim and an arbitrary
    state observation. The observation can represent the old public fields,
    state attestations, or any other state-derived evidence contract. -/
structure SemanticWorkflowRefinement
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {Observation : Type y}
    (original : FiniteWorkflow OriginalState OriginalAction)
    (refined : FiniteWorkflow RefinedState RefinedAction)
    (originalClaim : OriginalState → Bool)
    (refinedClaim : RefinedState → Bool)
    (originalObserve : OriginalState → Observation)
    (refinedObserve : RefinedState → Observation) where
  workflowRefinement : WorkflowRefinement original refined
  claimPreserved :
    ∀ state,
      refinedClaim (workflowRefinement.embedState state) =
        originalClaim state
  observationPreserved :
    ∀ state,
      refinedObserve (workflowRefinement.embedState state) =
        originalObserve state

namespace SemanticWorkflowRefinement

/-- Every old trace retains its claim value after conservative model
    refinement. -/
theorem traceClaimPreserved
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {Observation : Type y}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    {originalClaim : OriginalState → Bool}
    {refinedClaim : RefinedState → Bool}
    {originalObserve : OriginalState → Observation}
    {refinedObserve : RefinedState → Observation}
    (refinement :
      SemanticWorkflowRefinement
        original refined
        originalClaim refinedClaim
        originalObserve refinedObserve)
    (trace : List OriginalAction) :
    (match replay refined
        (trace.map refinement.workflowRefinement.embedAction) with
      | some state => refinedClaim state
      | none => false) =
    (match replay original trace with
      | some state => originalClaim state
      | none => false) := by
  rw [WorkflowRefinement.replay_eq_map
    refinement.workflowRefinement]
  cases replayed : replay original trace with
  | none => rfl
  | some state =>
      simp [refinement.claimPreserved]

/-- Every successful old trace retains its state-derived observation after
    refinement. -/
theorem traceObservationPreserved
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {Observation : Type y}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    {originalClaim : OriginalState → Bool}
    {refinedClaim : RefinedState → Bool}
    {originalObserve : OriginalState → Observation}
    {refinedObserve : RefinedState → Observation}
    (refinement :
      SemanticWorkflowRefinement
        original refined
        originalClaim refinedClaim
        originalObserve refinedObserve)
    (trace : List OriginalAction) :
    Option.map refinedObserve
        (replay refined
          (trace.map refinement.workflowRefinement.embedAction)) =
      Option.map originalObserve (replay original trace) := by
  rw [WorkflowRefinement.replay_eq_map
    refinement.workflowRefinement]
  cases replayed : replay original trace with
  | none => rfl
  | some state =>
      simp [refinement.observationPreserved]

end SemanticWorkflowRefinement

end LeanFinance.Epistemic
