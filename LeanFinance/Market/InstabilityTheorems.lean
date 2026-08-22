import LeanFinance.Market.RegimeTransition

namespace LeanFinance.Market

/-- A stable-to-stressed transition requires the destination state to satisfy
    the declared instability boundary. This is structural, not predictive. -/
theorem stressed_transition_requires_instability
    (transition : MarketTransition)
    (enters : EntersStressRegime transition) :
    NearInstability transition.destination := by
  have destinationStressed :
      classifyRegime transition.destination = .stressed :=
    enters.2
  by_cases near : NearInstability transition.destination
  · exact near
  · simp [classifyRegime, near] at destinationStressed

/-- Mechanisms are intentionally separated from state semantics. A future
    game-theoretic or network model only needs to prove that it induces a
    `MarketTransition` satisfying the shared contract. -/
theorem mechanism_refines_state_transition
    (mechanism : MarketMechanism)
    (transition : MarketTransition)
    (explains : MechanismExplainsTransition mechanism transition) :
    mechanism.transition transition :=
  explains

end LeanFinance.Market
