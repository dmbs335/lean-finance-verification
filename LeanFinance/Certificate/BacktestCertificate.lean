import LeanFinance.Backtest.Certificate
import LeanFinance.Backtest.CostModel
import LeanFinance.Backtest.Decision
import LeanFinance.Backtest.FeatureLineage
import LeanFinance.Backtest.Reproducibility
import LeanFinance.Backtest.SearchLedger
import LeanFinance.Certificate.StrategyCertificate
import LeanFinance.Certificate.DataCertificate
import LeanFinance.Certificate.UniverseCertificate
import LeanFinance.ResearchIntegrity.Commitment

namespace LeanFinance.Certificate

/-- A proof-carrying backtest binds an empirical result to exact code, data,
    point-in-time universe, feature lineage, costs, commitment, environment,
    and the recorded search path. -/
structure BacktestCertificate where
  strategy : StrategyCertificate
  data : DataCertificate
  universe : UniverseCertificate
  costModel : Backtest.CostModel
  commitment : ResearchIntegrity.ResearchCommitment
  features : List Backtest.FeatureLineage
  searchLedger : Backtest.SearchLedger
  experiment : Backtest.Experiment
  claim : Backtest.BacktestClaim
  reproducible : Backtest.Reproducible experiment
  searchRecorded :
    Backtest.RecordsParameterHash searchLedger strategy.parameterHash
  featuresValid :
    ∀ feature, feature ∈ features →
      feature.ValidAt data.decisionTime
  featureInputsBound :
    ∀ feature, feature ∈ features →
      ∀ inputHash, inputHash ∈ feature.inputDatasetHashes →
        data.ContainsHash inputHash
  universeAligned : universe.snapshot.asOf = data.decisionTime
  costModelValid : costModel.ValidAt data.decisionTime
  commitmentMatches :
    commitment.Matches
      strategy.strategyId
      strategy.codeHash
      strategy.parameterHash
  commitmentValid : commitment.ValidAt data.decisionTime
  claimWellFormed : claim.WellFormed
  resultAfterDecision : data.decisionTime <= claim.result.generatedAt

def BacktestCertificate.toDecision
    (certificate : BacktestCertificate) : Backtest.Decision :=
  {
    strategyId := certificate.strategy.strategyId
    decisionTime := certificate.data.decisionTime
    datasets := certificate.data.datasets
  }

end LeanFinance.Certificate
