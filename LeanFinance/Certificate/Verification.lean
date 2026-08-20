import LeanFinance.Backtest.NoFutureInformation
import LeanFinance.Certificate.BacktestCertificate

namespace LeanFinance.Certificate

/-- The machine-checkable claim exported by a proof-carrying backtest. -/
structure VerifiedResearchClaim (certificate : BacktestCertificate) : Prop where
  noFutureInformation :
    Backtest.NoFutureInformation certificate.toDecision
  dataWellFormed :
    ∀ dataset, dataset ∈ certificate.data.datasets →
      dataset.WellFormed
  reproducible : Backtest.Reproducible certificate.experiment
  searchRecorded :
    Backtest.RecordsParameterHash
      certificate.searchLedger
      certificate.strategy.parameterHash
  featuresValid :
    ∀ feature, feature ∈ certificate.features →
      feature.ValidAt certificate.data.decisionTime
  featureInputsBound :
    ∀ feature, feature ∈ certificate.features →
      ∀ inputHash, inputHash ∈ feature.inputDatasetHashes →
        certificate.data.ContainsHash inputHash
  claimWellFormed : certificate.claim.WellFormed
  resultAfterDecision :
    certificate.data.decisionTime <= certificate.claim.result.generatedAt

theorem BacktestCertificate.noFutureInformation
    (certificate : BacktestCertificate) :
    Backtest.NoFutureInformation certificate.toDecision := by
  intro dataset member
  exact certificate.data.available dataset member

theorem certificate_sound
    (certificate : BacktestCertificate) :
    VerifiedResearchClaim certificate :=
  {
    noFutureInformation := certificate.noFutureInformation
    dataWellFormed := certificate.data.wellFormed
    reproducible := certificate.reproducible
    searchRecorded := certificate.searchRecorded
    featuresValid := certificate.featuresValid
    featureInputsBound := certificate.featureInputsBound
    claimWellFormed := certificate.claimWellFormed
    resultAfterDecision := certificate.resultAfterDecision
  }

theorem verifiedClaim_implies_noFutureInformation
    {certificate : BacktestCertificate}
    (verified : VerifiedResearchClaim certificate) :
    Backtest.NoFutureInformation certificate.toDecision :=
  verified.noFutureInformation

theorem verifiedClaim_datasetAvailable
    {certificate : BacktestCertificate}
    (verified : VerifiedResearchClaim certificate)
    (dataset : Backtest.Dataset)
    (member : dataset ∈ certificate.data.datasets) :
    dataset.availableAt <= certificate.data.decisionTime :=
  verified.noFutureInformation dataset member

theorem verifiedClaim_featureInputBound
    {certificate : BacktestCertificate}
    (verified : VerifiedResearchClaim certificate)
    (feature : Backtest.FeatureLineage)
    (featureMember : feature ∈ certificate.features)
    (inputHash : String)
    (inputMember : inputHash ∈ feature.inputDatasetHashes) :
    certificate.data.ContainsHash inputHash :=
  verified.featureInputsBound feature featureMember inputHash inputMember

end LeanFinance.Certificate
