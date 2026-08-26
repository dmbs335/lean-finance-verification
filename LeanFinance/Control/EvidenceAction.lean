namespace LeanFinance.Control

/-- Certificate for an evidence-acquisition action. `postQueryGuarantee` is a
    lower bound valid after every declared observation. -/
structure EvidenceActionCertificate (Observation : Type) where
  currentRobustValue : Int
  queryCost : Int
  postObservationValue : Observation → Int
  postQueryGuarantee : Int
  guarantee :
    ∀ observation,
      postQueryGuarantee ≤ postObservationValue observation
  deriving Repr

namespace EvidenceActionCertificate

def netPostQueryValue
    (certificate : EvidenceActionCertificate Observation) : Int :=
  certificate.postQueryGuarantee - certificate.queryCost

def ValueOfInformation
    (certificate : EvidenceActionCertificate Observation) : Prop :=
  certificate.currentRobustValue < certificate.netPostQueryValue

/-- A positive robust value-of-information certificate means the worst declared
    post-query value, net of evidence cost, exceeds immediate robust value. -/
theorem positive_value_of_information
    (certificate : EvidenceActionCertificate Observation)
    (positive : certificate.ValueOfInformation) :
    certificate.currentRobustValue <
      certificate.postQueryGuarantee - certificate.queryCost :=
  positive

end EvidenceActionCertificate

end LeanFinance.Control
