import LeanFinance.Types

namespace LeanFinance.Backtest

/-- Empirical output. Formal verification does not assert profitability; it
    certifies the process and assumptions attached to this result. -/
structure BacktestResult where
  observations : Nat
  grossReturnBps : Int
  netReturnBps : Int
  generatedAt : Time
  deriving DecidableEq, Repr

structure BacktestClaim where
  description : String
  result : BacktestResult
  deriving DecidableEq, Repr

def BacktestClaim.WellFormed (claim : BacktestClaim) : Prop :=
  claim.description ≠ "" ∧ 0 < claim.result.observations

end LeanFinance.Backtest
