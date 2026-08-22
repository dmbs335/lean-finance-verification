import LeanFinance.Epistemic.Verification

namespace LeanFinance.Epistemic

universe u v w

/-- Histories agree on every selected evidence channel. -/
def ChannelsAgree
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (left right : History) : Prop :=
  ∀ evidenceChannel,
    selected evidenceChannel →
      channel evidenceChannel left = channel evidenceChannel right

/-- A selected family of channels verifies a claim when agreement on those
    channels forces agreement on the claim. -/
def ChannelSelectionVerifies
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop) : Prop :=
  ∀ left right,
    ChannelsAgree channel selected left right →
      (claim left ↔ claim right)

/-- One channel separates two histories when it reports different evidence. -/
def Separates
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (evidenceChannel : Channel)
    (left right : History) : Prop :=
  channel evidenceChannel left ≠ channel evidenceChannel right

/-- Closed finite separator goals are executable whenever observations have
    decidable equality. This keeps generated examples computational without
    requiring each one to unfold `Separates` manually. -/
instance instDecidableSeparates
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    [DecidableEq Observation]
    (channel : Channel → History → Observation)
    (evidenceChannel : Channel)
    (left right : History) :
    Decidable (Separates channel evidenceChannel left right) := by
  unfold Separates
  infer_instance

/-- A selection hits every claim disagreement when every pair of histories with
    different claim truth values is separated by at least one selected
    channel. -/
def HitsEveryClaimDisagreement
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop) : Prop :=
  ∀ left right,
    ¬ (claim left ↔ claim right) →
      ∃ evidenceChannel,
        selected evidenceChannel ∧
          Separates channel evidenceChannel left right

/-- Epistemic cut-set duality. A family of evidence channels verifies a claim
    exactly when it hits the separator set of every pair of histories on which
    the claim disagrees. -/
theorem evidence_cut_set_duality
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop) :
    ChannelSelectionVerifies channel selected claim ↔
      HitsEveryClaimDisagreement channel selected claim := by
  constructor
  · intro verifies left right disagreement
    apply Classical.byContradiction
    intro noSeparator
    have sameEvidence : ChannelsAgree channel selected left right := by
      intro evidenceChannel chosen
      apply Classical.byContradiction
      intro different
      exact noSeparator ⟨evidenceChannel, chosen, different⟩
    exact disagreement (verifies left right sameEvidence)
  · intro hits left right sameEvidence
    apply Classical.byContradiction
    intro disagreement
    rcases hits left right disagreement with
      ⟨evidenceChannel, chosen, separates⟩
    exact separates (sameEvidence evidenceChannel chosen)

/-- Selecting more channels cannot destroy verification. -/
theorem verification_monotone_in_channels
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (smaller larger : Channel → Prop)
    (claim : History → Prop)
    (included : ∀ evidenceChannel,
      smaller evidenceChannel → larger evidenceChannel)
    (verifiedSmaller :
      ChannelSelectionVerifies channel smaller claim) :
    ChannelSelectionVerifies channel larger claim := by
  intro left right sameLarger
  apply verifiedSmaller left right
  intro evidenceChannel chosen
  exact sameLarger evidenceChannel (included evidenceChannel chosen)

/-- A cut set is minimal when deleting any selected channel destroys
    verification. -/
def IsMinimalCutSet
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop) : Prop :=
  ChannelSelectionVerifies channel selected claim ∧
    ∀ removed,
      selected removed →
        ¬ ChannelSelectionVerifies channel
          (fun evidenceChannel =>
            selected evidenceChannel ∧ evidenceChannel ≠ removed)
          claim

/-- If a disagreement pair can only be separated by one channel, every
    verifying selection must contain that channel. -/
theorem necessary_channel_of_unique_separator
    {Channel : Type u}
    {History : Type v}
    {Observation : Type w}
    (channel : Channel → History → Observation)
    (selected : Channel → Prop)
    (claim : History → Prop)
    (required : Channel)
    (left right : History)
    (verified : ChannelSelectionVerifies channel selected claim)
    (leftClaim : claim left)
    (rightNotClaim : ¬ claim right)
    (unique : ∀ candidate,
      Separates channel candidate left right → candidate = required) :
    selected required := by
  have disagreement : ¬ (claim left ↔ claim right) := by
    intro sameClaim
    exact rightNotClaim (sameClaim.mp leftClaim)
  have hits : HitsEveryClaimDisagreement channel selected claim :=
    (evidence_cut_set_duality channel selected claim).mp verified
  rcases hits left right disagreement with
    ⟨candidate, chosen, separates⟩
  have candidateEq : candidate = required := unique candidate separates
  cases candidateEq
  exact chosen

end LeanFinance.Epistemic
