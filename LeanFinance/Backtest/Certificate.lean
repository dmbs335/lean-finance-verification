import LeanFinance.Core
import LeanFinance.Backtest.Decision

namespace LeanFinance.Backtest

structure BacktestClaim where
  decision : Decision
  resultHash : ContentHash
  metricName : String
  metricValue : Scalar
  deriving Repr

def BacktestClaim.Bound (claim : BacktestClaim) : Prop :=
  NonEmptyString claim.resultHash ∧ NonEmptyString claim.metricName

end LeanFinance.Backtest
