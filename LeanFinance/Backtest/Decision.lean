import LeanFinance.Core
import LeanFinance.Backtest.Dataset
import LeanFinance.Backtest.FeatureLineage

namespace LeanFinance.Backtest

structure Decision where
  strategyId : StrategyId
  decisionTime : Timestamp
  datasets : List Dataset
  features : List FeatureLineage
  parameterHash : ContentHash
  deriving Repr

def UsesDataBeforeDecision (decision : Decision) : Prop :=
  ∀ dataset,
    dataset ∈ decision.datasets →
    DatasetAvailableAt dataset decision.decisionTime

def UsesFeaturesBeforeDecision (decision : Decision) : Prop :=
  ∀ feature,
    feature ∈ decision.features →
    FeatureAvailableAt feature decision.decisionTime

end LeanFinance.Backtest
