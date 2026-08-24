import LeanFinance.Alpha.Certifiable

namespace LeanFinance.Alpha

/-- Envelope across the declared statistical/risk models. The proof field makes
    malformed intervals unrepresentable in the formal layer. -/
structure ModelAlphaEnvelope where
  lowerBound : RealizedAlpha
  upperBound : RealizedAlpha
  ordered : lowerBound ≤ upperBound

/-- Deployment-cost uncertainty remaining after the research process. -/
structure DeploymentCostRange where
  minimumCost : Nat
  maximumCost : Nat
  ordered : minimumCost ≤ maximumCost

/-- Conservative lower endpoint when unresolved research distortions can only
    inflate observed alpha by at most `unresolvedInflation`. -/
def certifiableDeployableLower
    (envelope : ModelAlphaEnvelope)
    (unresolvedInflation : Nat)
    (costs : DeploymentCostRange) : RealizedAlpha :=
  envelope.lowerBound
    - Int.ofNat (unresolvedInflation + costs.maximumCost)

def certifiableDeployableUpper
    (envelope : ModelAlphaEnvelope)
    (costs : DeploymentCostRange) : RealizedAlpha :=
  envelope.upperBound - Int.ofNat costs.minimumCost

structure CertifiableDeploymentInterval where
  lowerBound : RealizedAlpha
  upperBound : RealizedAlpha
  unresolvedInflation : Nat

/-- Stronger evidence that lowers the maximum unresolved upward distortion
    weakly improves the certifiable deployable-alpha lower bound. -/
theorem less_unresolved_inflation_improves_lower_bound
    (envelope : ModelAlphaEnvelope)
    (costs : DeploymentCostRange)
    (stronger weaker : Nat)
    (lessUnresolved : stronger ≤ weaker) :
    certifiableDeployableLower envelope weaker costs ≤
      certifiableDeployableLower envelope stronger costs := by
  have withCost :
      stronger + costs.maximumCost ≤
        weaker + costs.maximumCost :=
    Nat.add_le_add_right lessUnresolved costs.maximumCost
  exact Int.sub_le_sub_left (Int.ofNat_le.2 withCost)
    envelope.lowerBound

/-- Eliminating research-process distortion does not by itself collapse model
    and deployment uncertainty. A point interval requires an additional equality
    premise on the remaining endpoints. -/
theorem exact_point_requires_endpoint_equality
    (envelope : ModelAlphaEnvelope)
    (costs : DeploymentCostRange)
    (equalEndpoints :
      certifiableDeployableLower envelope 0 costs =
        certifiableDeployableUpper envelope costs) :
    certifiableDeployableLower envelope 0 costs =
      certifiableDeployableUpper envelope costs :=
  equalEndpoints

end LeanFinance.Alpha
