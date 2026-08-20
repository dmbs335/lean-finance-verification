import LeanFinance.Market.Liquidity

namespace LeanFinance.Dynamics

structure MarketState where
  price : Scalar
  volatility : Scalar
  liquidity : Market.LiquidityState
  deriving Repr

structure Transition where
  next : MarketState → MarketState

def evolves (transition : Transition) (state : MarketState) : MarketState :=
  transition.next state

def identityTransition : Transition :=
  { next := fun state => state }

theorem identityTransition_fixed (state : MarketState) :
    evolves identityTransition state = state :=
  rfl

end LeanFinance.Dynamics
