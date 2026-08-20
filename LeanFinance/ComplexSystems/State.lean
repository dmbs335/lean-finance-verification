import LeanFinance.Core

namespace LeanFinance.ComplexSystems

/-- Medium-horizon price-trend state used by the allocation policy. -/
inductive TrendState where
  | strong
  | mixed
  | weak
  deriving Repr, DecidableEq

/-- Endogenous market fragility inferred from liquidity, leverage, correlation,
    positioning concentration, and threshold density. -/
inductive FragilityState where
  | low
  | elevated
  | high
  deriving Repr, DecidableEq

/-- A coarse volatility state used only as a risk cap, not as a return forecast. -/
inductive VolatilityState where
  | normal
  | stressed
  deriving Repr, DecidableEq

/-- The policy consumes a finite, externally estimated market state. Lean checks
    decisions conditional on this state; it does not certify the estimator. -/
structure MarketState where
  trend : TrendState
  fragility : FragilityState
  volatility : VolatilityState
  deriving Repr, DecidableEq

/-- A particularly defensive state: weak trend and high endogenous fragility. -/
def DefensiveState (state : MarketState) : Prop :=
  state.trend = .weak ∧ state.fragility = .high

instance instDecidableDefensiveState
    (state : MarketState) : Decidable (DefensiveState state) := by
  unfold DefensiveState
  infer_instance

end LeanFinance.ComplexSystems
