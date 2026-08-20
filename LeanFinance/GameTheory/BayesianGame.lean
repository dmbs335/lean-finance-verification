import LeanFinance.GameTheory.Belief
import LeanFinance.GameTheory.Payoff

namespace LeanFinance.GameTheory

/-- A concrete partially informed game. Beliefs remain player-specific and
    utilities may depend on the full strategy profile. -/
structure BayesianGame where
  players : List Player
  belief : PlayerId → Belief
  utility : Player → Belief → StrategyProfile → Scalar

def BayesianIsBestResponse
    (game : BayesianGame)
    (player : Player)
    (profile : StrategyProfile) : Prop :=
  ∀ alternative,
    game.utility player (game.belief player.id) profile >=
      game.utility player (game.belief player.id)
        (profile.update player.id alternative)

def BayesianEquilibrium
    (game : BayesianGame)
    (profile : StrategyProfile) : Prop :=
  ∀ player, player ∈ game.players →
    BayesianIsBestResponse game player profile ∧
    (game.belief player.id).WellFormed

end LeanFinance.GameTheory
