import LeanFinance.Epistemic.WorkflowTransition

namespace LeanFinance.Epistemic

universe u v w x

/-- Resolve an externally observed event trace into one model's action alphabet. -/
def resolveTrace
    {Event : Type u}
    {Action : Type v}
    (resolve : Event → Option Action) :
    List Event → Option (List Action)
  | [] => some []
  | event :: rest =>
      match resolve event, resolveTrace resolve rest with
      | some action, some actions => some (action :: actions)
      | _, _ => none

/-- A proof-carrying model-refinement witness.

The original model is shown to miss at least one observed event at its action-
alphabet boundary. The refined model resolves the complete event trace, replays
it to the observed final state, and classifies that state as violating the
integrity claim. -/
structure TraceModelRefinementCertificate
    {Event : Type u}
    {OriginalAction : Type v}
    {RefinedAction : Type w}
    {RefinedState : Type x}
    (workflow : FiniteWorkflow RefinedState RefinedAction)
    (claim : RefinedState → Bool) where
  observedTrace : List Event
  originalResolve : Event → Option OriginalAction
  refinedResolve : Event → Option RefinedAction
  originalGap :
    ∃ event : Event,
      event ∈ observedTrace ∧
        originalResolve event = none
  refinedTrace : List RefinedAction
  refinedResolution :
    resolveTrace refinedResolve observedTrace = some refinedTrace
  finalState : RefinedState
  replayed : replay workflow refinedTrace = some finalState
  violates : claim finalState = false

namespace TraceModelRefinementCertificate

theorem originalAlphabetIncomplete
    {Event : Type u}
    {OriginalAction : Type v}
    {RefinedAction : Type w}
    {RefinedState : Type x}
    {workflow : FiniteWorkflow RefinedState RefinedAction}
    {claim : RefinedState → Bool}
    (certificate :
      TraceModelRefinementCertificate
        (Event := Event)
        (OriginalAction := OriginalAction)
        (RefinedAction := RefinedAction)
        (RefinedState := RefinedState)
        workflow claim) :
    ∃ event : Event,
      event ∈ certificate.observedTrace ∧
        certificate.originalResolve event = none :=
  certificate.originalGap

theorem refinedTraceResolves
    {Event : Type u}
    {OriginalAction : Type v}
    {RefinedAction : Type w}
    {RefinedState : Type x}
    {workflow : FiniteWorkflow RefinedState RefinedAction}
    {claim : RefinedState → Bool}
    (certificate :
      TraceModelRefinementCertificate
        (Event := Event)
        (OriginalAction := OriginalAction)
        (RefinedAction := RefinedAction)
        (RefinedState := RefinedState)
        workflow claim) :
    resolveTrace certificate.refinedResolve certificate.observedTrace =
      some certificate.refinedTrace :=
  certificate.refinedResolution

theorem refinedTraceReplays
    {Event : Type u}
    {OriginalAction : Type v}
    {RefinedAction : Type w}
    {RefinedState : Type x}
    {workflow : FiniteWorkflow RefinedState RefinedAction}
    {claim : RefinedState → Bool}
    (certificate :
      TraceModelRefinementCertificate
        (Event := Event)
        (OriginalAction := OriginalAction)
        (RefinedAction := RefinedAction)
        (RefinedState := RefinedState)
        workflow claim) :
    replay workflow certificate.refinedTrace =
      some certificate.finalState :=
  certificate.replayed

theorem refinedTraceViolatesClaim
    {Event : Type u}
    {OriginalAction : Type v}
    {RefinedAction : Type w}
    {RefinedState : Type x}
    {workflow : FiniteWorkflow RefinedState RefinedAction}
    {claim : RefinedState → Bool}
    (certificate :
      TraceModelRefinementCertificate
        (Event := Event)
        (OriginalAction := OriginalAction)
        (RefinedAction := RefinedAction)
        (RefinedState := RefinedState)
        workflow claim) :
    claim certificate.finalState = false :=
  certificate.violates

end TraceModelRefinementCertificate

end LeanFinance.Epistemic
