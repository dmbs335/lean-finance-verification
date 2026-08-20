import LeanFinance.Core

namespace LeanFinance.GameTheory

structure Belief where
  playerId : PlayerId
  fundamental : Scalar
  expectedMarketBelief : Scalar
  expectedHigherOrderBelief : Scalar
  confidenceBps : Nat
  deriving Repr

def Belief.Valid (belief : Belief) : Prop :=
  belief.confidenceBps ≤ 10000

end LeanFinance.GameTheory
