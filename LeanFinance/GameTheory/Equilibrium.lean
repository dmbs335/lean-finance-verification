import LeanFinance.GameTheory.Player
import LeanFinance.GameTheory.Action
import LeanFinance.GameTheory.Payoff

namespace LeanFinance.GameTheory

structure BestResponse where
  action : Action


def NashEquilibrium (p : Payoff) (players : List Player) : Prop :=
  True

end LeanFinance.GameTheory
