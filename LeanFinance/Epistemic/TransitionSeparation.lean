import LeanFinance.Epistemic.CutSet
import LeanFinance.Epistemic.WorkflowTransition

namespace LeanFinance.Epistemic

universe u v w x

/-- Scan one valid workflow trace for the first action that crosses a Boolean
    state claim from true to false. Invalid or prematurely terminal traces have
    no classified transition. -/
def firstViolationActionFrom
    {State : Type u}
    {Action : Type v}
    (workflow : FiniteWorkflow State Action)
    (safe : State → Bool) :
    State → List Action → List Action → Option Action
  | _state, _executedPrefix, [] => none
  | state, executedPrefix, action :: rest =>
      if workflow.terminal state then
        none
      else if workflow.enabled state executedPrefix action then
        let nextState := workflow.transition state action
        if safe state && !(safe nextState) then
          some action
        else
          firstViolationActionFrom workflow safe
            nextState (executedPrefix ++ [action]) rest
      else
        none

/-- First claim-changing action of a trace from the workflow's initial state. -/
def firstViolationAction
    {State : Type u}
    {Action : Type v}
    (workflow : FiniteWorkflow State Action)
    (safe : State → Bool)
    (trace : List Action) : Option Action :=
  firstViolationActionFrom workflow safe workflow.initial [] trace

/-- A history is safe according to a complete first-violation classifier exactly
    when the classifier returns no violation kind. -/
def FirstViolationClaim
    {History : Type u}
    {Violation : Type v}
    (firstViolation : History → Option Violation)
    (history : History) : Prop :=
  firstViolation history = none

/-- One violation kind occurs in the modeled history space. -/
def FirstViolationOccurs
    {History : Type u}
    {Violation : Type v}
    (firstViolation : History → Option Violation)
    (violation : Violation) : Prop :=
  ∃ history,
    firstViolation history = some violation

/-- Pairwise transition obligation: every safe history and every history whose
    first violation has kind `violation` retain a selected separator. -/
def FirstViolationPairCover
    {History : Type u}
    {Violation : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (firstViolation : History → Option Violation) : Prop :=
  ∀ safeHistory badHistory violation,
    firstViolation safeHistory = none →
      firstViolation badHistory = some violation →
        ∃ evidenceChannel,
          selected evidenceChannel ∧
            Separates channel evidenceChannel safeHistory badHistory

/-- Transition-level safety-observability duality. Grouping bad histories by
    their first claim-changing transition loses no verification information:
    the grouped pair cover is equivalent to verification of first-violation
    absence. -/
theorem first_violation_pair_cover_iff_verification
    {History : Type u}
    {Violation : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (firstViolation : History → Option Violation) :
    FirstViolationPairCover channel selected firstViolation ↔
      ChannelSelectionVerifies channel selected
        (FirstViolationClaim firstViolation) := by
  constructor
  · intro cover left right sameEvidence
    cases leftClass : firstViolation left with
    | none =>
        cases rightClass : firstViolation right with
        | none =>
            simp [FirstViolationClaim, leftClass, rightClass]
        | some violation =>
            rcases cover left right violation
                leftClass rightClass with
              ⟨evidenceChannel, chosen, separates⟩
            exact False.elim
              (separates (sameEvidence evidenceChannel chosen))
    | some leftViolation =>
        cases rightClass : firstViolation right with
        | none =>
            rcases cover right left leftViolation
                rightClass leftClass with
              ⟨evidenceChannel, chosen, separates⟩
            exact False.elim
              (separates
                (sameEvidence evidenceChannel chosen).symm)
        | some rightViolation =>
            simp [FirstViolationClaim, leftClass, rightClass]
  · intro verifies safeHistory badHistory violation
      safeClass badClass
    have claimDisagrees :
        ¬ (FirstViolationClaim firstViolation safeHistory ↔
          FirstViolationClaim firstViolation badHistory) := by
      simp [FirstViolationClaim, safeClass, badClass]
    have hits :
        HitsEveryClaimDisagreement channel selected
          (FirstViolationClaim firstViolation) :=
      (evidence_cut_set_duality channel selected
        (FirstViolationClaim firstViolation)).mp verifies
    exact hits safeHistory badHistory claimDisagrees

/-- One channel persistently and specifically separates every history in a
    first-violation class from every safe history. -/
def PersistentTransitionSeparator
    {History : Type u}
    {Violation : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (firstViolation : History → Option Violation)
    (evidenceChannel : Channel)
    (violation : Violation) : Prop :=
  ∀ safeHistory badHistory,
    firstViolation safeHistory = none →
      firstViolation badHistory = some violation →
        Separates channel evidenceChannel safeHistory badHistory

/-- Every occurring first-violation class has one selected persistent receipt. -/
def PersistentTransitionCover
    {History : Type u}
    {Violation : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (firstViolation : History → Option Violation) : Prop :=
  ∀ violation,
    FirstViolationOccurs firstViolation violation →
      ∃ evidenceChannel,
        selected evidenceChannel ∧
          PersistentTransitionSeparator
            channel firstViolation evidenceChannel violation

/-- A persistent transition cover supplies the exact pairwise cover required by
    the transition duality. -/
theorem persistent_transition_cover_implies_pair_cover
    {History : Type u}
    {Violation : Type v}
    {Channel : Type w}
    {Observation : Type x}
    {channel : Channel → History → Observation}
    {selected : Channel → Prop}
    {firstViolation : History → Option Violation}
    (persistent :
      PersistentTransitionCover channel selected firstViolation) :
    FirstViolationPairCover channel selected firstViolation := by
  intro safeHistory badHistory violation safeClass badClass
  rcases persistent violation ⟨badHistory, badClass⟩ with
    ⟨evidenceChannel, chosen, separates⟩
  exact
    ⟨evidenceChannel, chosen,
      separates safeHistory badHistory safeClass badClass⟩

/-- Persistent and specific receipts for every first-violation class are
    sufficient to verify absence of violations. -/
theorem persistent_transition_cover_implies_verification
    {History : Type u}
    {Violation : Type v}
    {Channel : Type w}
    {Observation : Type x}
    {channel : Channel → History → Observation}
    {selected : Channel → Prop}
    {firstViolation : History → Option Violation}
    (persistent :
      PersistentTransitionCover channel selected firstViolation) :
    ChannelSelectionVerifies channel selected
      (FirstViolationClaim firstViolation) :=
  (first_violation_pair_cover_iff_verification
    channel selected firstViolation).mp
      (persistent_transition_cover_implies_pair_cover persistent)

/-- A concrete safe/bad pair showing that one first violation is silent under
    all selected evidence. -/
structure SilentFirstViolationWitness
    {History : Type u}
    {Violation : Type v}
    {Channel : Type w}
    {Observation : Type x}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (firstViolation : History → Option Violation) where
  safeHistory : History
  badHistory : History
  violation : Violation
  safeClass : firstViolation safeHistory = none
  badClass : firstViolation badHistory = some violation
  selectedAgree :
    ChannelsAgree channel selected safeHistory badHistory

namespace SilentFirstViolationWitness

/-- Silent first-violation impossibility: a selected evidence family that cannot
    observe one claim-changing transition cannot verify violation absence. -/
theorem silent_first_violation_implies_unverifiable
    {History : Type u}
    {Violation : Type v}
    {Channel : Type w}
    {Observation : Type x}
    {channel : Channel → History → Observation}
    {selected : Channel → Prop}
    {firstViolation : History → Option Violation}
    (witness :
      SilentFirstViolationWitness channel selected firstViolation) :
    ¬ ChannelSelectionVerifies channel selected
      (FirstViolationClaim firstViolation) := by
  intro verifies
  have sameClaim :=
    verifies witness.safeHistory witness.badHistory
      witness.selectedAgree
  have safeClaim :
      FirstViolationClaim firstViolation witness.safeHistory := by
    simpa [FirstViolationClaim] using witness.safeClass
  have badNotClaim :
      ¬ FirstViolationClaim firstViolation witness.badHistory := by
    simp [FirstViolationClaim, witness.badClass]
  exact badNotClaim (sameClaim.mp safeClaim)

end SilentFirstViolationWitness

end LeanFinance.Epistemic
