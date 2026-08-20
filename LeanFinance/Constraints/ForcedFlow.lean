import LeanFinance.Constraints.MarginCall
import LeanFinance.Constraints.VaR
import LeanFinance.Market.OrderFlow

namespace LeanFinance.Constraints

/-- Policy quantities are nonnegative magnitudes. Forced sales are represented
    as negative signed order flow. -/
structure ForcedLiquidationPolicy where
  marginQuantity : Scalar
  riskQuantity : Scalar
  deriving Repr

def ForcedLiquidationPolicy.WellFormed
    (policy : ForcedLiquidationPolicy) : Prop :=
  0 <= policy.marginQuantity ∧ 0 <= policy.riskQuantity

def marginForcedFlow
    (policy : ForcedLiquidationPolicy)
    (state : MarginState) : Scalar :=
  if marginBreached state then -policy.marginQuantity else 0

def riskForcedFlow
    (policy : ForcedLiquidationPolicy)
    (constraint : VaRConstraint)
    (state : RiskState) : Scalar :=
  if riskBreached constraint state then -policy.riskQuantity else 0

def totalForcedFlow
    (policy : ForcedLiquidationPolicy)
    (marginState : MarginState)
    (riskConstraint : VaRConstraint)
    (riskState : RiskState) : Scalar :=
  marginForcedFlow policy marginState +
    riskForcedFlow policy riskConstraint riskState

theorem marginForcedFlow_eq_zero_of_satisfied
    (policy : ForcedLiquidationPolicy)
    (state : MarginState)
    (satisfied : state.requiredMargin <= state.equity) :
    marginForcedFlow policy state = 0 := by
  have inactive : ¬ marginBreached state := by
    simpa [forcedLiquidationRequired] using
      noForcedLiquidationWhenSatisfied state satisfied
  simp [marginForcedFlow, inactive]

theorem riskForcedFlow_eq_zero_of_underLimit
    (policy : ForcedLiquidationPolicy)
    (constraint : VaRConstraint)
    (state : RiskState)
    (underLimit : state.estimatedVaR <= constraint.limit) :
    riskForcedFlow policy constraint state = 0 := by
  have inactive : ¬ riskBreached constraint state :=
    noRiskBreachWhenUnderLimit constraint state underLimit
  simp [riskForcedFlow, inactive]

/-- When neither constraint binds, the mechanically forced component of order
    flow is exactly zero. -/
theorem totalForcedFlow_eq_zero_of_constraints_satisfied
    (policy : ForcedLiquidationPolicy)
    (marginState : MarginState)
    (riskConstraint : VaRConstraint)
    (riskState : RiskState)
    (marginSatisfied :
      marginState.requiredMargin <= marginState.equity)
    (riskUnderLimit :
      riskState.estimatedVaR <= riskConstraint.limit) :
    totalForcedFlow policy marginState riskConstraint riskState = 0 := by
  rw [totalForcedFlow]
  rw [marginForcedFlow_eq_zero_of_satisfied
    policy marginState marginSatisfied]
  rw [riskForcedFlow_eq_zero_of_underLimit
    policy riskConstraint riskState riskUnderLimit]
  rfl

def attachForcedFlow
    (base : Market.OrderFlow)
    (forced : Scalar) : Market.OrderFlow :=
  { base with forced := forced }

theorem attachForcedFlow_forced
    (base : Market.OrderFlow)
    (forced : Scalar) :
    (attachForcedFlow base forced).forced = forced :=
  rfl

end LeanFinance.Constraints
