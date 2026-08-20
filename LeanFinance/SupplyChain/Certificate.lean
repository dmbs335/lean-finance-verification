import LeanFinance.SupplyChain.Bottleneck
import LeanFinance.Backtest.NoFutureInformation

namespace LeanFinance.SupplyChain

/-- A proof-carrying dynamic bottleneck claim. The empirical values remain in
    the trusted input boundary; Lean checks both point-in-time admissibility and
    the binding inequality computed from those values. -/
structure DynamicBottleneckCertificate
    (node : SupplyNode)
    (decision : Backtest.Decision)
    (finalDemand : Nat) : Prop where
  noFutureInformation : Backtest.NoFutureInformation decision
  binding :
    IsCapacityBottleneckAt node decision.decisionTime finalDemand

theorem DynamicBottleneckCertificate.sound
    (node : SupplyNode)
    (decision : Backtest.Decision)
    (finalDemand : Nat)
    (certificate :
      DynamicBottleneckCertificate node decision finalDemand) :
    effectiveCapacityAt node decision.decisionTime <
      requiredFlow node finalDemand :=
  certificate.binding

theorem DynamicBottleneckCertificate.claimChecks
    (node : SupplyNode)
    (decision : Backtest.Decision)
    (finalDemand : Nat)
    (certificate :
      DynamicBottleneckCertificate node decision finalDemand) :
    (claimOfNode BottleneckKind.capacity node decision.decisionTime
      finalDemand).check = true := by
  apply (BottleneckClaim.check_eq_true_iff_valid _).2
  exact (claimOfNode_valid_iff BottleneckKind.capacity node
    decision.decisionTime finalDemand).2 certificate.binding

theorem DynamicBottleneckCertificate.dataset_available
    (node : SupplyNode)
    (decision : Backtest.Decision)
    (finalDemand : Nat)
    (certificate :
      DynamicBottleneckCertificate node decision finalDemand)
    (dataset : Backtest.Dataset)
    (used : dataset ∈ decision.datasets) :
    dataset.availableAt <= decision.decisionTime :=
  Backtest.noFutureInformation_sound decision
    certificate.noFutureInformation dataset used

/-- A private-rent certificate ties a network scarcity quantity to bounded
    bargaining and ownership weights. The bounds are semantic preconditions;
    the zero-capture and fully-priced theorems remain unconditional. -/
structure DynamicRentCertificate
    (node : SupplyNode)
    (decision : Backtest.Decision)
    (finalDemand : Nat)
    (input : DynamicRentInput) : Prop where
  bottleneck : DynamicBottleneckCertificate node decision finalDemand
  scarcityMatches :
    input.scarcityUnits =
      scarcityUnitsAt node decision.decisionTime finalDemand
  captureWeightBounded : input.captureWeight <= 10000
  ownershipWeightBounded : input.ownershipWeight <= 10000

end LeanFinance.SupplyChain
