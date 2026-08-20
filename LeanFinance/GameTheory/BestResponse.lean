namespace LeanFinance.GameTheory

import LeanFinance.GameTheory.Action
import LeanFinance.GameTheory.Payoff

/-- An action is a best response when no alternative action improves payoff. -/
def IsBestResponse
  (chosen : Action)
  (utility : Action → Rat) : Prop :=
  ∀ a, utility chosen >= utility a

end LeanFinance.GameTheory
