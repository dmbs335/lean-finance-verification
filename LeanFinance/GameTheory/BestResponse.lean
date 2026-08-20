import LeanFinance.GameTheory.Payoff

namespace LeanFinance.GameTheory

/-- No unilateral action yields strictly greater utility. -/
def IsBestResponse
    (payoff : Payoff)
    (player : Player)
    (profile : StrategyProfile) : Prop :=
  ∀ alternative,
    payoff.utility player profile >=
      payoff.deviationUtility player profile alternative

end LeanFinance.GameTheory
