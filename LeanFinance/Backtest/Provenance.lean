namespace LeanFinance.Backtest

structure Provenance where
  sourceId : String
  collectedAt : Nat
  availableAt : Nat

/-- Data must exist before it can influence a decision. -/
def AvailableBefore
    (p : Provenance)
    (decisionTime : Nat) : Prop :=
  p.availableAt <= decisionTime

end LeanFinance.Backtest
