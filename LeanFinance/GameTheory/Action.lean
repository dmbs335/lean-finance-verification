import LeanFinance.Types

namespace LeanFinance.GameTheory

/-- A one-asset action. Multi-asset profiles are represented by a function
    from player identifiers to actions. -/
inductive Action
  | buy (quantity : Scalar)
  | sell (quantity : Scalar)
  | hold
  deriving DecidableEq, Repr

def Action.signedQuantity : Action → Scalar
  | .buy quantity => quantity
  | .sell quantity => -quantity
  | .hold => 0

def Action.WellFormed : Action → Prop
  | .buy quantity => 0 <= quantity
  | .sell quantity => 0 <= quantity
  | .hold => True

end LeanFinance.GameTheory
