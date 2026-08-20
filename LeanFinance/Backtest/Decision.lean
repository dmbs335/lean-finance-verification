import LeanFinance.Backtest.Dataset

namespace LeanFinance.Backtest

structure Decision where
  strategyId : String
  decisionTime : Time
  datasets : List Dataset
  deriving Repr

def UsesDataBeforeDecision (decision : Decision) : Prop :=
  ∀ dataset, dataset ∈ decision.datasets →
    dataset.AvailableBy decision.decisionTime

end LeanFinance.Backtest
