namespace LeanFinance.Constraints

structure VaRState where
  measuredRisk : Nat
  riskLimit : Nat
  riskyPosition : Nat
  deriving Repr

def VaRBreach (state : VaRState) : Prop :=
  state.riskLimit < state.measuredRisk

instance decidableVaRBreach (state : VaRState) : Decidable (VaRBreach state) := by
  unfold VaRBreach
  infer_instance

def VaRReduction (state : VaRState) : Nat :=
  if VaRBreach state then state.riskyPosition else 0

theorem no_var_breach_no_reduction
    (state : VaRState)
    (h : ¬ VaRBreach state) :
    VaRReduction state = 0 := by
  simp [VaRReduction, h]

theorem var_breach_reduces_position
    (state : VaRState)
    (h : VaRBreach state) :
    VaRReduction state = state.riskyPosition := by
  simp [VaRReduction, h]

end LeanFinance.Constraints
