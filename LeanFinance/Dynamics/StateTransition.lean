import LeanFinance.Core

namespace LeanFinance.Dynamics

structure MarketState where
  price : Scalar
  volatilityBps : Nat
  liquidityDepth : Nat
  dealerCapital : Nat
  deriving Repr

structure MarketShock where
  fundamentalMove : Scalar
  orderFlowMove : Scalar
  volatilityIncrease : Nat
  liquidityDrain : Nat
  capitalLoss : Nat
  deriving Repr

def transition
    (state : MarketState)
    (shock : MarketShock) : MarketState :=
  { price := state.price + shock.fundamentalMove + shock.orderFlowMove
    volatilityBps := state.volatilityBps + shock.volatilityIncrease
    liquidityDepth := state.liquidityDepth - shock.liquidityDrain
    dealerCapital := state.dealerCapital - shock.capitalLoss }

theorem transition_price_identity
    (state : MarketState)
    (shock : MarketShock) :
    (transition state shock).price =
      state.price + shock.fundamentalMove + shock.orderFlowMove :=
  rfl

end LeanFinance.Dynamics
