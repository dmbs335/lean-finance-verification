import LeanFinance.Market.RegimeTransition

namespace LeanFinance.Market

/-- A simple sufficient condition for a state to satisfy the declared
    instability boundary. This is structural, not an empirical prediction. -/
theorem high_leverage_crowding_low_liquidity_implies_instability
    (state : MarketState)
    (leverageHigh : state.leverage > 0)
    (crowdingHigh : state.crowding > 0)
    (liquidityLow : state.liquidity < 0) :
    NearInstability state :=
  ⟨leverageHigh, crowdingHigh, liquidityLow⟩

/-- The abstract classifier labels every state inside the declared boundary as
    stressed. -/
theorem near_instability_classifies_stressed
    (state : MarketState)
    (near : NearInstability state) :
    classifyRegime state = .stressed := by
  simp [classifyRegime, near]

/-- Mechanism refinement contract: any concrete mechanism that produces a
    transition can be checked against the common market transition layer. -/
theorem mechanism_transition_is_market_transition
    (mechanism : MarketMechanism)
    (transition : MarketTransition)
    (explains : mechanism.transition transition) :
    MechanismExplainsTransition mechanism transition :=
  explains

end LeanFinance.Market
