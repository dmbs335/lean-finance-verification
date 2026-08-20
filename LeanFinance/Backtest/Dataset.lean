import LeanFinance.Types

namespace LeanFinance.Backtest

structure Dataset where
  id : String
  snapshotAt : Time
  availableAt : Time
  contentHash : String
  deriving DecidableEq, Repr

def Dataset.AvailableBy (dataset : Dataset) (decisionTime : Time) : Prop :=
  dataset.availableAt <= decisionTime

def Dataset.WellFormed (dataset : Dataset) : Prop :=
  dataset.snapshotAt <= dataset.availableAt ∧
  dataset.id ≠ "" ∧
  dataset.contentHash ≠ ""

end LeanFinance.Backtest
