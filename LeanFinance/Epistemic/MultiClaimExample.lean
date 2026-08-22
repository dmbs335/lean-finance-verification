import LeanFinance.Epistemic.MultiClaim

namespace LeanFinance.Epistemic.MultiClaimExample

inductive World where
  | honest
  | hiddenSweep
  | futureLeak
  | dualAttack
  deriving Repr, DecidableEq

inductive Channel where
  | hiddenReceipt
  | futureReceipt
  | unifiedAttestation
  deriving Repr, DecidableEq

inductive Observation where
  | absent
  | present
  | honest
  | hidden
  | future
  | dual
  deriving Repr, DecidableEq

def observe : Channel → World → Observation
  | .hiddenReceipt, .honest => .absent
  | .hiddenReceipt, .hiddenSweep => .present
  | .hiddenReceipt, .futureLeak => .absent
  | .hiddenReceipt, .dualAttack => .present
  | .futureReceipt, .honest => .absent
  | .futureReceipt, .hiddenSweep => .absent
  | .futureReceipt, .futureLeak => .present
  | .futureReceipt, .dualAttack => .present
  | .unifiedAttestation, .honest => .honest
  | .unifiedAttestation, .hiddenSweep => .hidden
  | .unifiedAttestation, .futureLeak => .future
  | .unifiedAttestation, .dualAttack => .dual

def noHidden : World → Prop
  | .honest => True
  | .hiddenSweep => False
  | .futureLeak => True
  | .dualAttack => False

def noFuture : World → Prop
  | .honest => True
  | .hiddenSweep => True
  | .futureLeak => False
  | .dualAttack => False

def claims : List (World → Prop) := [noHidden, noFuture]

def hiddenOnly (channel : Channel) : Prop :=
  channel = .hiddenReceipt

def futureOnly (channel : Channel) : Prop :=
  channel = .futureReceipt

def unifiedOnly (channel : Channel) : Prop :=
  channel = .unifiedAttestation

theorem hidden_receipt_verifies_no_hidden :
    ChannelSelectionVerifies observe hiddenOnly noHidden := by
  intro left right sameEvidence
  cases left <;> cases right <;>
    simp_all [ChannelsAgree, hiddenOnly, noHidden, observe]

theorem future_receipt_verifies_no_future :
    ChannelSelectionVerifies observe futureOnly noFuture := by
  intro left right sameEvidence
  cases left <;> cases right <;>
    simp_all [ChannelsAgree, futureOnly, noFuture, observe]

theorem unified_attestation_verifies_all :
    VerifiesAllClaims observe unifiedOnly claims := by
  intro claim member
  simp [claims] at member
  rcases member with rfl | rfl
  · intro left right sameEvidence
    cases left <;> cases right <;>
      simp_all [ChannelsAgree, unifiedOnly, noHidden, observe]
  · intro left right sameEvidence
    cases left <;> cases right <;>
      simp_all [ChannelsAgree, unifiedOnly, noFuture, observe]

/-- The claim-specific union is sufficient but uses two channels. The shared
    attestation verifies both claims with one channel, illustrating evidence
    synergy and why independent minima need not compose optimally. -/
theorem claim_specific_union_is_sufficient :
    VerifiesAllClaims observe
      (fun channel => hiddenOnly channel ∨ futureOnly channel)
      claims := by
  intro claim member
  simp [claims] at member
  rcases member with rfl | rfl
  · exact verification_monotone_in_channels
      observe hiddenOnly
      (fun channel => hiddenOnly channel ∨ futureOnly channel)
      noHidden
      (by intro channel selected; exact Or.inl selected)
      hidden_receipt_verifies_no_hidden
  · exact verification_monotone_in_channels
      observe futureOnly
      (fun channel => hiddenOnly channel ∨ futureOnly channel)
      noFuture
      (by intro channel selected; exact Or.inr selected)
      future_receipt_verifies_no_future

end LeanFinance.Epistemic.MultiClaimExample
