import LeanFinance.Market.CrowdingCascade

namespace LeanFinance.Market

/-- A simplified cascade state describing feedback between shocks and market
    fragility. -/
structure CascadeState where
  shockExposure : Scalar
  liquidityStress : Scalar
  forcedSellingPressure : Scalar
  deriving Repr

/-- Positive feedback-loop condition for cascade amplification. -/
def CascadeAmplification
    (state : CascadeState) : Prop :=
  state.shockExposure > 0 ∧
    state.liquidityStress > 0 ∧
    state.forcedSellingPressure > 0

/-- A cascade transition represents propagation of a local shock into a broader
    market-state change. -/
structure CascadeTransition where
  source : CascadeState
  destination : CascadeState
  deriving Repr

/-- An amplified source cascade contains a positive forced-selling propagation
    channel. -/
theorem cascade_preserves_feedback_channel
    (transition : CascadeTransition)
    (sourceAmplified : CascadeAmplification transition.source) :
    transition.source.forcedSellingPressure > 0 :=
  sourceAmplified.2.2

/-- Crowding can be refined into a cascade model by mapping crowding pressure to
    shock exposure and liquidity feedback. -/
structure CrowdingCascadeLink where
  pressure : CrowdingPressure
  cascade : CascadeState
  pressureToShock :
    pressure.imitation > 0 → cascade.shockExposure > 0

end LeanFinance.Market
