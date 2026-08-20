import LeanFinance.Core

namespace LeanFinance.Backtest

structure Dataset where
  id : String
  observedAt : Timestamp
  availableAt : Timestamp
  contentHash : ContentHash
  deriving Repr

def DatasetAvailableAt
    (dataset : Dataset)
    (decisionTime : Timestamp) : Prop :=
  dataset.availableAt ≤ decisionTime

def DatasetHashBound (dataset : Dataset) : Prop :=
  NonEmptyString dataset.contentHash

end LeanFinance.Backtest
