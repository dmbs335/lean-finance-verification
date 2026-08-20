import LeanFinance.Backtest.Certificate
import LeanFinance.Backtest.Decision
import LeanFinance.Backtest.FeatureLineage
import LeanFinance.Backtest.Reproducibility
import LeanFinance.Backtest.SearchLedger
import LeanFinance.Certificate.StrategyCertificate
import LeanFinance.Certificate.DataCertificate

namespace LeanFinance.Certificate

/-- A proof-carrying backtest binds an empirical result to exact code, data,
    feature lineage, experiment environment, and the recorded search path. -/
structure BacktestCertificate where
  strategy : StrategyCertificate
  data : DataCertificate
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
