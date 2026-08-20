import LeanFinance.StateSpace.Model

namespace LeanFinance.StateSpace

/-- Dynamical labels are intentionally distinct from ex-post bull/bear labels. -/
inductive DynamicalRegime where
  | resilient
  | crowded
  | fragile
  | transition
  | liquidation
  deriving Repr, DecidableEq

/-- Finite empirical evidence for metastability: internal mixing should occur
    faster than expected exit, while one-step retention exceeds a declared floor. -/
structure MetastabilityWitness where
  internalMixingSteps : Nat
  expectedExitSteps : Nat
  retentionBps : ProbabilityBps
  deriving Repr, DecidableEq

def Metastable (witness : MetastabilityWitness) : Prop :=
  witness.internalMixingSteps < witness.expectedExitSteps

instance decidableMetastable (witness : MetastabilityWitness) :
    Decidable (Metastable witness) := by
  unfold Metastable
  infer_instance

structure MetastabilityCertificate
    (witness : MetastabilityWitness)
    (minimumRetentionBps : ProbabilityBps) : Prop where
  timeScaleSeparated : Metastable witness
  retentionThresholdValid : ValidProbabilityBps minimumRetentionBps
  observedRetentionValid : ValidProbabilityBps witness.retentionBps
  retainsMass : minimumRetentionBps ≤ witness.retentionBps

theorem MetastabilityCertificate.sound
    (witness : MetastabilityWitness)
    (minimumRetentionBps : ProbabilityBps)
    (certificate :
      MetastabilityCertificate witness minimumRetentionBps) :
    Metastable witness ∧
      minimumRetentionBps ≤ witness.retentionBps :=
  ⟨certificate.timeScaleSeparated, certificate.retainsMass⟩

/-- Basis-point estimate of which basin is reached first. Unresolved mass allows
    finite-horizon censoring instead of forcing a binary ex-post label. -/
structure CommittorEstimate where
  returnToSourceFirstBps : ProbabilityBps
  reachTargetFirstBps : ProbabilityBps
  unresolvedBps : ProbabilityBps
  normalized :
    returnToSourceFirstBps + reachTargetFirstBps + unresolvedBps = 10000

def InTransitionRegion
    (lower upper : ProbabilityBps)
    (estimate : CommittorEstimate) : Prop :=
  lower < estimate.reachTargetFirstBps ∧
  estimate.reachTargetFirstBps < upper

instance decidableInTransitionRegion
    (lower upper : ProbabilityBps)
    (estimate : CommittorEstimate) :
    Decidable (InTransitionRegion lower upper estimate) := by
  unfold InTransitionRegion
  infer_instance

def CommittedToTarget
    (threshold : ProbabilityBps)
    (estimate : CommittorEstimate) : Prop :=
  threshold ≤ estimate.reachTargetFirstBps

instance decidableCommittedToTarget
    (threshold : ProbabilityBps)
    (estimate : CommittorEstimate) :
    Decidable (CommittedToTarget threshold estimate) := by
  unfold CommittedToTarget
  infer_instance

structure TransitionBoundaryCertificate
    (estimate : CommittorEstimate)
    (lower upper : ProbabilityBps) : Prop where
  ordered : lower < upper
  inside : InTransitionRegion lower upper estimate
  targetProbabilityValid :
    ValidProbabilityBps estimate.reachTargetFirstBps

theorem TransitionBoundaryCertificate.sound
    (estimate : CommittorEstimate)
    (lower upper : ProbabilityBps)
    (certificate :
      TransitionBoundaryCertificate estimate lower upper) :
    lower < estimate.reachTargetFirstBps ∧
      estimate.reachTargetFirstBps < upper :=
  certificate.inside

theorem TransitionBoundaryCertificate.not_committed_to_target
    {estimate : CommittorEstimate}
    {lower upper : ProbabilityBps}
    (certificate :
      TransitionBoundaryCertificate estimate lower upper)
    (threshold : ProbabilityBps)
    (upperLeThreshold : upper ≤ threshold) :
    ¬ CommittedToTarget threshold estimate := by
  intro committed
  have impossible :
      estimate.reachTargetFirstBps <
        estimate.reachTargetFirstBps :=
    Nat.lt_of_lt_of_le certificate.inside.2
      (Nat.le_trans upperLeThreshold committed)
  exact (Nat.lt_irrefl _) impossible

/-- Cumulative first-passage probabilities must be monotone in the horizon. -/
structure FirstPassageForecast where
  shortHorizon : Nat
  longHorizon : Nat
  shortHorizonBps : ProbabilityBps
  longHorizonBps : ProbabilityBps
  horizonMonotone : shortHorizon ≤ longHorizon
  probabilityMonotone : shortHorizonBps ≤ longHorizonBps
  longProbabilityValid : ValidProbabilityBps longHorizonBps

theorem FirstPassageForecast.shortProbabilityValid
    (forecast : FirstPassageForecast) :
    ValidProbabilityBps forecast.shortHorizonBps :=
  Nat.le_trans forecast.probabilityMonotone
    forecast.longProbabilityValid

end LeanFinance.StateSpace
