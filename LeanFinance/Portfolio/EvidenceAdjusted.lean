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

/-- Holding expected return, conventional risk, and evidence robustness fixed,
    a weakly larger evidence debt cannot improve the declared objective. The
    conclusion is structural in the supplied objective; whether markets price
    this dimension remains an empirical question. -/
theorem higher_debt_reduces_score
    (objective : PortfolioObjective)
    (strategyA strategyB : EvidenceAdjustedStrategy Strategy)
    (sameEconomics :
      strategyA.expectedReturn = strategyB.expectedReturn ∧
      strategyA.risk = strategyB.risk)
    (sameRobustness :
      strategyA.evidence.robustness = strategyB.evidence.robustness)
    (higherDebt :
      strategyB.evidence.evidenceDebt ≥ strategyA.evidence.evidenceDebt) :
    score objective strategyB ≤ score objective strategyA := by
  unfold score
  rw [← sameEconomics.1, ← sameEconomics.2, ← sameRobustness]
  have debtMonotone :
      objective.debtPenalty * strategyA.evidence.evidenceDebt ≤
        objective.debtPenalty * strategyB.evidence.evidenceDebt :=
    Nat.mul_le_mul_left objective.debtPenalty higherDebt
  have castDebt :
      Int.ofNat
          (objective.debtPenalty * strategyA.evidence.evidenceDebt) ≤
        Int.ofNat
          (objective.debtPenalty * strategyB.evidence.evidenceDebt) :=
    Int.ofNat_le.2 debtMonotone
  have subDebt :
      strategyA.expectedReturn
          - Int.ofNat (objective.riskPenalty * strategyA.risk)
          - Int.ofNat
              (objective.debtPenalty * strategyB.evidence.evidenceDebt) ≤
        strategyA.expectedReturn
          - Int.ofNat (objective.riskPenalty * strategyA.risk)
          - Int.ofNat
              (objective.debtPenalty * strategyA.evidence.evidenceDebt) :=
    Int.sub_le_sub_left castDebt
      (strategyA.expectedReturn
        - Int.ofNat (objective.riskPenalty * strategyA.risk))
  exact Int.add_le_add_right subDebt
    (Int.ofNat
      (objective.robustnessReward * strategyA.evidence.robustness))

end LeanFinance.Portfolio
