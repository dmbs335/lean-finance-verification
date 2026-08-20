import LeanFinance.Certificate.BacktestCertificate

namespace LeanFinance.Certificate

structure VerifiedResearchClaim where
  certificate : BacktestCertificate


def Sound (verified : VerifiedResearchClaim) : Prop :=
  Backtest.NoFutureInformation verified.certificate.claim.decision ∧
    Backtest.Reproducible verified.certificate.manifest ∧
    verified.certificate.claim.Bound

theorem verified_claim_is_sound
    (verified : VerifiedResearchClaim) : Sound verified := by
  exact ⟨verified.certificate.noFutureInformation,
    ⟨verified.certificate.reproducible,
      verified.certificate.claimBound⟩⟩

theorem verified_claim_uses_no_future_information
    (verified : VerifiedResearchClaim) :
    Backtest.NoFutureInformation verified.certificate.claim.decision :=
  verified.certificate.noFutureInformation

end LeanFinance.Certificate
