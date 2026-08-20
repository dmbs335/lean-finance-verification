namespace LeanFinance.Backtest

structure Experiment where
  name : String
  codeVersion : String
  dataVersion : String
  parameterVersion : String
  environmentHash : String
  deriving DecidableEq, Repr

def Reproducible (experiment : Experiment) : Prop :=
  experiment.name ≠ "" ∧
  experiment.codeVersion ≠ "" ∧
  experiment.dataVersion ≠ "" ∧
  experiment.parameterVersion ≠ "" ∧
  experiment.environmentHash ≠ ""

theorem Reproducible.codeVersionPresent
    {experiment : Experiment}
    (reproducible : Reproducible experiment) :
    experiment.codeVersion ≠ "" :=
  reproducible.2.1

end LeanFinance.Backtest
