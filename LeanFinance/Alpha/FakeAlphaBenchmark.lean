namespace LeanFinance.Alpha

/-- Classes of research-process distortions that can inflate apparent alpha. -/
inductive AlphaDistortion where
  | futureInformation
  | survivorshipBias
  | parameterMining
  | costMutation
  | benchmarkSwitching
  deriving Repr, DecidableEq

/-- A benchmark separates observed performance from admissible clean alpha. -/
structure AlphaExperiment where
  observedAlpha : Int
  cleanAlpha : Int
  distortions : List AlphaDistortion
  deriving Repr

/-- Removing declared distortions cannot increase the distortion-free gap. -/
def AlphaExperiment.Valid (experiment : AlphaExperiment) : Prop :=
  experiment.cleanAlpha ≤ experiment.observedAlpha

 theorem clean_alpha_is_bounded
    (experiment : AlphaExperiment)
    (valid : experiment.Valid) :
    experiment.cleanAlpha ≤ experiment.observedAlpha :=
  valid

end LeanFinance.Alpha
