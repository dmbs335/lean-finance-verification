import LeanFinance.Core
import LeanFinance.Backtest.Decision

namespace LeanFinance.Backtest

structure SearchEntry where
  hypothesisId : String
  parameterHash : ContentHash
  codeHash : ContentHash
  registeredAt : Timestamp
  deriving Repr

structure SearchLedger where
  entries : List SearchEntry
  deriving Repr

def ContainsParameter
    (ledger : SearchLedger)
    (parameterHash : ContentHash) : Prop :=
  ∃ entry,
    entry ∈ ledger.entries ∧ entry.parameterHash = parameterHash

def DecisionRegistered
    (ledger : SearchLedger)
    (decision : Decision) : Prop :=
  ContainsParameter ledger decision.parameterHash

end LeanFinance.Backtest
