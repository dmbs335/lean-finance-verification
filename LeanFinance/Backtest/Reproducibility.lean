structure Experiment where
  name : String
  codeVersion : String
  dataVersion : String
  parameterVersion : String


def Reproducible (e : Experiment) : Prop :=
  e.codeVersion.length > 0 ∧
  e.dataVersion.length > 0 ∧
  e.parameterVersion.length > 0
