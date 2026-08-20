namespace LeanFinance.Constraints

structure RedemptionState where
  requestedCash : Nat
  cashAvailable : Nat
  liquidPosition : Nat
  deriving Repr

def RedemptionCovered (state : RedemptionState) : Prop :=
  state.requestedCash ≤ state.cashAvailable

def RequiredSale (state : RedemptionState) : Nat :=
  if RedemptionCovered state then 0 else state.liquidPosition

theorem covered_redemption_requires_no_sale
    (state : RedemptionState)
    (h : RedemptionCovered state) :
    RequiredSale state = 0 := by
  simp [RequiredSale, h]

theorem uncovered_redemption_forces_sale
    (state : RedemptionState)
    (h : ¬ RedemptionCovered state) :
    RequiredSale state = state.liquidPosition := by
  simp [RequiredSale, h]

end LeanFinance.Constraints
