import LeanFinance.Epistemic.CutSet

namespace LeanFinance.Epistemic

universe u v w x

/-- A transition-level evidence semantics for one Boolean integrity claim.

`Transition` is intended to enumerate reachable first-violation transition
classes, not every low-level workflow step. Persistence says that once a
covered violation transition occurs, its receipt remains visible in the final
history observation. Specificity says the same receipt is absent from every
claim-satisfying history. -/
structure TransitionEvidenceSystem
    (History : Type u)
    (Transition : Type v)
    (Channel : Type w) where
  claim : History → Bool
  occurs : Transition → History → Prop
  detects : Channel → Transition → Prop
  observe : Channel → History → Bool
  violationComplete :
    ∀ history,
      claim history = false →
        ∃ transition,
          occurs transition history
  persistent :
    ∀ transition history channel,
      occurs transition history →
        detects channel transition →
          observe channel history = true
  specific :
    ∀ transition history channel,
      claim history = true →
        detects channel transition →
          observe channel history = false

namespace TransitionEvidenceSystem

/-- Proposition-valued interpretation of the system's Boolean claim. -/
def ClaimHolds
    {History : Type u}
    {Transition : Type v}
    {Channel : Type w}
    (system : TransitionEvidenceSystem History Transition Channel)
    (history : History) : Prop :=
  system.claim history = true

end TransitionEvidenceSystem

/-- A selected channel family covers every declared violation-transition class. -/
def CoversViolationTransitions
    {History : Type u}
    {Transition : Type v}
    {Channel : Type w}
    (system : TransitionEvidenceSystem History Transition Channel)
    (selected : Channel → Prop) : Prop :=
  ∀ transition,
    ∃ channel,
      selected channel ∧
        system.detects channel transition

/-- **Persistent transition-cover sufficiency.** If every possible violation
    history contains a declared violation transition, every selected detector
    persists to the final observation, and detectors are specific to violating
    histories, covering all transition classes verifies the terminal claim. -/
theorem transitionCover_implies_verification
    {History : Type u}
    {Transition : Type v}
    {Channel : Type w}
    (system : TransitionEvidenceSystem History Transition Channel)
    (selected : Channel → Prop)
    (cover : CoversViolationTransitions system selected) :
    ChannelSelectionVerifies
      system.observe selected system.ClaimHolds := by
  intro left right sameEvidence
  cases leftClaim : system.claim left with
  | false =>
      cases rightClaim : system.claim right with
      | false =>
          simp [TransitionEvidenceSystem.ClaimHolds,
            leftClaim, rightClaim]
      | true =>
          rcases system.violationComplete left leftClaim with
            ⟨transition, occursLeft⟩
          rcases cover transition with
            ⟨channel, selectedChannel, detectsTransition⟩
          have observedLeft : system.observe channel left = true :=
            system.persistent transition left channel
              occursLeft detectsTransition
          have observedRight : system.observe channel right = false :=
            system.specific transition right channel
              rightClaim detectsTransition
          have same := sameEvidence channel selectedChannel
          rw [observedLeft, observedRight] at same
          cases same
      
  | true =>
      cases rightClaim : system.claim right with
      | false =>
          rcases system.violationComplete right rightClaim with
            ⟨transition, occursRight⟩
          rcases cover transition with
            ⟨channel, selectedChannel, detectsTransition⟩
          have observedLeft : system.observe channel left = false :=
            system.specific transition left channel
              leftClaim detectsTransition
          have observedRight : system.observe channel right = true :=
            system.persistent transition right channel
              occursRight detectsTransition
          have same := sameEvidence channel selectedChannel
          rw [observedLeft, observedRight] at same
          cases same
      | true =>
          simp [TransitionEvidenceSystem.ClaimHolds,
            leftClaim, rightClaim]

/-- A transition witness basis is complete when every transition class has an
    honest/violating history pair such that every channel separating the pair
    detects that transition. This is the normal-form assumption needed for
    transition coverage to be necessary, rather than merely sufficient. -/
def TransitionWitnessComplete
    {History : Type u}
    {Transition : Type v}
    {Channel : Type w}
    (system : TransitionEvidenceSystem History Transition Channel) : Prop :=
  ∀ transition,
    ∃ honest attack,
      system.claim honest = true ∧
        system.claim attack = false ∧
          system.occurs transition attack ∧
            ∀ channel,
              Separates system.observe channel honest attack →
                system.detects channel transition

/-- Under a complete transition-witness basis, every verifying evidence family
    must cover every transition class. -/
theorem verification_implies_transitionCover
    {History : Type u}
    {Transition : Type v}
    {Channel : Type w}
    (system : TransitionEvidenceSystem History Transition Channel)
    (selected : Channel → Prop)
    (witnessComplete : TransitionWitnessComplete system)
    (verifies :
      ChannelSelectionVerifies
        system.observe selected system.ClaimHolds) :
    CoversViolationTransitions system selected := by
  have hits :
      HitsEveryClaimDisagreement
        system.observe selected system.ClaimHolds :=
    (evidence_cut_set_duality
      system.observe selected system.ClaimHolds).mp verifies
  intro transition
  rcases witnessComplete transition with
    ⟨honest, attack, honestClaim, attackClaim,
      occursAttack, separatorDetects⟩
  have disagreement :
      ¬ (system.ClaimHolds honest ↔
        system.ClaimHolds attack) := by
    simp [TransitionEvidenceSystem.ClaimHolds,
      honestClaim, attackClaim]
  rcases hits honest attack disagreement with
    ⟨channel, selectedChannel, separates⟩
  exact ⟨channel, selectedChannel,
    separatorDetects channel separates⟩

/-- **Transition-level safety–observability duality.** Under persistent,
    specific receipts and a complete witness basis, terminal verification is
    equivalent to covering every reachable first-violation transition class. -/
theorem transition_evidence_duality
    {History : Type u}
    {Transition : Type v}
    {Channel : Type w}
    (system : TransitionEvidenceSystem History Transition Channel)
    (selected : Channel → Prop)
    (witnessComplete : TransitionWitnessComplete system) :
    ChannelSelectionVerifies
        system.observe selected system.ClaimHolds ↔
      CoversViolationTransitions system selected :=
  ⟨verification_implies_transitionCover
      system selected witnessComplete,
    transitionCover_implies_verification system selected⟩

/-- A concrete silent violation: the attack contains a declared violation
    transition and changes the claim, but all selected final observations remain
    equal to an honest history. -/
structure SilentViolationWitness
    {History : Type u}
    {Transition : Type v}
    {Channel : Type w}
    (system : TransitionEvidenceSystem History Transition Channel)
    (selected : Channel → Prop) where
  transition : Transition
  honest : History
  attack : History
  honestClaim : system.claim honest = true
  attackClaim : system.claim attack = false
  occursAttack : system.occurs transition attack
  silent :
    ∀ channel,
      selected channel →
        system.observe channel honest =
          system.observe channel attack

namespace SilentViolationWitness

/-- **Silent-violation impossibility.** A selected family that is silent on one
    claim-changing violation pair cannot verify the terminal claim. -/
theorem notVerifiable
    {History : Type u}
    {Transition : Type v}
    {Channel : Type w}
    {system : TransitionEvidenceSystem History Transition Channel}
    {selected : Channel → Prop}
    (witness : SilentViolationWitness system selected) :
    ¬ ChannelSelectionVerifies
      system.observe selected system.ClaimHolds := by
  intro verifies
  have sameEvidence :
      ChannelsAgree system.observe selected
        witness.honest witness.attack := by
    intro channel selectedChannel
    exact witness.silent channel selectedChannel
  have sameClaim :=
    verifies witness.honest witness.attack sameEvidence
  have honestHolds : system.ClaimHolds witness.honest :=
    witness.honestClaim
  have attackDoesNotHold : ¬ system.ClaimHolds witness.attack := by
    simp [TransitionEvidenceSystem.ClaimHolds,
      witness.attackClaim]
  exact attackDoesNotHold (sameClaim.mp honestHolds)

end SilentViolationWitness

end LeanFinance.Epistemic
