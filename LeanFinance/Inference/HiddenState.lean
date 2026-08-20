import LeanFinance.Core

namespace LeanFinance.Inference

structure ObservedMarketData where
  timestamp : Timestamp
  price : Scalar
  volume : Nat
  optionOpenInterest : Nat
  shortInterest : Nat
  fundFlow : Scalar
  deriving Repr

structure HiddenMarketState where
  netPosition : Scalar
  leverage : Nat
  constraintSlack : Nat
  higherOrderBelief : Scalar
  regimeId : Nat
  deriving Repr

structure StateEstimate where
  state : HiddenMarketState
  confidenceBps : Nat
  deriving Repr

def StateEstimate.Valid (estimate : StateEstimate) : Prop :=
  estimate.confidenceBps ≤ 10000

end LeanFinance.Inference
