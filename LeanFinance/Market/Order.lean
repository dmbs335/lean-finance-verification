import LeanFinance.GameTheory.Player

namespace LeanFinance.Market

inductive OrderSide
  | buy
  | sell
  deriving DecidableEq, Repr

structure Order where
  traderId : GameTheory.PlayerId
  quantity : Scalar
  limitPrice : Scalar
  side : OrderSide
  deriving Repr

def Order.WellFormed (order : Order) : Prop :=
  0 < order.quantity ∧ 0 <= order.limitPrice

def Order.signedQuantity (order : Order) : Scalar :=
  match order.side with
  | .buy => order.quantity
  | .sell => -order.quantity

end LeanFinance.Market
