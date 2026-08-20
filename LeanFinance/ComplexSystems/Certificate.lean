import LeanFinance.ComplexSystems.Claim
import LeanFinance.Backtest.NoFutureInformation

namespace LeanFinance.ComplexSystems

/-- Proof-carrying allocation decision. It certifies policy execution and
    point-in-time admissibility, not profitability or statistical correctness of
    the state estimator. -/
structure AllocationCertificate
    (claim : AllocationClaim)
    (decision : Backtest.Decision) where
  accepted : claim.check = true
  noFutureInformation : Backtest.NoFutureInformation decision
  decisionTimeBound : claim.decisionTime = decision.decisionTime
  policyHashBound : claim.policyHash = decision.parameterHash
  stateFeature : Backtest.FeatureLineage
  stateFeatureUsed : stateFeature ∈ decision.features
  stateFeatureBound : Backtest.FeatureBoundToInputs stateFeature

namespace AllocationCertificate

theorem valid
    (claim : AllocationClaim)
    (decision : Backtest.Decision)
    (certificate : AllocationCertificate claim decision) :
    claim.Valid :=
  AllocationClaim.check_sound claim certificate.accepted

theorem target_matches_policy
    (claim : AllocationClaim)
    (decision : Backtest.Decision)
    (certificate : AllocationCertificate claim decision) :
    claim.claimedTargetRiskUnits = targetRiskUnits claim.state :=
  (valid claim decision certificate).1

theorem action_matches_policy
    (claim : AllocationClaim)
    (decision : Backtest.Decision)
    (certificate : AllocationCertificate claim decision) :
    claim.claimedAction =
      rebalanceAction claim.currentRiskUnits claim.state :=
  (valid claim decision certificate).2.1

theorem current_allocation_is_unlevered
    (claim : AllocationClaim)
    (decision : Backtest.Decision)
    (certificate : AllocationCertificate claim decision) :
    claim.currentRiskUnits ≤ 100 :=
  (valid claim decision certificate).2.2.1

theorem target_preserves_core
    (claim : AllocationClaim)
    (decision : Backtest.Decision)
    (certificate : AllocationCertificate claim decision) :
    coreRiskUnits ≤ claim.claimedTargetRiskUnits := by
  rw [target_matches_policy claim decision certificate]
  exact targetRiskUnits_core_floor claim.state

theorem target_is_unlevered
    (claim : AllocationClaim)
    (decision : Backtest.Decision)
    (certificate : AllocationCertificate claim decision) :
    claim.claimedTargetRiskUnits ≤ 100 := by
  rw [target_matches_policy claim decision certificate]
  exact targetRiskUnits_at_most_full claim.state

theorem uses_no_future_information
    (claim : AllocationClaim)
    (decision : Backtest.Decision)
    (certificate : AllocationCertificate claim decision) :
    Backtest.NoFutureInformation decision :=
  certificate.noFutureInformation

theorem state_feature_available
    (claim : AllocationClaim)
    (decision : Backtest.Decision)
    (certificate : AllocationCertificate claim decision) :
    Backtest.FeatureAvailableAt
      certificate.stateFeature decision.decisionTime :=
  certificate.noFutureInformation.2
    certificate.stateFeature certificate.stateFeatureUsed

theorem certified_buy_sound
    (claim : AllocationClaim)
    (decision : Backtest.Decision)
    (certificate : AllocationCertificate claim decision)
    (claimedBuy : claim.claimedAction = .buy) :
    claim.currentRiskUnits < claim.claimedTargetRiskUnits := by
  have policyBuy :
      rebalanceAction claim.currentRiskUnits claim.state = .buy := by
    rw [← action_matches_policy claim decision certificate]
    exact claimedBuy
  have below :=
    rebalanceAction_buy_sound claim.currentRiskUnits claim.state policyBuy
  simpa [target_matches_policy claim decision certificate] using below

theorem certified_sell_sound
    (claim : AllocationClaim)
    (decision : Backtest.Decision)
    (certificate : AllocationCertificate claim decision)
    (claimedSell : claim.claimedAction = .sell) :
    claim.claimedTargetRiskUnits < claim.currentRiskUnits := by
  have policySell :
      rebalanceAction claim.currentRiskUnits claim.state = .sell := by
    rw [← action_matches_policy claim decision certificate]
    exact claimedSell
  have above :=
    rebalanceAction_sell_sound claim.currentRiskUnits claim.state policySell
  simpa [target_matches_policy claim decision certificate] using above

end AllocationCertificate

end LeanFinance.ComplexSystems
