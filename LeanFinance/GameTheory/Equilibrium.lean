import LeanFinance.GameTheory.BayesianGame
import LeanFinance.GameTheory.BestResponse

namespace LeanFinance.GameTheory

def IsBayesNashEquilibrium
    (game : BayesianGame)
    (profile : StrategyProfile) : Prop :=
  ∀ player, player ∈ game.players →
    ∃ belief,
      belief ∈ game.beliefs ∧
      belief.playerId = player.id ∧
      IsBestResponse
        (game.feasible player)
        (game.payoff player belief)
        (profile.actionOf player.id)

theorem equilibrium_actions_are_feasible
    (game : BayesianGame)
    (profile : StrategyProfile)
    (hEq : IsBayesNashEquilibrium game profile)
    (player : Player)
    (hPlayer : player ∈ game.players) :
    game.feasible player (profile.actionOf player.id) := by
  cases hEq player hPlayer with
  | intro _belief hBelief =>
      exact hBelief.2.2.1

end LeanFinance.GameTheory
