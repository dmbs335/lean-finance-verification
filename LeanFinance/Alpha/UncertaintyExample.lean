import LeanFinance.Alpha.Uncertainty

namespace LeanFinance.Alpha.UncertaintyExample

open LeanFinance.Alpha

def envelope : ModelAlphaEnvelope :=
  { lowerBound := 150
    upperBound := 600
    ordered := by decide }

def costs : DeploymentCostRange :=
  { minimumCost := 50
    maximumCost := 120
    ordered := by decide }

theorem no_evidence_lower_bound :
    certifiableDeployableLower envelope 650 costs = (-620 : Int) := by
  decide

theorem complete_attack_evidence_lower_bound :
    certifiableDeployableLower envelope 0 costs = 30 := by
  decide

theorem remaining_upper_bound :
    certifiableDeployableUpper envelope costs = 550 := by
  decide

/-- Even after every declared upward distortion is removed, model and cost
    uncertainty leave a nondegenerate 520 bps interval. -/
theorem attack_identification_does_not_make_alpha_exact :
    certifiableDeployableLower envelope 0 costs ≠
      certifiableDeployableUpper envelope costs := by
  decide

end LeanFinance.Alpha.UncertaintyExample
