import LeanFinance.GameTheory.Player

namespace LeanFinance.GameTheory

structure Constraint where
  leverageLimit : Rat
  riskLimit : Rat


def Feasible (p : Player) (c : Constraint) : Prop :=
  p.leverageLimit ≤ c.leverageLimit

end LeanFinance.GameTheory
