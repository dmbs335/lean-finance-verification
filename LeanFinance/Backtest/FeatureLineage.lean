import LeanFinance.Types

namespace LeanFinance.Backtest

structure FeatureLineage where
  featureName : String
  inputDatasetHashes : List String
  generatedAt : Time
  codeHash : String
  deriving DecidableEq, Repr

def FeatureLineage.ValidAt
    (lineage : FeatureLineage)
    (decisionTime : Time) : Prop :=
  lineage.generatedAt <= decisionTime ∧
  lineage.featureName ≠ "" ∧
  lineage.codeHash ≠ "" ∧
  lineage.inputDatasetHashes ≠ []

end LeanFinance.Backtest
