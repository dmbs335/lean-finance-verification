import LeanFinance.Dynamics.StateTransition

namespace LeanFinance.Dynamics

inductive Regime
  | normal
  | crowded
  | stressed
  | crisis
  deriving DecidableEq, Repr

structure EquilibriumState where
  market : MarketState
  regime : Regime
  activeConstraints : List String
  deriving Repr

end LeanFinance.Dynamics
