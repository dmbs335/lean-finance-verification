import LeanFinance.Epistemic.CutSet

namespace LeanFinance.Epistemic

universe u v w

/-- One selected evidence family verifies every claim in a declared list. -/
def VerifiesAllClaims
    {World : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (channel : Channel → World → Observation)
    (selected : Channel → Prop)
    (claims : List (World → Prop)) : Prop :=
  ∀ claim,
    claim ∈ claims →
      ChannelSelectionVerifies channel selected claim

/-- Pointwise verified claims form a verified multi-claim portfolio. -/
theorem verifies_all_claims_of_each
    {World : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (channel : Channel → World → Observation)
    (selected : Channel → Prop)
    (claims : List (World → Prop))
    (verified :
      ∀ claim,
        claim ∈ claims →
          ChannelSelectionVerifies channel selected claim) :
    VerifiesAllClaims channel selected claims :=
  verified

/-- Conjunction of every claim in a finite portfolio. -/
def ConjoinedClaim
    {World : Type u}
    (claims : List (World → Prop))
    (world : World) : Prop :=
  ∀ claim,
    claim ∈ claims → claim world

/-- Verifying every claim separately is sufficient to verify their conjunction.
    The converse is deliberately not asserted: a conjunction may be constantly
    false while individual claims remain underdetermined. -/
theorem verifies_all_implies_conjoined_claim
    {World : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (channel : Channel → World → Observation)
    (selected : Channel → Prop)
    (claims : List (World → Prop))
    (verified : VerifiesAllClaims channel selected claims) :
    ChannelSelectionVerifies channel selected
      (ConjoinedClaim claims) := by
  intro left right sameEvidence
  constructor
  · intro leftAll claim member
    exact (verified claim member left right sameEvidence).mp
      (leftAll claim member)
  · intro rightAll claim member
    exact (verified claim member left right sameEvidence).mpr
      (rightAll claim member)

/-- Union of claim-specific evidence selections. -/
def ClaimSelectionUnion
    {World : Type u}
    {Channel : Type v}
    (claims : List (World → Prop))
    (selectedFor : (World → Prop) → Channel → Prop)
    (evidenceChannel : Channel) : Prop :=
  ∃ claim,
    claim ∈ claims ∧
      selectedFor claim evidenceChannel

/-- The union of individually sufficient selections is always a sufficient
    multi-claim design, although it need not be globally minimum cost. -/
theorem claim_selection_union_is_sufficient
    {World : Type u}
    {Channel : Type v}
    {Observation : Type w}
    (channel : Channel → World → Observation)
    (claims : List (World → Prop))
    (selectedFor : (World → Prop) → Channel → Prop)
    (eachVerified :
      ∀ claim,
        claim ∈ claims →
          ChannelSelectionVerifies channel (selectedFor claim) claim) :
    VerifiesAllClaims channel
      (ClaimSelectionUnion claims selectedFor) claims := by
  intro claim member
  apply verification_monotone_in_channels
    channel
    (selectedFor claim)
    (ClaimSelectionUnion claims selectedFor)
    claim
  · intro evidenceChannel selected
    exact ⟨claim, member, selected⟩
  · exact eachVerified claim member

end LeanFinance.Epistemic
