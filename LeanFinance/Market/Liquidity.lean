namespace LeanFinance.Market

structure LiquidityState where
  depth : Nat
  spreadBps : Nat
  priceImpactBps : Nat
  deriving Repr

def LiquidityState.Stressed (state : LiquidityState) : Prop :=
  state.depth = 0 ∨ state.spreadBps > 100

end LeanFinance.Market
