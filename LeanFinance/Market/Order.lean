import LeanFinance.Core
import LeanFinance.GameTheory.Action

namespace LeanFinance.Market

structure Order where
  trader : PlayerId
  action : GameTheory.Action
  limitPrice : Option Scalar
  submittedAt : Timestamp
  deriving Repr

def Order.signedQuantity (order : Order) : Scalar :=
  match order.action.side with
  | GameTheory.Side.buy => Int.ofNat order.action.quantity
  | GameTheory.Side.hold => 0
  | GameTheory.Side.sell => -Int.ofNat order.action.quantity

end LeanFinance.Market
