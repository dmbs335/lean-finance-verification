import LeanFinance.Core
import LeanFinance.GameTheory.Action

namespace LeanFinance.GameTheory

def IsBestResponse
    (feasible : Action → Prop)
    (payoff : Action → Scalar)
    (chosen : Action) : Prop :=
  feasible chosen ∧
    ∀ alternative, feasible alternative → payoff alternative ≤ payoff chosen

theorem best_response_is_feasible
    (feasible : Action → Prop)
    (payoff : Action → Scalar)
    (chosen : Action)
    (h : IsBestResponse feasible payoff chosen) : feasible chosen :=
  h.1

end LeanFinance.GameTheory
