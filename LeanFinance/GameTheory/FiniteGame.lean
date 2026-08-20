import LeanFinance.GameTheory.Equilibrium

namespace LeanFinance.GameTheory

/-- A finite action restriction around the general payoff/profile model. This
    is the interface expected from an external equilibrium-search procedure. -/
structure FiniteGame where
  players : List Player
  actions : PlayerId → List Action
  payoff : Payoff

/-- Every selected action belongs to the player's declared finite action set. -/
def ProfileAdmissible
    (game : FiniteGame)
    (profile : StrategyProfile) : Prop :=
  ∀ player, player ∈ game.players →
    profile player.id ∈ game.actions player.id

/-- No admissible unilateral deviation improves payoff. -/
def FiniteIsBestResponse
    (game : FiniteGame)
    (player : Player)
    (profile : StrategyProfile) : Prop :=
  ∀ alternative,
    alternative ∈ game.actions player.id →
      game.payoff.utility player profile >=
        game.payoff.deviationUtility player profile alternative

def FiniteNashEquilibrium
    (game : FiniteGame)
    (profile : StrategyProfile) : Prop :=
  ProfileAdmissible game profile ∧
  ∀ player, player ∈ game.players →
    FiniteIsBestResponse game player profile

theorem FiniteNashEquilibrium.profileAdmissible
    {game : FiniteGame}
    {profile : StrategyProfile}
    (equilibrium : FiniteNashEquilibrium game profile) :
    ProfileAdmissible game profile :=
  equilibrium.1

theorem FiniteNashEquilibrium.noProfitableDeviation
    {game : FiniteGame}
    {profile : StrategyProfile}
    (equilibrium : FiniteNashEquilibrium game profile)
    {player : Player}
    (playerMember : player ∈ game.players)
    {alternative : Action}
    (alternativeMember : alternative ∈ game.actions player.id) :
    game.payoff.utility player profile >=
      game.payoff.deviationUtility player profile alternative :=
  equilibrium.2 player playerMember alternative alternativeMember

end LeanFinance.GameTheory
