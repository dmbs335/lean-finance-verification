import LeanFinance.GameTheory.Player

namespace LeanFinance.GameTheory

/-- First-, second-, and third-order expectations for a player. -/
structure Belief where
  playerId : PlayerId
  fundamentalExpectation : Scalar
  marketExpectation : Scalar
  higherOrderExpectation : Scalar
  confidence : Scalar
  deriving Repr

def Belief.WellFormed (belief : Belief) : Prop :=
  0 <= belief.confidence ∧ belief.confidence <= 1

end LeanFinance.GameTheory
