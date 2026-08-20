import LeanFinance.Core

namespace LeanFinance.Backtest

structure FeatureLineage where
  featureName : String
  inputHashes : List ContentHash
  generatedAt : Timestamp
  codeHash : ContentHash
  deriving Repr

def FeatureAvailableAt
    (lineage : FeatureLineage)
    (decisionTime : Timestamp) : Prop :=
  lineage.generatedAt ≤ decisionTime

def FeatureBoundToInputs (lineage : FeatureLineage) : Prop :=
  lineage.inputHashes ≠ [] ∧ NonEmptyString lineage.codeHash

end LeanFinance.Backtest
