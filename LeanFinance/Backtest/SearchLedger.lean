structure SearchEntry where
  hypothesis : String
  parameterHash : String
  createdAt : Nat

structure SearchLedger where
  entries : List SearchEntry


def ContainsRecord (ledger : SearchLedger) (entry : SearchEntry) : Prop :=
  entry ∈ ledger.entries
