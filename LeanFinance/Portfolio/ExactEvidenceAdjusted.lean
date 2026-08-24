import LeanFinance.Portfolio.EvidenceAdjusted

namespace LeanFinance.Portfolio

/-- Aggregate sufficient statistics for one finite portfolio candidate. Alpha is
    the sum of certifiable lower bounds, not the more optimistic observed
    backtest values. -/
structure PortfolioSummary where
  certifiableAlpha : Int
  risk : Nat
  evidenceDebt : Nat
  robustness : Nat
  dependencyConcentration : Nat
  deriving Repr

/-- Evidence-adjusted allocation extends the single-strategy objective with a
    penalty for shared evidence domains. Calibration remains external. -/
structure PortfolioSelectionObjective extends PortfolioObjective where
  dependencyPenalty : Nat
  deriving Repr

def portfolioScore
    (objective : PortfolioSelectionObjective)
    (portfolio : PortfolioSummary) : Int :=
  portfolio.certifiableAlpha
    - Int.ofNat (objective.riskPenalty * portfolio.risk)
    - Int.ofNat (objective.debtPenalty * portfolio.evidenceDebt)
    + Int.ofNat (objective.robustnessReward * portfolio.robustness)
    - Int.ofNat
        (objective.dependencyPenalty * portfolio.dependencyConcentration)

/-- Holding certifiable alpha, conventional risk, evidence debt, and robustness
    fixed, a portfolio with weakly greater dependency concentration cannot have
    a higher score under a nonnegative declared concentration penalty. -/
theorem higher_dependency_concentration_reduces_score
    (objective : PortfolioSelectionObjective)
    (portfolioA portfolioB : PortfolioSummary)
    (sameAlpha :
      portfolioA.certifiableAlpha = portfolioB.certifiableAlpha)
    (sameRisk : portfolioA.risk = portfolioB.risk)
    (sameDebt : portfolioA.evidenceDebt = portfolioB.evidenceDebt)
    (sameRobustness : portfolioA.robustness = portfolioB.robustness)
    (higherConcentration :
      portfolioB.dependencyConcentration ≥
        portfolioA.dependencyConcentration) :
    portfolioScore objective portfolioB ≤
      portfolioScore objective portfolioA := by
  unfold portfolioScore
  rw [← sameAlpha, ← sameRisk, ← sameDebt, ← sameRobustness]
  have concentrationMonotone :
      objective.dependencyPenalty * portfolioA.dependencyConcentration ≤
        objective.dependencyPenalty * portfolioB.dependencyConcentration :=
    Nat.mul_le_mul_left objective.dependencyPenalty higherConcentration
  have castConcentration :
      Int.ofNat
          (objective.dependencyPenalty *
            portfolioA.dependencyConcentration) ≤
        Int.ofNat
          (objective.dependencyPenalty *
            portfolioB.dependencyConcentration) :=
    Int.ofNat_le.2 concentrationMonotone
  exact Int.sub_le_sub_left castConcentration
    (portfolioA.certifiableAlpha
      - Int.ofNat (objective.riskPenalty * portfolioA.risk)
      - Int.ofNat (objective.debtPenalty * portfolioA.evidenceDebt)
      + Int.ofNat
          (objective.robustnessReward * portfolioA.robustness))

end LeanFinance.Portfolio
