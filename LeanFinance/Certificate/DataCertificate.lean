import LeanFinance.Backtest.Dataset

namespace LeanFinance.Certificate

/-- Carries proofs that every referenced dataset was available by the decision
    time and is content-addressed. -/
structure DataCertificate where
  decisionTime : Time
  datasets : List Backtest.Dataset
  available :
    ∀ dataset, dataset ∈ datasets →
      dataset.availableAt <= decisionTime
  hashed :
    ∀ dataset, dataset ∈ datasets →
      dataset.contentHash ≠ ""

end LeanFinance.Certificate
