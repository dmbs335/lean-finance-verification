namespace LeanFinance.Statistics

/-- One logged one-step decision for a doubly-robust off-policy calculation.
    Probabilities are represented by positive integer weights with a common
    external scale. -/
structure LoggedDecision where
  behaviorWeight : Nat
  targetWeight : Nat
  rewardBps : Int
  loggedActionModelBps : Int
  targetPolicyModelBps : Int
  behaviorPositive : 0 < behaviorWeight
  deriving Repr

namespace LoggedDecision

def residualBps (decision : LoggedDecision) : Int :=
  decision.rewardBps - decision.loggedActionModelBps

/-- Numerator of the one-step doubly-robust contribution under denominator
    `behaviorWeight`. -/
def doublyRobustNumerator (decision : LoggedDecision) : Int :=
  Int.ofNat decision.behaviorWeight * decision.targetPolicyModelBps +
    Int.ofNat decision.targetWeight * decision.residualBps

/-- Expanding the residual preserves the registered arithmetic identity. -/
theorem doubly_robust_numerator_expands
    (decision : LoggedDecision) :
    decision.doublyRobustNumerator =
      Int.ofNat decision.behaviorWeight *
          decision.targetPolicyModelBps +
        Int.ofNat decision.targetWeight *
          (decision.rewardBps - decision.loggedActionModelBps) := by
  rfl

end LoggedDecision

/-- Cross-multiplied effective-sample-size certificate. If weights are `wᵢ`,
    the checked proposition is `minimumESS * Σwᵢ² ≤ (Σwᵢ)²`. -/
structure EffectiveSampleSizeCertificate where
  sumWeights : Nat
  sumSquaredWeights : Nat
  minimumESS : Nat
  denominatorPositive : 0 < sumSquaredWeights
  threshold :
    minimumESS * sumSquaredWeights ≤ sumWeights * sumWeights
  deriving Repr

namespace EffectiveSampleSizeCertificate

theorem clears_registered_threshold
    (certificate : EffectiveSampleSizeCertificate) :
    certificate.minimumESS * certificate.sumSquaredWeights ≤
      certificate.sumWeights * certificate.sumWeights :=
  certificate.threshold

end EffectiveSampleSizeCertificate

end LeanFinance.Statistics
