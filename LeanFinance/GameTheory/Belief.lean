namespace LeanFinance.GameTheory

structure Belief where
  playerId : Nat
  confidence : Rat

/-- A simple representation of private belief strength. -/
def Belief.valid (b : Belief) : Prop :=
  0 <= b.confidence ∧ b.confidence <= 1

end LeanFinance.GameTheory
