import LeanFinance.Types

namespace LeanFinance.Market

structure LiquidityState where
  depth : Scalar
  spread : Scalar
  impact : Scalar
  deriving Repr

def LiquidityState.WellFormed (state : LiquidityState) : Prop :=
  0 <= state.depth ∧ 0 <= state.spread ∧ 0 <= state.impact

end LeanFinance.Market
