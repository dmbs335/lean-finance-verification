import LeanFinance.Backtest.Decision

namespace LeanFinance.Backtest

def NoFutureInformation (decision : Decision) : Prop :=
  UsesDataBeforeDecision decision ∧ UsesFeaturesBeforeDecision decision

theorem no_future_information_data
    (decision : Decision)
    (h : NoFutureInformation decision) :
    UsesDataBeforeDecision decision :=
  h.1

theorem no_future_information_features
    (decision : Decision)
    (h : NoFutureInformation decision) :
    UsesFeaturesBeforeDecision decision :=
  h.2

end LeanFinance.Backtest
