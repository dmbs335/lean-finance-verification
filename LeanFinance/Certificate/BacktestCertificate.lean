import LeanFinance.Backtest.Certificate
import LeanFinance.Backtest.NoFutureInformation
import LeanFinance.Backtest.Reproducibility
import LeanFinance.Certificate.DataCertificate
import LeanFinance.Certificate.StrategyCertificate

namespace LeanFinance.Certificate

structure BacktestCertificate where
  claim : Backtest.BacktestClaim
  data : List DataCertificate
  strategy : StrategyCertificate
  manifest : Backtest.ExperimentManifest
  decisionMatches : strategy.decision = claim.decision
  dataCovered :
    ∀ dataset,
      dataset ∈ claim.decision.datasets →
      ∃ certificate,
        certificate ∈ data ∧
        certificate.dataset.contentHash = dataset.contentHash
  noFutureInformation : Backtest.NoFutureInformation claim.decision
  reproducible : Backtest.Reproducible manifest
  claimBound : claim.Bound

end LeanFinance.Certificate
