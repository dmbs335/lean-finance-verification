import LeanFinance.Core

namespace LeanFinance.Backtest

structure Provenance where
  sourceId : String
  observedAt : Timestamp
  publishedAt : Timestamp
  retrievedAt : Timestamp
  contentHash : ContentHash
  deriving Repr

def AvailableBefore
    (provenance : Provenance)
    (decisionTime : Timestamp) : Prop :=
  provenance.publishedAt ≤ decisionTime

def CausallyOrdered (provenance : Provenance) : Prop :=
  provenance.observedAt ≤ provenance.publishedAt ∧
    provenance.publishedAt ≤ provenance.retrievedAt

end LeanFinance.Backtest
