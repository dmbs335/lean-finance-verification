namespace LeanFinance.Constraints

structure MarginState where
  equity : Nat
  requiredMargin : Nat
  position : Nat
  deriving Repr

def MarginBreach (state : MarginState) : Prop :=
  state.equity < state.requiredMargin

def ForcedLiquidation (state : MarginState) : Nat :=
  if MarginBreach state then state.position else 0

theorem no_breach_no_forced_liquidation
    (state : MarginState)
    (h : ¬ MarginBreach state) :
    ForcedLiquidation state = 0 := by
  simp [ForcedLiquidation, h]

theorem breach_liquidates_position
    (state : MarginState)
    (h : MarginBreach state) :
    ForcedLiquidation state = state.position := by
  simp [ForcedLiquidation, h]

end LeanFinance.Constraints
