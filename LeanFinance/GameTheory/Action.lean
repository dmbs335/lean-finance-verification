namespace LeanFinance.GameTheory

inductive Side
  | buy
  | hold
  | sell
  deriving DecidableEq, Repr

structure Action where
  side : Side
  quantity : Nat
  deriving DecidableEq, Repr

namespace Action

def zero : Action :=
  { side := Side.hold, quantity := 0 }

end Action
end LeanFinance.GameTheory
