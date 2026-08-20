namespace LeanFinance

structure MarketState where
  price : Rat
  volatility : Rat
  liquidity : Rat

structure Transition where
  next : MarketState → MarketState

 def evolves (t : Transition) (s : MarketState) : MarketState :=
  t.next s

end LeanFinance
