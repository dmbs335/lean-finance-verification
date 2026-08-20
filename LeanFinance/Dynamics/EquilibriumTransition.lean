import LeanFinance.Dynamics.Regime

namespace LeanFinance.Dynamics

def EvolveEquilibrium
    (state : EquilibriumState)
    (shock : MarketShock)
    (nextRegime : Regime)
    (nextConstraints : List String) : EquilibriumState :=
  { market := transition state.market shock
    regime := nextRegime
    activeConstraints := nextConstraints }

def RegimeChanged
    (before after : EquilibriumState) : Prop :=
  before.regime ≠ after.regime

theorem equal_regime_is_not_a_regime_change
    (before after : EquilibriumState)
    (h : before.regime = after.regime) :
    ¬ RegimeChanged before after := by
  intro hChanged
  exact hChanged h

end LeanFinance.Dynamics
