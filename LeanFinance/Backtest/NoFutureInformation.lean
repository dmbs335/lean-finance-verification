import LeanFinance.Backtest.Decision

namespace LeanFinance.Backtest

def NoFutureInformation (decision : Decision) : Prop :=
  UsesDataBeforeDecision decision

theorem noFutureInformation_sound
    (decision : Decision)
    (certificate : NoFutureInformation decision)
    (dataset : Dataset)
    (used : dataset ∈ decision.datasets) :
    dataset.availableAt <= decision.decisionTime :=
  certificate dataset used

end LeanFinance.Backtest
