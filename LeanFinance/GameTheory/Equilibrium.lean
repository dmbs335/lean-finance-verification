import LeanFinance.GameTheory.BestResponse

namespace LeanFinance.GameTheory

def NashEquilibrium
    (payoff : Payoff)
    (players : List Player)
    (profile : StrategyProfile) : Prop :=
  ∀ player, player ∈ players → IsBestResponse payoff player profile

theorem NashEquilibrium.noProfitableDeviation
    {payoff : Payoff}
    {players : List Player}
    {profile : StrategyProfile}
    (equilibrium : NashEquilibrium payoff players profile)
    {player : Player}
    (member : player ∈ players)
    (alternative : Action) :
    payoff.utility player profile >=
      payoff.deviationUtility player profile alternative :=
  equilibrium player member alternative

end LeanFinance.GameTheory
