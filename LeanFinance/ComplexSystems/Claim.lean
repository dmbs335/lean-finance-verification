import LeanFinance.ComplexSystems.Allocation

namespace LeanFinance.ComplexSystems

/-- A serializable allocation claim emitted by an empirical pipeline. Hashes are
    opaque bindings at this layer; Lean checks that they are non-empty and that
    the claimed target and action exactly match the formal policy. -/
structure AllocationClaim where
  decisionTime : Timestamp
  state : MarketState
  currentRiskUnits : Nat
  claimedTargetRiskUnits : Nat
  claimedAction : RebalanceAction
  stateHash : ContentHash
  policyHash : ContentHash
  deriving Repr, DecidableEq

namespace AllocationClaim

def Valid (claim : AllocationClaim) : Prop :=
  claim.claimedTargetRiskUnits = targetRiskUnits claim.state ∧
    claim.claimedAction =
      rebalanceAction claim.currentRiskUnits claim.state ∧
    claim.currentRiskUnits ≤ 100 ∧
    NonEmptyString claim.stateHash ∧
    NonEmptyString claim.policyHash

instance instDecidableValid
    (claim : AllocationClaim) : Decidable claim.Valid := by
  unfold Valid NonEmptyString
  infer_instance

def check (claim : AllocationClaim) : Bool :=
  decide claim.Valid

theorem check_eq_true_iff_valid
    (claim : AllocationClaim) :
    claim.check = true ↔ claim.Valid := by
  by_cases valid : claim.Valid
  · simp [check, valid]
  · simp [check, valid]

theorem check_sound
    (claim : AllocationClaim)
    (accepted : claim.check = true) :
    claim.Valid :=
  (check_eq_true_iff_valid claim).mp accepted

end AllocationClaim

end LeanFinance.ComplexSystems
