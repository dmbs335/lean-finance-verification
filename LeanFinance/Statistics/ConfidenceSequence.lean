namespace LeanFinance.Statistics

/-- Arithmetic envelope emitted by an external anytime-valid estimator. Lean
    checks interval ordering and promotion use; statistical coverage remains
    conditional on the registered estimator assumptions. -/
structure ConfidenceSequenceCertificate where
  lowerBps : Int
  estimateBps : Int
  upperBps : Int
  sampleCount : Nat
  lowerBounded : lowerBps ≤ estimateBps
  upperBounded : estimateBps ≤ upperBps
  deriving Repr

namespace ConfidenceSequenceCertificate

def Contains
    (certificate : ConfidenceSequenceCertificate)
    (value : Int) : Prop :=
  certificate.lowerBps ≤ value ∧ value ≤ certificate.upperBps

theorem estimate_is_contained
    (certificate : ConfidenceSequenceCertificate) :
    certificate.Contains certificate.estimateBps :=
  ⟨certificate.lowerBounded, certificate.upperBounded⟩

end ConfidenceSequenceCertificate

end LeanFinance.Statistics
