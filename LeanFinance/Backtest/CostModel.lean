import LeanFinance.Types

namespace LeanFinance.Backtest

/-- Identifies the exact transaction-cost implementation used by a backtest. -/
structure CostModel where
  modelId : String
  versionHash : String
  lockedAt : Time
  deriving DecidableEq, Repr

def CostModel.ValidAt (model : CostModel) (decisionTime : Time) : Prop :=
  model.lockedAt <= decisionTime ∧
  model.modelId ≠ "" ∧
  model.versionHash ≠ ""

theorem CostModel.lockedBeforeDecision
    {model : CostModel}
    {decisionTime : Time}
    (valid : model.ValidAt decisionTime) :
    model.lockedAt <= decisionTime :=
  valid.1

end LeanFinance.Backtest
