import LeanFinance.Backtest.Universe

namespace LeanFinance.Certificate

/-- Certifies that every selected security belonged to the universe at the
    snapshot time, including securities later delisted or removed. -/
structure UniverseCertificate where
  snapshot : Backtest.UniverseSnapshot
  active : snapshot.Valid

end LeanFinance.Certificate
