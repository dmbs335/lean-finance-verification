import LeanFinance.Core

namespace LeanFinance.Backtest

structure ExperimentManifest where
  name : String
  codeHash : ContentHash
  dataHashes : List ContentHash
  parameterHash : ContentHash
  environmentHash : ContentHash
  deriving Repr

def Reproducible (manifest : ExperimentManifest) : Prop :=
  NonEmptyString manifest.codeHash ∧
    manifest.dataHashes ≠ [] ∧
    NonEmptyString manifest.parameterHash ∧
    NonEmptyString manifest.environmentHash

end LeanFinance.Backtest
