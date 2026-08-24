import LeanFinance.Core

namespace LeanFinance.Portfolio

structure EvidenceProfile where
  evidenceDebt : Nat
  robustness : Nat
  dependencyExposure : Nat
  deriving Repr

structure EvidenceAdjustedStrategy (Strategy : Type) where
  strategy : Strategy
  expectedReturn : Int
  risk : Nat
  evidence : EvidenceProfile
  deriving Repr

structure PortfolioObjective where
  riskPenalty : Nat
  debtPenalty : Nat
  robustnessReward : Nat
  deriving Repr

def score
    (objective : PortfolioObjective)
    (strategy : EvidenceAdjustedStrategy Strategy) : Int :=
  strategy.expectedReturn
    - Int.ofNat (objective.riskPenalty * strategy.risk)
    - Int.ofNat (objective.debtPenalty * strategy.evidence.evidenceDebt)
    + Int.ofNat (objective.robustnessReward * strategy.evidence.robustness)

/-- In the formal prototype, debt monotonicity is represented as an explicit
    objective assumption. The market calibration problem is intentionally left
    outside the theorem boundary. -/
theorem higher_debt_reduces_score
    (objective : PortfolioObjective)
    (strategyA strategyB : EvidenceAdjustedStrategy Strategy)
    (sameEconomics :
      strategyA.expectedReturn = strategyB.expectedReturn ∧
      strategyA.risk = strategyB.risk)
    (sameRobustness :
      strategyA.evidence.robustness = strategyB.evidence.robustness)
    (higherDebt :
      strategyB.evidence.evidenceDebt ≥ strategyA.evidence.evidenceDebt)
    (debtMonotone :
      objective.debtPenalty * strategyA.evidence.evidenceDebt ≤
        objective.debtPenalty * strategyB.evidence.evidenceDebt) :
    score objective strategyB ≤ score objective strategyA := by
  simp [score, sameEconomics.1, sameEconomics.2, sameRobustness,
    Int.ofNat_le.2 debtMonotone]

end LeanFinance.Portfolio
