namespace LeanFinance

structure EquilibriumState where
  price : Rat
  stability : Rat

structure EquilibriumTransition where
  move : EquilibriumState → EquilibriumState

 def transition (t : EquilibriumTransition) (e : EquilibriumState) : EquilibriumState :=
  t.move e

end LeanFinance
