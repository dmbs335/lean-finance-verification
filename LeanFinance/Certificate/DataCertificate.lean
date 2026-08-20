import LeanFinance.Backtest.Dataset

namespace LeanFinance.Certificate

/-- Carries proofs that every referenced dataset was available by the decision
    time, content-addressed, and internally well-formed. -/
structure DataCertificate where
  decisionTime : Time
  datasets : List Backtest.Dataset
  available :
    ∀ dataset, dataset ∈ datasets →
      dataset.availableAt <= decisionTime
  hashed :
    ∀ dataset, dataset ∈ datasets →
      dataset.contentHash ≠ ""
  wellFormed :
    ∀ dataset, dataset ∈ datasets →
      dataset.WellFormed

def DataCertificate.ContainsHash
    (certificate : DataCertificate)
    (contentHash : String) : Prop :=
  ∃ dataset,
    dataset ∈ certificate.datasets ∧
    dataset.contentHash = contentHash

theorem DataCertificate.containsHash_of_member
    (certificate : DataCertificate)
    (dataset : Backtest.Dataset)
    (member : dataset ∈ certificate.datasets) :
    certificate.ContainsHash dataset.contentHash :=
  ⟨dataset, member, rfl⟩

end LeanFinance.Certificate
