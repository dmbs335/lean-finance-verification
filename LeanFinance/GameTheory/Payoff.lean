import LeanFinance.GameTheory.Player
import LeanFinance.GameTheory.Action

namespace LeanFinance.GameTheory

abbrev StrategyProfile := PlayerId → Action

def StrategyProfile.update
    (profile : StrategyProfile)
    (playerId : PlayerId)
    (action : Action) : StrategyProfile :=
  fun candidateId => if candidateId = playerId then action else profile candidateId

/-- Reduced-form utility. More specialized market modules may refine this into
    information, inventory, benchmark, funding, and constraint components. -/
structure Payoff where
  utility : Player → StrategyProfile → Scalar

def Payoff.deviationUtility
    (payoff : Payoff)
    (player : Player)
    (profile : StrategyProfile)
    (alternative : Action) : Scalar :=
  payoff.utility player (profile.update player.id alternative)

end LeanFinance.GameTheory
