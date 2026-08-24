import LeanFinance.Statistics.OffPolicy
import LeanFinance.Statistics.ConfidenceSequence
import LeanFinance.Control.Authority

namespace LeanFinance.Statistics

/-- Complete arithmetic gate for one baseline-relative authority promotion. -/
structure OffPolicyPromotionCertificate where
  improvement : ConfidenceSequenceCertificate
  requiredImprovementBps : Int
  effectiveSampleSize : EffectiveSampleSizeCertificate
  riskUcb : Nat
  riskBudget : Nat
  modelShift : Bool
  operationalBreach : Bool
  lowerClearsMargin :
    requiredImprovementBps ≤ improvement.lowerBps
  riskWithinBudget : riskUcb ≤ riskBudget
  noModelShift : modelShift = false
  noOperationalBreach : operationalBreach = false
  deriving Repr

namespace OffPolicyPromotionCertificate

def toAuthorityEvidence
    (certificate : OffPolicyPromotionCertificate) :
    LeanFinance.Control.PromotionEvidence :=
  { improvementLcb := certificate.improvement.lowerBps
    effectiveSampleSize := certificate.effectiveSampleSize.sumWeights *
      certificate.effectiveSampleSize.sumWeights
    minimumEffectiveSampleSize :=
      certificate.effectiveSampleSize.minimumESS *
        certificate.effectiveSampleSize.sumSquaredWeights
    riskUcb := certificate.riskUcb
    riskBudget := certificate.riskBudget
    modelShift := certificate.modelShift
    operationalBreach := certificate.operationalBreach }

/-- A registered promotion certificate has a lower bound clearing its margin and
    a risk upper bound inside budget. -/
theorem registered_promotion_clears_bounds
    (certificate : OffPolicyPromotionCertificate) :
    certificate.requiredImprovementBps ≤
        certificate.improvement.lowerBps ∧
      certificate.riskUcb ≤ certificate.riskBudget :=
  ⟨certificate.lowerClearsMargin, certificate.riskWithinBudget⟩

end OffPolicyPromotionCertificate

end LeanFinance.Statistics
