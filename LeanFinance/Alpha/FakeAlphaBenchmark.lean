import LeanFinance.Alpha.Certifiable

namespace LeanFinance.Alpha

/-- Declared classes of research-process distortion that can inflate apparent
    alpha without improving the underlying economic strategy. -/
inductive AlphaDistortion where
  | futureInformation
  | survivorshipBias
  | parameterMining
  | costMutation
  | benchmarkSwitching
  deriving Repr, DecidableEq

/-- One bounded contribution to observed alpha. Values are integer basis points
    in the executable research model. -/
structure DistortionAmount where
  kind : AlphaDistortion
  inflationBps : Nat
  deriving Repr

def totalInflation (distortions : List DistortionAmount) : Nat :=
  distortions.foldl (fun total distortion =>
    total + distortion.inflationBps) 0

/-- The benchmark keeps the distortion-free alpha separate from the observed
    alpha generated after declared integrity failures. -/
structure AlphaExperiment where
  experimentId : String
  cleanAlpha : RealizedAlpha
  distortions : List DistortionAmount
  deriving Repr

def observedAlpha (experiment : AlphaExperiment) : RealizedAlpha :=
  experiment.cleanAlpha + Int.ofNat (totalInflation experiment.distortions)

/-- Correct the observed alpha by the amount of inflation established by the
    selected evidence architecture. Undetected distortions remain in the upper
    endpoint. -/
def correctedAlpha
    (experiment : AlphaExperiment)
    (detectedInflation : Nat) : RealizedAlpha :=
  observedAlpha experiment - Int.ofNat detectedInflation

/-- A benchmark interval is grounded by the controlled clean alpha and bounded
    above by the alpha remaining after detected distortions are removed. -/
def benchmarkInterval
    (experiment : AlphaExperiment)
    (detectedInflation : Nat)
    (state : EvidenceState) : CertifiableAlpha :=
  { lowerBound := experiment.cleanAlpha
    upperBound := correctedAlpha experiment detectedInflation
    state := state }

/-- Detecting the complete declared distortion amount recovers the clean alpha. -/
theorem full_remediation_recovers_clean_alpha
    (experiment : AlphaExperiment)
    (detectedInflation : Nat)
    (complete : detectedInflation = totalInflation experiment.distortions) :
    correctedAlpha experiment detectedInflation = experiment.cleanAlpha := by
  simp [correctedAlpha, observedAlpha, complete]

/-- Under complete remediation the controlled certifiable interval collapses to
    the clean alpha point. -/
theorem full_remediation_collapses_interval
    (experiment : AlphaExperiment)
    (state : EvidenceState) :
    (benchmarkInterval experiment
      (totalInflation experiment.distortions) state).lowerBound =
      (benchmarkInterval experiment
        (totalInflation experiment.distortions) state).upperBound := by
  simp [benchmarkInterval, full_remediation_recovers_clean_alpha]

end LeanFinance.Alpha
