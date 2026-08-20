import LeanFinance.Core
import LeanFinance.Backtest.SearchLedger

namespace LeanFinance.Certificate

structure StrategyCertificate where
  decision : Backtest.Decision
  ledger : Backtest.SearchLedger
  parameterHashBound : NonEmptyString decision.parameterHash
  registered : Backtest.DecisionRegistered ledger decision

end LeanFinance.Certificate
