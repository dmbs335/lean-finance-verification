import LeanFinance.Core

namespace LeanFinance.Market

/-- Latent market state combining interacting economic dimensions.

This is intentionally not a price predictor. It represents hidden state
variables whose evolution can produce observable market regimes. -/
structure MarketState where
  valuation : Scalar
  liquidity : Scalar
  leverage : Scalar
  volatility : Scalar
  crowding : Scalar
  positioning : Scalar
  informationFlow : Scalar
  deriving Repr

/-- Observable market measurements are separated from latent state. -/
structure MarketObservation where
  priceReturn : Scalar
  volume : Scalar
  realizedVolatility : Scalar
  deriving Repr

/-- A transition relation captures regime evolution.

The dynamics are intentionally abstract so that later models can instantiate
agent interaction, network effects, or game-theoretic mechanisms. -/
structure MarketTransition where
  source : MarketState
  destination : MarketState
  shock : Scalar
  deriving Repr

/-- Structural instability boundary used by the regime layer. -/
def NearInstability (state : MarketState) : Prop :=
  state.leverage > 0 ∧
    state.crowding > 0 ∧
    state.liquidity < 0

/-- `NearInstability` is a concrete conjunction of decidable integer-order
    predicates. Declaring the instance explicitly keeps downstream classifiers
    computational without importing classical proposition decidability. -/
instance instDecidableNearInstability (state : MarketState) :
    Decidable (NearInstability state) := by
  unfold NearInstability
  infer_instance

/-- Strategy ecology, game interaction, and network models can refine this
    common market state representation. -/
structure MarketMechanism where
  transition : MarketTransition → Prop

end LeanFinance.Market
