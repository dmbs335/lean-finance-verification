import LeanFinance.Types

namespace LeanFinance.Backtest

structure SearchEntry where
  hypothesis : String
  parameterHash : String
  createdAt : Time
  deriving DecidableEq, Repr

structure SearchLedger where
  entries : List SearchEntry
  deriving Repr

def ContainsRecord (ledger : SearchLedger) (entry : SearchEntry) : Prop :=
  entry ∈ ledger.entries

def RecordsParameterHash
    (ledger : SearchLedger)
    (parameterHash : String) : Prop :=
  ∃ entry, entry ∈ ledger.entries ∧ entry.parameterHash = parameterHash

theorem containsRecord_of_mem
    {ledger : SearchLedger}
    {entry : SearchEntry}
    (member : entry ∈ ledger.entries) :
    ContainsRecord ledger entry :=
  member

end LeanFinance.Backtest
