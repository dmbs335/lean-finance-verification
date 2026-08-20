import LeanFinance.Core
import LeanFinance.GameTheory.Player
import LeanFinance.GameTheory.Action
import LeanFinance.GameTheory.Belief

namespace LeanFinance.GameTheory

structure BayesianGame where
  players : List Player
  actions : List Action
  beliefs : List Belief
  payoff : Player → Belief → Action → Scalar
  feasible : Player → Action → Prop

structure StrategyProfile where
  actionOf : PlayerId → Action

end LeanFinance.GameTheory
