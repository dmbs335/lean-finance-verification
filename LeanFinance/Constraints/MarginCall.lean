import LeanFinance.Types

namespace LeanFinance.Constraints

structure MarginConstraint where
  collateral : Scalar
  maintenanceMargin : Scalar
  deriving Repr

structure MarginState where
  equity : Scalar
  requiredMargin : Scalar
  deriving Repr

def marginBreached (state : MarginState) : Prop :=
  state.equity < state.requiredMargin

def forcedLiquidationRequired (state : MarginState) : Prop :=
  marginBreached state

theorem noForcedLiquidationWhenSatisfied
    (state : MarginState)
    (satisfied : state.requiredMargin <= state.equity) :
    ¬ forcedLiquidationRequired state := by
  intro breached
  exact (not_lt_of_ge satisfied) breached

end LeanFinance.Constraints
