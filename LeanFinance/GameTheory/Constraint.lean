namespace LeanFinance.GameTheory

structure ConstraintState where
  equity : Nat
  requiredMargin : Nat
  measuredRisk : Nat
  riskLimit : Nat
  grossExposure : Nat
  leverageLimit : Nat
  deriving Repr

def MarginFeasible (state : ConstraintState) : Prop :=
  state.requiredMargin ≤ state.equity

def RiskFeasible (state : ConstraintState) : Prop :=
  state.measuredRisk ≤ state.riskLimit

def LeverageFeasible (state : ConstraintState) : Prop :=
  state.grossExposure ≤ state.leverageLimit

def Feasible (state : ConstraintState) : Prop :=
  MarginFeasible state ∧ RiskFeasible state ∧ LeverageFeasible state

theorem feasible_implies_margin
    (state : ConstraintState)
    (h : Feasible state) : MarginFeasible state :=
  h.1

theorem feasible_implies_risk
    (state : ConstraintState)
    (h : Feasible state) : RiskFeasible state :=
  h.2.1

theorem feasible_implies_leverage
    (state : ConstraintState)
    (h : Feasible state) : LeverageFeasible state :=
  h.2.2

end LeanFinance.GameTheory
