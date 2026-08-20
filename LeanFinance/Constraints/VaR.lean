import LeanFinance.Types

namespace LeanFinance.Constraints

structure VaRConstraint where
  confidence : Scalar
  limit : Scalar
  deriving Repr

structure RiskState where
  estimatedVaR : Scalar
  deriving Repr

def VaRConstraint.WellFormed (constraint : VaRConstraint) : Prop :=
  0 <= constraint.confidence ∧
  constraint.confidence <= 1 ∧
  0 <= constraint.limit

def riskBreached (constraint : VaRConstraint) (state : RiskState) : Prop :=
  constraint.limit < state.estimatedVaR

theorem noRiskBreachWhenUnderLimit
    (constraint : VaRConstraint)
    (state : RiskState)
    (underLimit : state.estimatedVaR <= constraint.limit) :
    ¬ riskBreached constraint state := by
  intro breached
  exact (not_lt_of_ge underLimit) breached

end LeanFinance.Constraints
