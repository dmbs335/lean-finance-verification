namespace LeanFinance.GameTheory

structure Player where
  id : Nat
  riskAversion : Rat
  leverageLimit : Rat
  horizon : Nat

structure MarketState where
  price : Rat
  volatility : Rat
  liquidity : Rat

structure Constraint where
  active : Bool
  shadowPrice : Rat

end LeanFinance.GameTheory
