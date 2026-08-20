import LeanFinance.Backtest.NoFutureInformation
import LeanFinance.Certificate.BacktestCertificate

namespace LeanFinance.Certificate

def VerifiedResearchClaim (certificate : BacktestCertificate) : Prop :=
  Backtest.NoFutureInformation certificate.toDecision ∧
  Backtest.Reproducible certificate.experiment ∧
  Backtest.RecordsParameterHash
    certificate.searchLedger
    certificate.strategy.parameterHash ∧
  (∀ feature, feature ∈ certificate.features →
    feature.ValidAt certificate.data.decisionTime)

theorem BacktestCertificate.noFutureInformation
    (certificate : BacktestCertificate) :
    Backtest.NoFutureInformation certificate.toDecision := by
  intro dataset member
  exact certificate.data.available dataset member

theorem certificate_sound
    (certificate : BacktestCertificate) :
    VerifiedResearchClaim certificate := by
  exact ⟨
    certificate.noFutureInformation,
    certificate.reproducible,
    certificate.searchRecorded,
    certificate.featuresValid
  ⟩

theorem verifiedClaim_implies_noFutureInformation
    {certificate : BacktestCertificate}
    (verified : VerifiedResearchClaim certificate) :
    Backtest.NoFutureInformation certificate.toDecision :=
  verified.1

end LeanFinance.Certificate
