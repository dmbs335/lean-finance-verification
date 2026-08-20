import LeanFinance.GameTheory.Player
import LeanFinance.GameTheory.Action

namespace LeanFinance.GameTheory

structure Payoff where
  utility : Player → Action → Rat

end LeanFinance.GameTheory
