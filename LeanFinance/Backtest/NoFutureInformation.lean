import LeanFinance.Backtest.Decision


def NoFutureInformation (d : Decision) : Prop :=
  UsesDataBeforeDecision d

 theorem no_future_information_sound
    (d : Decision)
    (h : NoFutureInformation d) :
    d.dataset.timestamp <= d.decisionTime := by
  exact h
