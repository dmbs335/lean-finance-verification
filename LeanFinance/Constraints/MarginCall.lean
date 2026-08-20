import LeanFinance.GameTheory.Constraint

namespace LeanFinance

structure MarginConstraint where
  collateral : Rat
  maintenanceMargin : Rat

structure MarginState where
  equity : Rat
  requiredMargin : Rat

 def marginBreached (s : MarginState) : Prop :=
  s.equity < s.requiredMargin

end LeanFinance
