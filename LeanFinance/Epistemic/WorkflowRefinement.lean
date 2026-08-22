import LeanFinance.Epistemic.WorkflowTransition

namespace LeanFinance.Epistemic

universe u v w x y z

/-- A conservative embedding of one deterministic workflow into a refined
    workflow. Every original state and action has a distinguished image, and
    the refined workflow agrees with the original workflow on the embedded
    fragment.

    The refined workflow may contain additional states and actions. The
    preservation fields prevent a newly observed attack from being explained by
    silently changing the semantics of histories that the original model
    already understood. -/
structure WorkflowRefinement
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    (original : FiniteWorkflow OriginalState OriginalAction)
    (refined : FiniteWorkflow RefinedState RefinedAction) where
  embedState : OriginalState → RefinedState
  embedAction : OriginalAction → RefinedAction
  initialPreserved : embedState original.initial = refined.initial
  enabledPreserved :
    ∀ state prefix action,
      original.enabled state prefix action =
        refined.enabled
          (embedState state)
          (prefix.map embedAction)
          (embedAction action)
  transitionPreserved :
    ∀ state action,
      embedState (original.transition state action) =
        refined.transition (embedState state) (embedAction action)
  terminalPreserved :
    ∀ state,
      original.terminal state =
        refined.terminal (embedState state)

namespace WorkflowRefinement

/-- Embed an original action trace into the refined action alphabet. -/
def embedTrace
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (trace : List OriginalAction) : List RefinedAction :=
  trace.map refinement.embedAction

/-- Replay preservation from an arbitrary intermediate state and already
    executed prefix. This is the induction principle used by the public replay
    theorem below. -/
theorem replayFrom_preserved
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined) :
    ∀ state prefix trace,
      Option.map refinement.embedState
          (replayFrom original state prefix trace) =
        replayFrom refined
          (refinement.embedState state)
          (prefix.map refinement.embedAction)
          (trace.map refinement.embedAction) := by
  intro state prefix trace
  induction trace generalizing state prefix with
  | nil =>
      rfl
  | cons action rest inductionHypothesis =>
      simp only [replayFrom, List.map_cons]
      rw [← refinement.terminalPreserved state]
      by_cases terminal : original.terminal state
      · simp [terminal]
      · simp [terminal]
        rw [← refinement.enabledPreserved state prefix action]
        by_cases enabled : original.enabled state prefix action
        · simp [enabled]
          simpa [List.map_append,
            refinement.transitionPreserved state action] using
            inductionHypothesis
              (state := original.transition state action)
              (prefix := prefix ++ [action])
        · simp [enabled]

/-- Every result of an original replay is reproduced by the refined workflow
    after embedding the trace. -/
theorem replay_preserved
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (trace : List OriginalAction) :
    Option.map refinement.embedState (replay original trace) =
      replay refined (refinement.embedTrace trace) := by
  unfold replay embedTrace
  rw [← refinement.initialPreserved]
  exact refinement.replayFrom_preserved
    original.initial [] trace

/-- A successful old replay remains successful and ends in the embedded old
    state. -/
theorem replay_some_preserved
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (trace : List OriginalAction)
    (state : OriginalState)
    (replayed : replay original trace = some state) :
    replay refined (refinement.embedTrace trace) =
      some (refinement.embedState state) := by
  have preserved := refinement.replay_preserved trace
  rw [replayed] at preserved
  simpa using preserved.symm

/-- Terminality of every original history is preserved by the embedding. -/
theorem terminal_trace_preserved
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (trace : List OriginalAction)
    (terminal : isTerminalTrace original trace = true) :
    isTerminalTrace refined (refinement.embedTrace trace) = true := by
  unfold isTerminalTrace at terminal ⊢
  cases replayed : replay original trace with
  | none =>
      simp [replayed] at terminal
  | some state =>
      have refinedReplay :
          replay refined (refinement.embedTrace trace) =
            some (refinement.embedState state) :=
        refinement.replay_some_preserved trace state replayed
      have oldTerminal : original.terminal state = true := by
        simpa [replayed] using terminal
      rw [refinedReplay]
      simpa [← refinement.terminalPreserved state] using oldTerminal

end WorkflowRefinement

/-- Claim preservation on the embedded state fragment. -/
def PreservesStateClaim
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (originalClaim : OriginalState → Bool)
    (refinedClaim : RefinedState → Bool) : Prop :=
  ∀ state,
    originalClaim state =
      refinedClaim (refinement.embedState state)

/-- A successful old history has the same claim value after conservative
    refinement. -/
theorem replay_claim_preserved
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (originalClaim : OriginalState → Bool)
    (refinedClaim : RefinedState → Bool)
    (claimPreserved :
      PreservesStateClaim refinement originalClaim refinedClaim)
    (trace : List OriginalAction)
    (state : OriginalState)
    (replayed : replay original trace = some state) :
    refinedClaim (refinement.embedState state) =
      originalClaim state :=
  (claimPreserved state).symm

/-- A trace observation contract for evidence channels that existed before the
    model was refined. The refined model may add new channels and richer
    observations; this contract only requires that old observations embed
    without changing meaning. -/
def PreservesTraceObservation
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {OriginalChannel : Type y}
    {RefinedChannel : Type z}
    {OriginalObservation : Type _}
    {RefinedObservation : Type _}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (embedChannel : OriginalChannel → RefinedChannel)
    (embedObservation : OriginalObservation → RefinedObservation)
    (originalObserve :
      OriginalChannel → List OriginalAction → OriginalObservation)
    (refinedObserve :
      RefinedChannel → List RefinedAction → RefinedObservation) : Prop :=
  ∀ channel trace,
    embedObservation (originalObserve channel trace) =
      refinedObserve
        (embedChannel channel)
        (refinement.embedTrace trace)

/-- Observation preservation is stable under deterministic downstream
    post-processing. -/
theorem postprocess_preserves_trace_observation
    {OriginalState : Type u}
    {OriginalAction : Type v}
    {RefinedState : Type w}
    {RefinedAction : Type x}
    {OriginalChannel : Type y}
    {RefinedChannel : Type z}
    {OriginalObservation : Type _}
    {RefinedObservation : Type _}
    {Output : Type _}
    {original : FiniteWorkflow OriginalState OriginalAction}
    {refined : FiniteWorkflow RefinedState RefinedAction}
    (refinement : WorkflowRefinement original refined)
    (embedChannel : OriginalChannel → RefinedChannel)
    (embedObservation : OriginalObservation → RefinedObservation)
    (originalObserve :
      OriginalChannel → List OriginalAction → OriginalObservation)
    (refinedObserve :
      RefinedChannel → List RefinedAction → RefinedObservation)
    (preserved :
      PreservesTraceObservation refinement embedChannel embedObservation
        originalObserve refinedObserve)
    (postprocess : RefinedObservation → Output) :
    ∀ channel trace,
      postprocess (embedObservation (originalObserve channel trace)) =
        postprocess
          (refinedObserve
            (embedChannel channel)
            (refinement.embedTrace trace)) := by
  intro channel trace
  exact congrArg postprocess (preserved channel trace)

end LeanFinance.Epistemic
