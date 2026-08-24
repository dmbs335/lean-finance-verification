import LeanFinance.Alpha.FakeAlpha

namespace LeanFinance.Examples.FakeAlphaBenchmark

open LeanFinance.Alpha

def futureInformationCase : AlphaDecomposition :=
  { economicAlpha := 40
    attackBias := 60
    modelBias := 5
    samplingNoise := -2 }

def futureInformationFinding : AttackFinding :=
  { attack := .futureInformation
    estimatedBias := 60
    detected := true }

theorem observed_alpha_is_inflated :
    futureInformationCase.observedAlpha = 103 := by
  decide

theorem evidence_removes_the_attack_bias :
    identifiedBias [futureInformationFinding] = 60 := by
  decide

theorem cleaned_alpha_still_contains_residual_error :
    cleanedAlpha futureInformationCase.observedAlpha
      [futureInformationFinding] = 43 := by
  decide

theorem cleaned_alpha_is_not_yet_economic_alpha :
    cleanedAlpha futureInformationCase.observedAlpha
      [futureInformationFinding] ≠
        futureInformationCase.economicAlpha := by
  decide

def certifiedInterval : CertifiableAlphaInterval :=
  { lower := 35
    upper := 50
    integrityVerified := true
    ordered := by decide }

theorem economic_alpha_is_inside_certified_interval :
    certifiedInterval.Contains futureInformationCase.economicAlpha := by
  decide

end LeanFinance.Examples.FakeAlphaBenchmark
