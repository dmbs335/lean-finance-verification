import LeanFinance.Epistemic.FiniteSynthesis

namespace LeanFinance.Epistemic

universe u v w

/-- An optimal evidence selection over one explicit finite candidate language.

    The witness carries semantic verification and the lower-bound proof instead
    of treating an optimizer's reported objective value as trusted input. -/
structure EvidenceDebtWitness
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (candidates : List (List Channel)) where
  selected : List Channel
  selectedAdmissible : selected ∈ candidates
  selectedVerifies : BoundedSelectionVerifies model selected
  minimum :
    ∀ candidate,
      candidate ∈ candidates →
        BoundedSelectionVerifies model candidate →
          selectionCost model selected ≤
            selectionCost model candidate

namespace EvidenceDebtWitness

/-- Minimum verification cost represented by one proof-carrying optimum. -/
def debt
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    {model : BoundedEvidenceModel History Channel Observation}
    {candidates : List (List Channel)}
    (witness : EvidenceDebtWitness model candidates) : Nat :=
  selectionCost model witness.selected

end EvidenceDebtWitness

/-- The small model's bounded history universe is included in the large model's
    universe. -/
def HistoriesIncluded
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (small large : BoundedEvidenceModel History Channel Observation) : Prop :=
  ∀ history,
    history ∈ small.histories →
      history ∈ large.histories

/-- Claims agree pointwise between two bounded models. -/
def ClaimsPreserved
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (small large : BoundedEvidenceModel History Channel Observation) : Prop :=
  ∀ history,
    small.claim history = large.claim history

/-- Existing channels retain the same observation semantics. -/
def ObservationsPreserved
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (small large : BoundedEvidenceModel History Channel Observation) : Prop :=
  ∀ channel history,
    small.observe channel history =
      large.observe channel history

/-- Existing channel costs retain the same interpretation. -/
def CostsPreserved
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (small large : BoundedEvidenceModel History Channel Observation) : Prop :=
  ∀ channel,
    small.cost channel = large.cost channel

/-- Adding possible histories while preserving claims and observations can only
    remove verifying selections. Every selection that verifies the expanded
    adversarial model also verifies its history restriction. -/
theorem verification_antitone_under_history_extension
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (small large : BoundedEvidenceModel History Channel Observation)
    (selected : List Channel)
    (included : HistoriesIncluded small large)
    (claimsPreserved : ClaimsPreserved small large)
    (observationsPreserved : ObservationsPreserved small large)
    (verifiesLarge : BoundedSelectionVerifies large selected) :
    BoundedSelectionVerifies small selected := by
  intro left leftMember right rightMember claimDifferent
  have leftLarge : left ∈ large.histories :=
    included left leftMember
  have rightLarge : right ∈ large.histories :=
    included right rightMember
  have claimDifferentLarge :
      large.claim left ≠ large.claim right := by
    intro sameLargeClaim
    apply claimDifferent
    calc
      small.claim left = large.claim left := claimsPreserved left
      _ = large.claim right := sameLargeClaim
      _ = small.claim right := (claimsPreserved right).symm
  rcases verifiesLarge left leftLarge right rightLarge
      claimDifferentLarge with
    ⟨channel, channelSelected, separatesLarge⟩
  refine ⟨channel, channelSelected, ?_⟩
  intro sameSmallObservation
  apply separatesLarge
  calc
    large.observe channel left = small.observe channel left :=
      (observationsPreserved channel left).symm
    _ = small.observe channel right := sameSmallObservation
    _ = large.observe channel right :=
      observationsPreserved channel right

/-- Pointwise cost preservation implies equality of every selected portfolio's
    scalar cost. -/
theorem selectionCost_eq_of_costs_preserved
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (small large : BoundedEvidenceModel History Channel Observation)
    (costsPreserved : CostsPreserved small large) :
    ∀ selected,
      selectionCost small selected =
        selectionCost large selected := by
  intro selected
  induction selected with
  | nil =>
      rfl
  | cons channel rest inductionHypothesis =>
      simp [selectionCost, costsPreserved channel,
        inductionHypothesis]

/-- **Attack-pressure monotonicity.** With a fixed candidate evidence language,
    conservatively adding possible adversarial histories cannot reduce minimum
    verification cost. -/
theorem evidenceDebt_monotone_under_history_extension
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (small large : BoundedEvidenceModel History Channel Observation)
    (candidates : List (List Channel))
    (included : HistoriesIncluded small large)
    (claimsPreserved : ClaimsPreserved small large)
    (observationsPreserved : ObservationsPreserved small large)
    (costsPreserved : CostsPreserved small large)
    (smallDebt : EvidenceDebtWitness small candidates)
    (largeDebt : EvidenceDebtWitness large candidates) :
    smallDebt.debt ≤ largeDebt.debt := by
  have largeSelectionVerifiesSmall :
      BoundedSelectionVerifies small largeDebt.selected :=
    verification_antitone_under_history_extension
      small large largeDebt.selected included claimsPreserved
      observationsPreserved largeDebt.selectedVerifies
  change selectionCost small smallDebt.selected ≤
    selectionCost large largeDebt.selected
  calc
    selectionCost small smallDebt.selected ≤
        selectionCost small largeDebt.selected :=
      smallDebt.minimum largeDebt.selected
        largeDebt.selectedAdmissible largeSelectionVerifiesSmall
    _ = selectionCost large largeDebt.selected :=
      selectionCost_eq_of_costs_preserved
        small large costsPreserved largeDebt.selected

/-- One finite candidate language is included in another. -/
def CandidateLanguageIncluded
    {Channel : Type v}
    (small large : List (List Channel)) : Prop :=
  ∀ candidate,
    candidate ∈ small → candidate ∈ large

/-- **Sensor-relief antitonicity.** Enlarging the admissible evidence-portfolio
    language cannot increase minimum verification cost. -/
theorem evidenceDebt_antitone_under_candidate_extension
    {History : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (model : BoundedEvidenceModel History Channel Observation)
    (smallCandidates largeCandidates : List (List Channel))
    (included :
      CandidateLanguageIncluded smallCandidates largeCandidates)
    (smallDebt : EvidenceDebtWitness model smallCandidates)
    (largeDebt : EvidenceDebtWitness model largeCandidates) :
    largeDebt.debt ≤ smallDebt.debt := by
  change selectionCost model largeDebt.selected ≤
    selectionCost model smallDebt.selected
  exact largeDebt.minimum smallDebt.selected
    (included smallDebt.selected smallDebt.selectedAdmissible)
    smallDebt.selectedVerifies

/-- Nonnegative verification cost added by expanding the adversarial history
    model while holding the candidate sensor language fixed. -/
def attackPressure (baseDebt expandedDebt : Nat) : Nat :=
  expandedDebt - baseDebt

/-- Verification cost recovered by expanding the candidate sensor language for
    a fixed expanded adversarial model. -/
def sensorRelief (expandedDebt repairedDebt : Nat) : Nat :=
  expandedDebt - repairedDebt

/-- The two monotonic effects form a conservative debt balance. The left side
    starts from the old model and adds attack pressure; the right side starts
    from the repaired model and adds back the cost relieved by new sensors.
    Both sides equal the minimum debt of the expanded model under the old
    sensor language. -/
theorem evidenceDebt_refinement_balance
    (baseDebt expandedDebt repairedDebt : Nat)
    (attackMonotone : baseDebt ≤ expandedDebt)
    (sensorAntitone : repairedDebt ≤ expandedDebt) :
    baseDebt + attackPressure baseDebt expandedDebt =
      repairedDebt + sensorRelief expandedDebt repairedDebt := by
  unfold attackPressure sensorRelief
  calc
    baseDebt + (expandedDebt - baseDebt) = expandedDebt :=
      Nat.add_sub_of_le attackMonotone
    _ = repairedDebt + (expandedDebt - repairedDebt) :=
      (Nat.add_sub_of_le sensorAntitone).symm

end LeanFinance.Epistemic
